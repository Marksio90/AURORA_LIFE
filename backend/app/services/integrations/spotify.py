"""
Spotify Integration Service

Syncs music listening data for mood analysis:
- Recently played tracks
- Top tracks/artists
- Audio features (valence, energy, tempo)
- Listening patterns and preferences

Spotify Web API:
https://developer.spotify.com/documentation/web-api
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
import logging

from app.services.integrations.base_integration import BaseIntegration
from app.models.integrations import UserIntegration

logger = logging.getLogger(__name__)


class SpotifyIntegration(BaseIntegration):
    """
    Spotify music integration for mood tracking.

    Features:
    - Recently played tracks
    - Audio feature analysis (valence, energy, danceability)
    - Listening patterns
    - Genre preferences
    - Mood inference from music choices
    """

    PROVIDER_NAME = "spotify"
    OAUTH_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
    OAUTH_TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE_URL = "https://api.spotify.com/v1"
    SUPPORTS_WEBHOOKS = False  # Spotify doesn't support webhooks directly

    # OAuth scopes
    SCOPES = [
        "user-read-recently-played",
        "user-top-read",
        "user-read-playback-state",
        "user-read-currently-playing"
    ]

    def __init__(
        self,
        db,
        user_integration: UserIntegration,
        client_id: str,
        client_secret: str
    ):
        super().__init__(db, user_integration, client_id, client_secret)
        self.http_client = httpx.AsyncClient(timeout=30.0)


    def get_authorization_url(self, redirect_uri: str, state: Optional[str] = None) -> str:
        """Get Spotify OAuth authorization URL."""
        params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': ' '.join(self.SCOPES),
            'state': state or '',
            'show_dialog': 'false'
        }

        from urllib.parse import urlencode
        return f"{self.OAUTH_AUTHORIZE_URL}?{urlencode(params)}"


    async def authorize(self, auth_code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Returns token data including access_token, refresh_token, expires_in.
        """
        try:
            data = {
                'grant_type': 'authorization_code',
                'code': auth_code,
                'redirect_uri': redirect_uri,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            response = await self.http_client.post(
                self.OAUTH_TOKEN_URL,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code != 200:
                logger.error(f"Spotify OAuth error: {response.text}")
                return {
                    'success': False,
                    'error': f'OAuth failed: {response.status_code}'
                }

            token_data = response.json()

            # Store tokens
            await self._store_tokens(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                expires_in=token_data.get('expires_in', 3600)
            )

            # Get user profile for metadata
            user_profile = await self._get_user_profile()

            return {
                'success': True,
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'expires_in': token_data.get('expires_in'),
                'user_profile': user_profile
            }

        except Exception as e:
            logger.error(f"Spotify authorization error: {e}")
            return {'success': False, 'error': str(e)}


    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh expired access token using refresh token."""
        try:
            refresh_token = self.user_integration.refresh_token

            if not refresh_token:
                return {'success': False, 'error': 'No refresh token available'}

            data = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }

            response = await self.http_client.post(
                self.OAUTH_TOKEN_URL,
                data=data,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            if response.status_code != 200:
                logger.error(f"Spotify token refresh error: {response.text}")
                return {'success': False, 'error': 'Token refresh failed'}

            token_data = response.json()

            # Update tokens
            await self._store_tokens(
                access_token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token', refresh_token),
                expires_in=token_data.get('expires_in', 3600)
            )

            return {
                'success': True,
                'access_token': token_data['access_token']
            }

        except Exception as e:
            logger.error(f"Spotify token refresh error: {e}")
            return {'success': False, 'error': str(e)}


    async def sync_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Sync music listening data from Spotify.

        Args:
            start_date: Start date for sync (default: 7 days ago)
            end_date: End date for sync (default: now)

        Returns:
            Sync result with statistics
        """
        try:
            # Ensure valid access token
            if not await self._ensure_valid_token():
                return {'success': False, 'error': 'Failed to get valid access token'}

            start_date = start_date or (datetime.utcnow() - timedelta(days=7))
            end_date = end_date or datetime.utcnow()

            total_synced = 0

            # Sync recently played tracks
            recently_played = await self._sync_recently_played()
            total_synced += recently_played

            # Sync top tracks (medium term - ~6 months)
            top_tracks = await self._sync_top_tracks()
            total_synced += top_tracks

            # Sync top artists
            top_artists = await self._sync_top_artists()
            total_synced += top_artists

            # Analyze overall mood from recent listening
            mood_analysis = await self._analyze_listening_mood()

            # Store mood analysis as synced data
            if mood_analysis:
                await self._store_synced_data(
                    data_type='mood_analysis',
                    raw_data=mood_analysis,
                    external_id=f"mood_{datetime.utcnow().isoformat()}",
                    data_timestamp=datetime.utcnow()
                )
                total_synced += 1

            # Update sync metadata
            await self._update_sync_metadata(
                last_sync=datetime.utcnow(),
                next_sync=datetime.utcnow() + timedelta(hours=6),  # Sync every 6 hours
                records_synced=total_synced
            )

            logger.info(f"Spotify sync completed: {total_synced} records")

            return {
                'success': True,
                'records_synced': total_synced,
                'recently_played': recently_played,
                'top_tracks': top_tracks,
                'top_artists': top_artists,
                'mood_analysis': mood_analysis
            }

        except Exception as e:
            logger.error(f"Spotify sync error: {e}")
            return {'success': False, 'error': str(e)}


    async def _sync_recently_played(self, limit: int = 50) -> int:
        """
        Sync recently played tracks.

        Returns number of tracks synced.
        """
        try:
            response = await self._make_api_request(
                'GET',
                f"{self.API_BASE_URL}/me/player/recently-played",
                params={'limit': limit}
            )

            if not response or 'items' not in response:
                return 0

            items = response['items']
            track_ids = [item['track']['id'] for item in items if item.get('track', {}).get('id')]

            # Get audio features for tracks
            audio_features = await self._get_audio_features(track_ids)

            synced_count = 0

            for item in items:
                track = item.get('track', {})
                played_at = item.get('played_at')

                if not track or not played_at:
                    continue

                track_id = track['id']
                features = audio_features.get(track_id, {})

                # Store track with audio features
                await self._store_synced_data(
                    data_type='recently_played_track',
                    raw_data={
                        'track': {
                            'id': track_id,
                            'name': track.get('name'),
                            'artists': [a['name'] for a in track.get('artists', [])],
                            'album': track.get('album', {}).get('name'),
                            'duration_ms': track.get('duration_ms'),
                            'popularity': track.get('popularity')
                        },
                        'played_at': played_at,
                        'audio_features': features
                    },
                    external_id=f"track_{track_id}_{played_at}",
                    data_timestamp=datetime.fromisoformat(played_at.replace('Z', '+00:00'))
                )
                synced_count += 1

            logger.info(f"Synced {synced_count} recently played tracks")
            return synced_count

        except Exception as e:
            logger.error(f"Error syncing recently played: {e}")
            return 0


    async def _sync_top_tracks(self, time_range: str = 'medium_term', limit: int = 20) -> int:
        """
        Sync user's top tracks.

        time_range: short_term (4 weeks), medium_term (6 months), long_term (years)
        """
        try:
            response = await self._make_api_request(
                'GET',
                f"{self.API_BASE_URL}/me/top/tracks",
                params={'time_range': time_range, 'limit': limit}
            )

            if not response or 'items' not in response:
                return 0

            tracks = response['items']
            track_ids = [t['id'] for t in tracks if t.get('id')]

            # Get audio features
            audio_features = await self._get_audio_features(track_ids)

            # Store as single top tracks summary
            await self._store_synced_data(
                data_type='top_tracks',
                raw_data={
                    'time_range': time_range,
                    'tracks': [
                        {
                            'id': t['id'],
                            'name': t['name'],
                            'artists': [a['name'] for a in t.get('artists', [])],
                            'popularity': t.get('popularity'),
                            'audio_features': audio_features.get(t['id'], {})
                        }
                        for t in tracks
                    ]
                },
                external_id=f"top_tracks_{time_range}_{datetime.utcnow().date()}",
                data_timestamp=datetime.utcnow()
            )

            logger.info(f"Synced {len(tracks)} top tracks ({time_range})")
            return 1  # 1 record (summary)

        except Exception as e:
            logger.error(f"Error syncing top tracks: {e}")
            return 0


    async def _sync_top_artists(self, time_range: str = 'medium_term', limit: int = 20) -> int:
        """Sync user's top artists."""
        try:
            response = await self._make_api_request(
                'GET',
                f"{self.API_BASE_URL}/me/top/artists",
                params={'time_range': time_range, 'limit': limit}
            )

            if not response or 'items' not in response:
                return 0

            artists = response['items']

            # Store as single top artists summary
            await self._store_synced_data(
                data_type='top_artists',
                raw_data={
                    'time_range': time_range,
                    'artists': [
                        {
                            'id': a['id'],
                            'name': a['name'],
                            'genres': a.get('genres', []),
                            'popularity': a.get('popularity')
                        }
                        for a in artists
                    ]
                },
                external_id=f"top_artists_{time_range}_{datetime.utcnow().date()}",
                data_timestamp=datetime.utcnow()
            )

            logger.info(f"Synced {len(artists)} top artists ({time_range})")
            return 1  # 1 record (summary)

        except Exception as e:
            logger.error(f"Error syncing top artists: {e}")
            return 0


    async def _get_audio_features(self, track_ids: List[str]) -> Dict[str, Dict]:
        """
        Get audio features for tracks.

        Audio features include:
        - valence: 0.0-1.0 (musical positiveness/happiness)
        - energy: 0.0-1.0 (intensity and activity)
        - danceability: 0.0-1.0
        - acousticness: 0.0-1.0
        - tempo: BPM
        - loudness: dB
        """
        try:
            if not track_ids:
                return {}

            # Spotify allows up to 100 IDs per request
            chunk_size = 100
            all_features = {}

            for i in range(0, len(track_ids), chunk_size):
                chunk = track_ids[i:i + chunk_size]

                response = await self._make_api_request(
                    'GET',
                    f"{self.API_BASE_URL}/audio-features",
                    params={'ids': ','.join(chunk)}
                )

                if response and 'audio_features' in response:
                    for features in response['audio_features']:
                        if features:  # Can be None for unavailable tracks
                            all_features[features['id']] = {
                                'valence': features.get('valence'),
                                'energy': features.get('energy'),
                                'danceability': features.get('danceability'),
                                'acousticness': features.get('acousticness'),
                                'instrumentalness': features.get('instrumentalness'),
                                'speechiness': features.get('speechiness'),
                                'tempo': features.get('tempo'),
                                'loudness': features.get('loudness'),
                                'mode': features.get('mode'),  # 0=minor, 1=major
                                'key': features.get('key')
                            }

            return all_features

        except Exception as e:
            logger.error(f"Error getting audio features: {e}")
            return {}


    async def _analyze_listening_mood(self) -> Optional[Dict[str, Any]]:
        """
        Analyze overall mood from recent listening patterns.

        Uses audio features (especially valence and energy) to infer mood.
        """
        try:
            # Get recently played with features
            response = await self._make_api_request(
                'GET',
                f"{self.API_BASE_URL}/me/player/recently-played",
                params={'limit': 50}
            )

            if not response or 'items' not in response:
                return None

            items = response['items']
            track_ids = [item['track']['id'] for item in items if item.get('track', {}).get('id')]

            if not track_ids:
                return None

            # Get audio features
            audio_features = await self._get_audio_features(track_ids)

            if not audio_features:
                return None

            # Calculate averages
            valences = [f['valence'] for f in audio_features.values() if f.get('valence') is not None]
            energies = [f['energy'] for f in audio_features.values() if f.get('energy') is not None]
            tempos = [f['tempo'] for f in audio_features.values() if f.get('tempo') is not None]

            if not valences or not energies:
                return None

            avg_valence = sum(valences) / len(valences)
            avg_energy = sum(energies) / len(energies)
            avg_tempo = sum(tempos) / len(tempos) if tempos else 0

            # Infer mood quadrant based on valence-energy model
            mood = self._infer_mood_from_features(avg_valence, avg_energy)

            return {
                'avg_valence': round(avg_valence, 3),
                'avg_energy': round(avg_energy, 3),
                'avg_tempo': round(avg_tempo, 1),
                'inferred_mood': mood,
                'tracks_analyzed': len(valences),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing listening mood: {e}")
            return None


    def _infer_mood_from_features(self, valence: float, energy: float) -> str:
        """
        Infer mood from valence and energy using quadrant model.

        Valence-Energy Quadrant Model:
        - High valence, high energy: Happy, Excited, Energetic
        - High valence, low energy: Calm, Peaceful, Content
        - Low valence, high energy: Angry, Tense, Anxious
        - Low valence, low energy: Sad, Depressed, Tired
        """
        if valence >= 0.5 and energy >= 0.5:
            return "happy"  # High valence, high energy
        elif valence >= 0.5 and energy < 0.5:
            return "calm"  # High valence, low energy
        elif valence < 0.5 and energy >= 0.5:
            return "tense"  # Low valence, high energy
        else:
            return "sad"  # Low valence, low energy


    async def _get_user_profile(self) -> Dict[str, Any]:
        """Get Spotify user profile."""
        try:
            response = await self._make_api_request(
                'GET',
                f"{self.API_BASE_URL}/me"
            )

            if response:
                return {
                    'id': response.get('id'),
                    'display_name': response.get('display_name'),
                    'email': response.get('email'),
                    'country': response.get('country'),
                    'product': response.get('product')  # free/premium
                }

            return {}

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {}


    async def _make_api_request(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """Make authenticated API request to Spotify."""
        try:
            headers = {
                'Authorization': f'Bearer {self.user_integration.access_token}',
                'Content-Type': 'application/json'
            }

            response = await self.http_client.request(
                method,
                url,
                headers=headers,
                params=params,
                json=json_data
            )

            if response.status_code == 401:
                # Token expired, refresh and retry
                logger.info("Spotify token expired, refreshing...")
                refresh_result = await self.refresh_access_token()

                if refresh_result['success']:
                    # Retry with new token
                    headers['Authorization'] = f'Bearer {self.user_integration.access_token}'
                    response = await self.http_client.request(
                        method,
                        url,
                        headers=headers,
                        params=params,
                        json=json_data
                    )

            if response.status_code != 200:
                logger.error(f"Spotify API error {response.status_code}: {response.text}")
                return None

            return response.json()

        except Exception as e:
            logger.error(f"Spotify API request error: {e}")
            return None


    async def handle_webhook(self, event_type: str, payload: Dict) -> Dict[str, Any]:
        """
        Spotify doesn't support webhooks directly.

        For real-time updates, use polling or implement webhook via
        Spotify's partner-only notifications.
        """
        return {
            'success': False,
            'error': 'Spotify does not support webhooks'
        }


    async def disconnect(self) -> Dict[str, Any]:
        """Disconnect Spotify integration."""
        try:
            # Note: Spotify doesn't provide a revoke endpoint
            # Token will naturally expire

            result = await super().disconnect()

            logger.info(f"Spotify integration disconnected for user {self.user_integration.user_id}")

            return result

        except Exception as e:
            logger.error(f"Error disconnecting Spotify: {e}")
            return {'success': False, 'error': str(e)}
