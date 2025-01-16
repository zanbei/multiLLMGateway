import os
import boto3
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

@lru_cache()
def get_bedrock_models():
    """Get list of available Bedrock models"""
    try:
        bedrock_client = boto3.client(
            'bedrock'
            #aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
            #aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            #region_name=os.environ.get("AWS_REGION_NAME", "us-east-1")
        )
        response = bedrock_client.list_foundation_models()
        return {model['modelId']: model for model in response['modelSummaries']}
    except Exception as e:
        logger.error(f"Error getting Bedrock models: {str(e)}")
        return {}

def get_bedrock_client():
    """Get Bedrock runtime client"""
    return boto3.client(
        'bedrock-runtime'
        #aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        #aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        #region_name=os.environ.get("AWS_REGION_NAME", "us-east-1")
    )
