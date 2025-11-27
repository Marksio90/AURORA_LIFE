"""
Voice Interface Service using OpenAI Whisper API

Enables:
- Voice journaling (speech to text)
- Voice commands
- Voice search
- Hands-free logging
"""
import asyncio
from typing import Dict, Any, Optional, BinaryIO
from pathlib import Path
import tempfile
import os

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from app.config import settings


class VoiceService:
    """
    Voice interface service using Whisper API.

    Features:
    - Transcribe audio to text
    - Support multiple audio formats
    - Language detection
    - Optional translation to English
    """

    SUPPORTED_FORMATS = [
        'mp3', 'mp4', 'mpeg', 'mpga',
        'm4a', 'wav', 'webm',
        'flac', 'ogg'
    ]

    MAX_FILE_SIZE_MB = 25  # Whisper API limit

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize voice service.

        Args:
            api_key: OpenAI API key (defaults to settings)
        """
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed. Install with: pip install openai")

        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def transcribe(
        self,
        audio_file: BinaryIO,
        filename: str,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text.

        Args:
            audio_file: Audio file binary stream
            filename: Original filename (for format detection)
            language: ISO-639-1 language code (e.g., 'en', 'pl')
            prompt: Optional prompt to guide transcription

        Returns:
            Transcription result with text and metadata
        """
        # Validate format
        file_ext = Path(filename).suffix.lstrip('.').lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {file_ext}")

        # Transcribe
        try:
            response = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                prompt=prompt,
                response_format="verbose_json"
            )

            return {
                'text': response.text,
                'language': response.language if hasattr(response, 'language') else language,
                'duration': response.duration if hasattr(response, 'duration') else None,
                'segments': response.segments if hasattr(response, 'segments') else None,
                'success': True
            }

        except Exception as e:
            return {
                'text': '',
                'error': str(e),
                'success': False
            }

    async def translate_to_english(
        self,
        audio_file: BinaryIO,
        filename: str,
        prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe and translate audio to English.

        Args:
            audio_file: Audio file binary stream
            filename: Original filename
            prompt: Optional prompt

        Returns:
            Translation result
        """
        try:
            response = await self.client.audio.translations.create(
                model="whisper-1",
                file=audio_file,
                prompt=prompt,
                response_format="verbose_json"
            )

            return {
                'text': response.text,
                'original_language': response.language if hasattr(response, 'language') else None,
                'duration': response.duration if hasattr(response, 'duration') else None,
                'success': True
            }

        except Exception as e:
            return {
                'text': '',
                'error': str(e),
                'success': False
            }

    async def transcribe_with_timestamps(
        self,
        audio_file: BinaryIO,
        filename: str,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe with detailed timestamps for each segment.

        Useful for:
        - Long recordings
        - Identifying specific parts
        - Time-based analysis

        Args:
            audio_file: Audio file
            filename: Filename
            language: Language code

        Returns:
            Transcription with timestamps
        """
        result = await self.transcribe(audio_file, filename, language)

        if not result['success']:
            return result

        # Format segments with timestamps
        if result.get('segments'):
            formatted_segments = []
            for segment in result['segments']:
                formatted_segments.append({
                    'start': segment.get('start', 0),
                    'end': segment.get('end', 0),
                    'text': segment.get('text', ''),
                    'confidence': segment.get('confidence', 1.0) if hasattr(segment, 'confidence') else None
                })

            result['formatted_segments'] = formatted_segments

        return result

    async def voice_command(
        self,
        audio_file: BinaryIO,
        filename: str,
        command_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process voice command.

        Transcribes audio and parses for commands.

        Args:
            audio_file: Audio file
            filename: Filename
            command_context: Context for command parsing

        Returns:
            Command and transcription
        """
        # Provide context prompt for better command recognition
        prompt = "Voice command for life tracking app. Commands include: log event, check stats, add reminder, search events."

        if command_context:
            prompt += f" Context: {command_context}"

        result = await self.transcribe(audio_file, filename, prompt=prompt)

        if not result['success']:
            return result

        # Parse command (simple keyword matching)
        text = result['text'].lower()
        command = self._parse_command(text)

        return {
            **result,
            'command': command
        }

    def _parse_command(self, text: str) -> Dict[str, Any]:
        """
        Parse text for voice commands.

        Simple keyword-based parsing.
        In production, use NLU (Natural Language Understanding).
        """
        command = {
            'type': 'unknown',
            'action': None,
            'params': {}
        }

        # Log event commands
        if any(word in text for word in ['log', 'add', 'record', 'track']):
            command['type'] = 'log_event'

            if 'sleep' in text:
                command['params']['category'] = 'sleep'
            elif 'exercise' in text or 'workout' in text:
                command['params']['category'] = 'exercise'
            elif 'meal' in text or 'food' in text or 'eat' in text:
                command['params']['category'] = 'nutrition'
            elif 'mood' in text or 'feeling' in text:
                command['params']['category'] = 'mood'

        # Query commands
        elif any(word in text for word in ['show', 'get', 'check', 'what']):
            command['type'] = 'query'

            if 'stats' in text or 'statistics' in text:
                command['action'] = 'show_stats'
            elif 'streak' in text:
                command['action'] = 'show_streaks'
            elif 'achievements' in text or 'badges' in text:
                command['action'] = 'show_achievements'
            elif 'energy' in text:
                command['action'] = 'show_energy'

        # Search commands
        elif 'search' in text or 'find' in text:
            command['type'] = 'search'
            # Extract search query (everything after search/find)
            for word in ['search', 'find']:
                if word in text:
                    query_start = text.index(word) + len(word)
                    command['params']['query'] = text[query_start:].strip()
                    break

        return command

    async def voice_journal(
        self,
        audio_file: BinaryIO,
        filename: str,
        user_id: int,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process voice journal entry.

        Transcribes and optionally analyzes sentiment/emotions.

        Args:
            audio_file: Audio file
            filename: Filename
            user_id: User ID
            language: Language code

        Returns:
            Journal entry data
        """
        # Provide context for journaling
        prompt = "Personal journal entry about daily life, mood, and activities."

        result = await self.transcribe(audio_file, filename, language, prompt)

        if not result['success']:
            return result

        # Add journaling metadata
        return {
            **result,
            'entry_type': 'voice_journal',
            'user_id': user_id,
            'word_count': len(result['text'].split()),
            'character_count': len(result['text'])
        }

    def validate_audio_file(self, file_size_bytes: int, filename: str) -> Dict[str, Any]:
        """
        Validate audio file before processing.

        Args:
            file_size_bytes: File size in bytes
            filename: Filename

        Returns:
            Validation result
        """
        errors = []

        # Check file size
        max_size_bytes = self.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            errors.append(f"File too large: {file_size_bytes / (1024 * 1024):.2f}MB (max: {self.MAX_FILE_SIZE_MB}MB)")

        # Check format
        file_ext = Path(filename).suffix.lstrip('.').lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            errors.append(f"Unsupported format: {file_ext} (supported: {', '.join(self.SUPPORTED_FORMATS)})")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }


# Example usage in API endpoint:
"""
from fastapi import UploadFile

@app.post("/api/voice/transcribe")
async def transcribe_audio(file: UploadFile):
    voice_service = VoiceService()

    # Validate
    validation = voice_service.validate_audio_file(
        file_size_bytes=file.size,
        filename=file.filename
    )

    if not validation['valid']:
        raise HTTPException(400, detail=validation['errors'])

    # Transcribe
    audio_data = await file.read()
    result = await voice_service.transcribe(
        audio_file=audio_data,
        filename=file.filename,
        language='en'  # or auto-detect
    )

    return result
"""
