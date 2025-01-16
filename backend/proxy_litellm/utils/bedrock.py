import os
import boto3
from functools import lru_cache
import logging
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)

@lru_cache()
def get_bedrock_models():
    """Get list of available Bedrock models"""
    try:
        logger.debug("Initializing Bedrock client for listing models")
        bedrock_client = boto3.client(
            'bedrock',
            region_name=os.environ.get("AWS_REGION_NAME", "us-west-2")
        )
        logger.debug(f"Using AWS region: {bedrock_client.meta.region_name}")

        response = bedrock_client.list_foundation_models()
        logger.info(f"Successfully retrieved {len(response['modelSummaries'])} Bedrock models")
        return {model['modelId']: model for model in response['modelSummaries']}
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError in get_bedrock_models: {error_code} - {error_message}")
        return {}
    except BotoCoreError as e:
        logger.error(f"AWS BotoCoreError in get_bedrock_models: {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error in get_bedrock_models: {str(e)}", exc_info=True)
        return {}

def get_bedrock_client():
    """Get Bedrock runtime client"""
    try:
        logger.debug("Initializing Bedrock runtime client")
        client = boto3.client(
            'bedrock-runtime',
            region_name=os.environ.get("AWS_REGION_NAME", "us-west-2")
        )
        logger.debug(f"Bedrock runtime client initialized with region: {client.meta.region_name}")
        return client
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS ClientError in get_bedrock_client: {error_code} - {error_message}")
        raise
    except BotoCoreError as e:
        logger.error(f"AWS BotoCoreError in get_bedrock_client: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_bedrock_client: {str(e)}", exc_info=True)
        raise
