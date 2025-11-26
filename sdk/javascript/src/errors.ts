/**
 * Base error class for all AURORA_LIFE SDK errors
 */
export class AuroraLifeError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'AuroraLifeError';
    Object.setPrototypeOf(this, AuroraLifeError.prototype);
  }
}

/**
 * Authentication error (401)
 */
export class AuthenticationError extends AuroraLifeError {
  constructor(message: string = 'Authentication failed') {
    super(message, 401);
    this.name = 'AuthenticationError';
    Object.setPrototypeOf(this, AuthenticationError.prototype);
  }
}

/**
 * Validation error (422)
 */
export class ValidationError extends AuroraLifeError {
  constructor(message: string = 'Validation error', details?: any) {
    super(message, 422, details);
    this.name = 'ValidationError';
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

/**
 * Rate limit error (429)
 */
export class RateLimitError extends AuroraLifeError {
  constructor(message: string = 'Rate limit exceeded') {
    super(message, 429);
    this.name = 'RateLimitError';
    Object.setPrototypeOf(this, RateLimitError.prototype);
  }
}

/**
 * Not found error (404)
 */
export class NotFoundError extends AuroraLifeError {
  constructor(message: string = 'Resource not found') {
    super(message, 404);
    this.name = 'NotFoundError';
    Object.setPrototypeOf(this, NotFoundError.prototype);
  }
}
