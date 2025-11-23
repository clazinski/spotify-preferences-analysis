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
        """Load client_id and client_secret from Secrets Manager"""
        try:
            self.secrets = self.secrets_manager.get_secret("spotify/api-credentials")
            print("Client credentials loaded")
        except Exception as e:
            print(f"Error loading credentials: {e}")
            raise
    
    def get_authorization_url(self):
        """Generate authorization URL for user"""
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
        """Exchange authorization code for access and refresh tokens"""
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
            print(f"Error exchanging code for token: {e}")
            raise
    
    def setup_initial_tokens(self):
        """Complete initial setup flow"""
        print("=== Spotify OAuth Setup ===")
        
        auth_url = self.get_authorization_url()
        print(f"\n1. Open this URL in your browser:\n{auth_url}")
        
        webbrowser.open(auth_url)
        
        print("\n2. After authorizing, you will be redirected.")
        print("   Copy the 'code' parameter from the redirect URL.")
        authorization_code = input("\n3. Paste the authorization code here: ").strip()
        
        print("\n4. Retrieving tokens...")
        token_data = self.exchange_code_for_token(authorization_code)
        
        self.secrets.update({
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_expires_in': token_data['expires_in']
        })
        
        success = self.secrets_manager.update_secret("spotify/api-credentials", self.secrets)
        
        if success:
            print("Tokens successfully saved to Secrets Manager")
            print(f"   - Access Token: {token_data['access_token'][:20]}...")
            print(f"   - Refresh Token: {token_data['refresh_token'][:20]}...")
            print(f"   - Expires in: {token_data['expires_in']} seconds")
        else:
            print("Error saving tokens to Secrets Manager")

def main():
    try:
        setup = SpotifyAuthSetup()
        setup.setup_initial_tokens()
    except Exception as e:
        print(f"Setup failed: {e}")

if __name__ == "__main__":
    main()