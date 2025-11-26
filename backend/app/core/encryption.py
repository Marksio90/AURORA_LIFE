"""
Field-level encryption for sensitive data.

Uses Fernet symmetric encryption (AES 128 in CBC mode).
Encryption keys should be stored in environment variables or secrets management.

Usage:
    from app.core.encryption import encrypt_field, decrypt_field

    # Encrypt
    encrypted = encrypt_field("sensitive data")

    # Decrypt
    decrypted = decrypt_field(encrypted)
"""

from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
import base64
import logging

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data fields."""

    def __init__(self, encryption_key: str):
        """
        Initialize encryption service.

        Args:
            encryption_key: Base64-encoded Fernet key (32 bytes)
        """
        try:
            self.fernet = Fernet(encryption_key.encode())
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise ValueError("Invalid encryption key")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string value.

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return plaintext

        try:
            encrypted_bytes = self.fernet.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Encrypted string (base64-encoded)

        Returns:
            Decrypted plaintext string

        Raises:
            InvalidToken: If decryption fails (wrong key or corrupted data)
        """
        if not ciphertext:
            return ciphertext

        try:
            decrypted_bytes = self.fernet.decrypt(ciphertext.encode())
            return decrypted_bytes.decode()
        except InvalidToken:
            logger.error("Decryption failed: Invalid token")
            raise
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def rotate_key(self, old_key: str, new_key: str, ciphertext: str) -> str:
        """
        Re-encrypt data with a new key.

        Args:
            old_key: Previous encryption key
            new_key: New encryption key
            ciphertext: Data encrypted with old key

        Returns:
            Data re-encrypted with new key
        """
        old_fernet = Fernet(old_key.encode())
        new_fernet = Fernet(new_key.encode())

        # Decrypt with old key
        plaintext = old_fernet.decrypt(ciphertext.encode()).decode()

        # Encrypt with new key
        new_ciphertext = new_fernet.encrypt(plaintext.encode())

        return new_ciphertext.decode()


# Global encryption service instance
_encryption_service = None


def get_encryption_service() -> EncryptionService:
    """Get or create encryption service singleton."""
    global _encryption_service

    if _encryption_service is None:
        if not settings.ENCRYPTION_KEY:
            logger.warning("ENCRYPTION_KEY not set, using default (INSECURE for production!)")
            # Generate a key for development (DO NOT use in production)
            key = Fernet.generate_key().decode()
        else:
            key = settings.ENCRYPTION_KEY

        _encryption_service = EncryptionService(key)

    return _encryption_service


# Convenience functions
def encrypt_field(value: str) -> str:
    """Encrypt a field value."""
    service = get_encryption_service()
    return service.encrypt(value)


def decrypt_field(value: str) -> str:
    """Decrypt a field value."""
    service = get_encryption_service()
    return service.decrypt(value)


# Generate a new encryption key (for initial setup)
def generate_encryption_key() -> str:
    """
    Generate a new Fernet encryption key.

    Returns:
        Base64-encoded key string

    Usage:
        >>> key = generate_encryption_key()
        >>> print(key)
        'gAAAAABc8W...'
    """
    return Fernet.generate_key().decode()


# SQLAlchemy custom type for encrypted fields
from sqlalchemy.types import TypeDecorator, String


class EncryptedString(TypeDecorator):
    """
    SQLAlchemy type for automatically encrypted string columns.

    Usage:
        class User(Base):
            ssn = Column(EncryptedString(255))
            credit_card = Column(EncryptedString(255))
    """

    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database."""
        if value is not None:
            return encrypt_field(value)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt value when reading from database."""
        if value is not None:
            return decrypt_field(value)
        return value


# Example usage for specific sensitive fields
def encrypt_ssn(ssn: str) -> str:
    """Encrypt Social Security Number."""
    return encrypt_field(ssn)


def decrypt_ssn(encrypted_ssn: str) -> str:
    """Decrypt Social Security Number."""
    return decrypt_field(encrypted_ssn)


def encrypt_credit_card(cc_number: str) -> str:
    """Encrypt credit card number."""
    return encrypt_field(cc_number)


def decrypt_credit_card(encrypted_cc: str) -> str:
    """Decrypt credit card number."""
    return decrypt_field(encrypted_cc)


# Key rotation script
async def rotate_encryption_keys(old_key: str, new_key: str, db_session):
    """
    Rotate encryption keys for all encrypted fields.

    This should be run as a maintenance script when rotating keys.

    Args:
        old_key: Current encryption key
        new_key: New encryption key to use
        db_session: Database session

    Example:
        >>> await rotate_encryption_keys(old_key, new_key, db)
    """
    from app.models.user import User  # Import models with encrypted fields

    service = EncryptionService(old_key)
    new_service = EncryptionService(new_key)

    # Rotate user sensitive fields
    users = await db_session.execute("SELECT id, encrypted_field FROM users WHERE encrypted_field IS NOT NULL")

    for user_id, encrypted_value in users:
        try:
            # Decrypt with old key
            plaintext = service.decrypt(encrypted_value)

            # Encrypt with new key
            new_encrypted = new_service.encrypt(plaintext)

            # Update database
            await db_session.execute(
                "UPDATE users SET encrypted_field = :new_value WHERE id = :id",
                {"new_value": new_encrypted, "id": user_id}
            )

        except Exception as e:
            logger.error(f"Failed to rotate key for user {user_id}: {e}")
            raise

    await db_session.commit()
    logger.info("Encryption keys rotated successfully")
