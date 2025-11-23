import requests
import webbrowser
import json
from urllib.parse import urlencode
import boto3
from secrets_manager import SecretsManager

class SpotifyAuthSetup:
    def __init__(self):
        self.secrets_manager = SecretsManager()
        self.secrets = None
        self._load_client_credentials()
    
    def _load_client_credentials(self):
        """Carrega client_id e client_secret do Secrets Manager"""
        try:
            self.secrets = self.secrets_manager.get_secret("spotify/api-credentials")
            print("Credenciais do cliente carregadas")
        except Exception as e:
            print(f"Erro ao carregar credenciais: {e}")
            raise
    
    def get_authorization_url(self):
        """Gera URL de autorização para usuário"""
        auth_url = "https://accounts.spotify.com/authorize"
        
        params = {
            'client_id': self.secrets['client_id'],
            'response_type': 'code',
            'redirect_uri': self.secrets['redirect_uri'],
            'scope': ' '.join([
                'user-read-private',
                'user-read-email',
                'user-top-read',
                'user-library-read',
                'user-read-recently-played',
                'playlist-read-private'
            ]),
            'show_dialog': 'true'
        }
        
        return f"{auth_url}?{urlencode(params)}"
    
    def exchange_code_for_token(self, authorization_code):
        """Troca authorization code por access e refresh tokens"""
        token_url = "https://accounts.spotify.com/api/token"
        
        data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.secrets['redirect_uri'],
            'client_id': self.secrets['client_id'],
            'client_secret': self.secrets['client_secret']
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao trocar code por token: {e}")
            raise
    
    def setup_initial_tokens(self):
        """Fluxo completo de setup inicial"""
        print("=== Spotify OAuth Setup ===")
        
        auth_url = self.get_authorization_url()
        print(f"\n1. Abra esta URL no seu navegador:\n{auth_url}")
        
        webbrowser.open(auth_url)
        
        print("\n2. Após autorizar, você será redirecionado.")
        print("   Copie o parâmetro 'code' da URL de redirecionamento.")
        authorization_code = input("\n3. Cole o authorization code aqui: ").strip()
        
        print("\n4. Obtendo tokens...")
        token_data = self.exchange_code_for_token(authorization_code)
        
        self.secrets.update({
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_expires_in': token_data['expires_in']
        })
        
        success = self.secrets_manager.update_secret("spotify/api-credentials", self.secrets)
        
        if success:
            print("Tokens salvos com sucesso no Secrets Manager")
            print(f"   - Access Token: {token_data['access_token'][:20]}...")
            print(f"   - Refresh Token: {token_data['refresh_token'][:20]}...")
            print(f"   - Expira em: {token_data['expires_in']} segundos")
        else:
            print("Erro ao salvar tokens no Secrets Manager")

def main():
    try:
        setup = SpotifyAuthSetup()
        setup.setup_initial_tokens()
    except Exception as e:
        print(f"Setup falhou: {e}")

if __name__ == "__main__":
    main()