import requests
import base64
from datetime import datetime, timedelta
from .secrets_manager import secrets_manager
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class SpotifyOAuthClient:
    def __init__(self):
        self.secrets = None
        self.access_token = None
        self.refresh_token = None
        self.token_expires = None
        self.base_url = "https://api.spotify.com/v1"
        self._load_credentials()
    
    def _load_credentials(self):
        """Carrega credenciais do Secrets Manager"""
        try:
            self.secrets = secrets_manager.get_secret("spotify/api-credentials")
            self.refresh_token = self.secrets.get('refresh_token')
            logger.info("Credenciais carregadas com sucesso")
        except Exception as e:
            logger.error(f"Erro ao carregar credenciais: {str(e)}")
            raise
    
    def _get_auth_header(self):
        """Gera header de autorização básica"""
        client_creds = f"{self.secrets['client_id']}:{self.secrets['client_secret']}"
        client_creds_b64 = base64.b64encode(client_creds.encode()).decode()
        return {'Authorization': f'Basic {client_creds_b64}'}
    
    def refresh_access_token(self):
        """Refresh token usando o refresh_token"""
        if not self.refresh_token:
            raise Exception("Refresh token não disponível")
        
        auth_url = 'https://accounts.spotify.com/api/token'
        headers = self._get_auth_header()
        
        try:
            response = requests.post(auth_url, {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }, headers=headers, timeout=10)
            
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            self.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'])
            
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
                self.secrets['refresh_token'] = self.refresh_token
                secrets_manager.update_secret("spotify/api-credentials", self.secrets)
            
            logger.info("Access token renovado com sucesso")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao renovar token: {str(e)}")
            raise
    
    def _ensure_token_valid(self):
        """Verifica se o token é válido e renova se necessário"""
        if not self.access_token or not self.token_expires or datetime.now() >= self.token_expires:
            logger.info("Token expirado ou inválido, renovando...")
            self.refresh_access_token()
    
    def _make_authenticated_request(self, endpoint, params=None):
        """Faz requisição para a API com token válido"""
        self._ensure_token_valid()
        
        url = f"{self.base_url}/{endpoint}"
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401: 
                logger.warning("Token expirado, tentando renovar...")
                self.refresh_access_token()
                return self._make_authenticated_request(endpoint, params) 
            else:
                logger.error(f"HTTP Error {response.status_code}: {response.text}")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {str(e)}")
            raise
    
    def get_user_profile(self):
        """Busca perfil do usuário"""
        return self._make_authenticated_request('me')
    
    def get_user_top_tracks(self, limit=20, time_range='medium_term'):
        """Busca top tracks do usuário"""
        return self._make_authenticated_request('me/top/tracks', {
            'limit': limit,
            'time_range': time_range
        })
    
    def get_user_top_artists(self, limit=20, time_range='medium_term'):
        """Busca top artists do usuário"""
        return self._make_authenticated_request('me/top/artists', {
            'limit': limit,
            'time_range': time_range
        })
    
    def get_user_playlists(self, limit=50):
        """Busca playlists do usuário"""
        return self._make_authenticated_request('me/playlists', {'limit': limit})
    
    def get_saved_tracks(self, limit=50):
        """Busca músicas salvas (liked songs)"""
        return self._make_authenticated_request('me/tracks', {'limit': limit})
    
    def get_recently_played(self, limit=50):
        """Busca músicas tocadas recentemente"""
        return self._make_authenticated_request('me/player/recently-played', {'limit': limit})
    
    def get_audio_features(self, track_ids):
        """Busca features de áudio para tracks"""
        if isinstance(track_ids, list):
            track_ids = ','.join(track_ids)
        return self._make_authenticated_request(f'audio-features', {'ids': track_ids})
    
    def get_audio_analysis(self, track_id):
        """Busca análise de áudio detalhada"""
        return self._make_authenticated_request(f'audio-analysis/{track_id}')