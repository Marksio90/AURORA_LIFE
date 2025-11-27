"""
Integrations API Endpoints

Endpoints for:
- Connect/disconnect integrations
- Manage OAuth flow
- Sync data
- View integration status
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.api.auth import get_current_user
from app.services.voice_service import VoiceService


router = APIRouter(prefix="/api/v1/integrations", tags=["Integrations"])


# ========== Pydantic Models ==========

class IntegrationConnectRequest(BaseModel):
    provider: str
    auth_code: Optional[str] = None
    redirect_uri: Optional[str] = None


class VoiceTranscribeRequest(BaseModel):
    language: Optional[str] = None


# ========== Integration Management ==========

@router.get("/available")
async def get_available_integrations():
    """Get list of available integrations."""
    return {
        'integrations': [
            {
                'provider': 'google_calendar',
                'type': 'calendar',
                'name': 'Google Calendar',
                'description': 'Sync calendar events for context',
                'supports_oauth': True,
                'supports_webhooks': True
            },
            {
                'provider': 'fitbit',
                'type': 'health',
                'name': 'Fitbit',
                'description': 'Sync steps, sleep, heart rate',
                'supports_oauth': True,
                'supports_webhooks': True
            },
            {
                'provider': 'oura',
                'type': 'health',
                'name': 'Oura Ring',
                'description': 'Advanced sleep and readiness tracking',
                'supports_oauth': True,
                'supports_webhooks': True
            },
            {
                'provider': 'spotify',
                'type': 'music',
                'name': 'Spotify',
                'description': 'Track mood from music listening',
                'supports_oauth': True,
                'supports_webhooks': False
            }
        ]
    }


@router.get("/connected")
async def get_connected_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's connected integrations."""
    # TODO: Implement fetching
    return {
        'integrations': [],
        'total': 0
    }


@router.post("/connect")
async def connect_integration(
    request: IntegrationConnectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Connect an integration.

    For OAuth integrations, returns authorization URL.
    """
    # TODO: Implement connection
    return {
        'success': True,
        'provider': request.provider,
        'authorization_url': f'https://accounts.google.com/o/oauth2/auth?...',
        'requires_oauth': True
    }


@router.post("/disconnect/{integration_id}")
async def disconnect_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Disconnect an integration."""
    # TODO: Implement disconnection
    return {
        'success': True,
        'integration_id': integration_id
    }


@router.post("/sync/{integration_id}")
async def sync_integration(
    integration_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger sync for an integration."""
    # TODO: Implement manual sync
    return {
        'success': True,
        'integration_id': integration_id,
        'sync_started': True,
        'estimated_completion': '2-3 minutes'
    }


@router.get("/sync-history/{integration_id}")
async def get_sync_history(
    integration_id: int,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get sync history for an integration."""
    # TODO: Implement history fetching
    return {
        'integration_id': integration_id,
        'sync_logs': [],
        'last_sync': None,
        'next_sync': None
    }


# ========== Voice Interface ==========

@router.post("/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Transcribe voice recording to text.

    Supports: mp3, mp4, wav, webm, flac, ogg
    Max size: 25MB
    """
    voice_service = VoiceService()

    # Validate file
    file_size = 0
    content = await file.read()
    file_size = len(content)

    validation = voice_service.validate_audio_file(
        file_size_bytes=file_size,
        filename=file.filename
    )

    if not validation['valid']:
        raise HTTPException(400, detail=validation['errors'])

    # Transcribe
    from io import BytesIO
    audio_file = BytesIO(content)
    audio_file.name = file.filename

    result = await voice_service.transcribe(
        audio_file=audio_file,
        filename=file.filename,
        language=language
    )

    if not result['success']:
        raise HTTPException(500, detail=result.get('error', 'Transcription failed'))

    return result


@router.post("/voice/command")
async def process_voice_command(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Process voice command.

    Transcribes and parses for commands like:
    - "log exercise 30 minutes"
    - "show my stats"
    - "search sleep data"
    """
    voice_service = VoiceService()

    # Validate
    content = await file.read()
    validation = voice_service.validate_audio_file(
        file_size_bytes=len(content),
        filename=file.filename
    )

    if not validation['valid']:
        raise HTTPException(400, detail=validation['errors'])

    # Process command
    from io import BytesIO
    audio_file = BytesIO(content)
    audio_file.name = file.filename

    result = await voice_service.voice_command(
        audio_file=audio_file,
        filename=file.filename
    )

    if not result['success']:
        raise HTTPException(500, detail=result.get('error', 'Command processing failed'))

    return result


@router.post("/voice/journal")
async def voice_journal_entry(
    file: UploadFile = File(...),
    language: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """
    Create journal entry from voice recording.

    Transcribes and optionally analyzes sentiment.
    """
    voice_service = VoiceService()

    # Validate
    content = await file.read()
    validation = voice_service.validate_audio_file(
        file_size_bytes=len(content),
        filename=file.filename
    )

    if not validation['valid']:
        raise HTTPException(400, detail=validation['errors'])

    # Process journal
    from io import BytesIO
    audio_file = BytesIO(content)
    audio_file.name = file.filename

    result = await voice_service.voice_journal(
        audio_file=audio_file,
        filename=file.filename,
        user_id=current_user.id,
        language=language
    )

    if not result['success']:
        raise HTTPException(500, detail=result.get('error', 'Journaling failed'))

    # TODO: Create life event from transcription

    return {
        **result,
        'journal_entry_created': True
    }
