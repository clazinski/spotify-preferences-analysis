import json
import boto3
from datetime import datetime
from .spotify_client import SpotifyOAuthClient
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda principal para extração de dados do Spotify com OAuth
    """
    try:
        spotify = SpotifyOAuthClient()
        s3_client = boto3.client('s3')
        
        bucket_name = 'spotify-raw-data' 
        
        execution_date = datetime.now()
        date_prefix = execution_date.strftime('%Y/%m/%d')
        timestamp = execution_date.strftime('%Y%m%d_%H%M%S')
        
        user_profile = spotify.get_user_profile()
        user_id = user_profile['id']
        
        logger.info(f"Coletando dados para usuário: {user_id}")
        
        datasets = {
            'user_profile': user_profile,
            'top_tracks_short': spotify.get_user_top_tracks(time_range='short_term'),
            'top_tracks_medium': spotify.get_user_top_tracks(time_range='medium_term'),
            'top_tracks_long': spotify.get_user_top_tracks(time_range='long_term'),
            'top_artists_short': spotify.get_user_top_artists(time_range='short_term'),
            'top_artists_medium': spotify.get_user_top_artists(time_range='medium_term'),
            'top_artists_long': spotify.get_user_top_artists(time_range='long_term'),
            'user_playlists': spotify.get_user_playlists(limit=50),
            'saved_tracks': spotify.get_saved_tracks(limit=50),
            'recently_played': spotify.get_recently_played(limit=50)
        }
        
        top_tracks = datasets['top_tracks_medium']
        if top_tracks and 'items' in top_tracks:
            track_ids = [item['id'] for item in top_tracks['items'] if item.get('id')]
            if track_ids:
                audio_features = spotify.get_audio_features(track_ids)
                datasets['audio_features'] = audio_features
        
        for dataset_name, data in datasets.items():
            if data:
                s3_key = f"raw/{user_id}/{date_prefix}/{dataset_name}_{timestamp}.json"
                
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=json.dumps(data, ensure_ascii=False, default=str),
                    ContentType='application/json'
                )
                logger.info(f"Dataset {dataset_name} salvo em s3://{bucket_name}/{s3_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Dados do usuário extraídos com sucesso',
                'user_id': user_id,
                'datasets_extraidos': list(datasets.keys()),
                'timestamp': timestamp
            })
        }
        
    except Exception as e:
        logger.error(f"Erro na execução: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Falha na extração de dados do usuário',
                'details': str(e)
            })
        }