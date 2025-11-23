import boto3
import json
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class SecretsManager:
    def __init__(self, region_name='us-east-1'):
        self.region_name = region_name
        self.session = boto3.session.Session()
        self.client = self.session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
    
    def get_secret(self, secret_name):
        """Retrieve secret from AWS Secrets Manager"""
        try:
            get_secret_value_response = self.client.get_secret_value(
                SecretId=secret_name
            )
            
            if 'SecretString' in get_secret_value_response:
                return json.loads(get_secret_value_response['SecretString'])
            else:
                import base64
                decoded_binary_secret = base64.b64decode(
                    get_secret_value_response['SecretBinary']
                )
                return json.loads(decoded_binary_secret)
                
        except ClientError as e:
            logger.error(f"Error accessing secret {secret_name}: {e.response['Error']['Code']}")
            raise e
    
    def update_secret(self, secret_name, secret_dict):
        """Update an existing secret"""
        try:
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(secret_dict)
            )
            logger.info(f"Secret {secret_name} successfully updated")
            return True
        except ClientError as e:
            logger.error(f"Error updating secret: {str(e)}")
            return False

secrets_manager = SecretsManager()