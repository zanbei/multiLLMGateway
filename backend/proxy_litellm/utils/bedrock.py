import os
import json
import logging
import boto3
import requests
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
import botocore.session
from functools import lru_cache
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)

BEDROCK_ENDPOINT = f"https://bedrock-runtime.{os.environ.get('AWS_REGION_NAME', 'us-west-2')}.amazonaws.com"

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

class BedrockClient:
    def __init__(self):
        self.region = os.environ.get("AWS_REGION_NAME", "us-west-2")
        logger.debug(f"Initializing BedrockClient with region: {self.region}")

        self.session = boto3.Session()

        logger.debug("SigV4 auth signer initialized")

    def _prepare_request(self, url, data, headers=None):
        """Prepare and sign request with SigV4"""
        if headers is None:
            headers = {}

        logger.debug(f"Preparing request for URL: {url}")
        logger.debug(f"Request payload: {json.dumps(data, indent=2)}")

        # Create request without headers for signing
        request_for_signing = AWSRequest(
            method='POST',
            url=url,
            data=json.dumps(data),
            headers={}  # Empty headers for signing
        )

        logger.debug("Adding SigV4 authentication")
        SigV4Auth(self.session.get_credentials(), "bedrock", self.region).add_auth(request_for_signing)

        # Create final request with original headers plus auth headers
        final_headers = headers.copy()
        # Copy over the authorization-related headers from the signed request
        auth_headers = ['Authorization', 'X-Amz-Date', 'X-Amz-Security-Token']
        for header in auth_headers:
            if header in request_for_signing.headers:
                final_headers[header] = request_for_signing.headers[header]

        request = AWSRequest(
            method='POST',
            url=url,
            data=json.dumps(data),
            headers=final_headers
        )

        logger.debug(f"Request headers after signing: {json.dumps(dict(request.headers), indent=2)}")
        return request

    def converse(self, **kwargs):
        """Forward request to Bedrock with SigV4 auth"""
        model_id = kwargs.pop('modelId')
        url = f"{BEDROCK_ENDPOINT}/model/{model_id}/converse"

        logger.debug(f"Making Bedrock request for model: {model_id}")
        logger.debug(f"Full request URL: {url}")

        try:
            prepped_request = self._prepare_request(url, kwargs)

            logger.debug("Sending request to Bedrock API")
            response = requests.post(
                prepped_request.url,
                headers=prepped_request.headers,
                data=prepped_request.body
            )

            if response.status_code != 200:
                logger.error(f"Bedrock API error - Status: {response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")
                logger.error(f"Response body: {response.text}")

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in Bedrock request: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                logger.error(f"Response body: {e.response.text}")
            raise

    def converse_stream(self, **kwargs):
        """Forward streaming request to Bedrock with SigV4 auth"""
        model_id = kwargs.pop('modelId')
        url = f"{BEDROCK_ENDPOINT}/model/{model_id}/converse-stream"

        logger.debug(f"Making Bedrock streaming request for model: {model_id}")
        logger.debug(f"Full request URL: {url}")

        try:
            prepped_request = self._prepare_request(url, kwargs)

            logger.debug("Sending streaming request to Bedrock API")
            response = requests.post(
                prepped_request.url,
                headers=prepped_request.headers,
                data=prepped_request.body,
                stream=True
            )

            if response.status_code != 200:
                logger.error(f"Bedrock streaming API error - Status: {response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")

            response.raise_for_status()

            return {
                'body': self._stream_response(response)
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error in Bedrock streaming request: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response headers: {json.dumps(dict(e.response.headers), indent=2)}")
                logger.error(f"Response body: {e.response.text}")
            raise

    async def _stream_response(self, response):
        """Process streaming response from Bedrock"""
        for line in response.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                    yield {'chunk': chunk}
                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding response chunk: {str(e)}")
                    logger.error(f"Raw chunk content: {line}")
                    continue

@lru_cache()
def get_bedrock_client():
    """Get Bedrock client instance"""
    try:
        logger.debug("Initializing Bedrock client")
        client = BedrockClient()
        logger.debug(f"Bedrock client initialized with region: {client.region}")
        return client
    except Exception as e:
        logger.error(f"Error initializing Bedrock client: {str(e)}", exc_info=True)
        raise
