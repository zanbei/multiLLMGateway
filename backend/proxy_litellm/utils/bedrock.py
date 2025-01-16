import os
import json
import logging
import boto3
import aiohttp
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from functools import lru_cache

logger = logging.getLogger(__name__)

BEDROCK_ENDPOINT = f"https://bedrock-runtime.{os.environ.get('AWS_REGION_NAME', 'us-west-2')}.amazonaws.com"

@lru_cache()
def get_bedrock_models():
    """Get list of available Bedrock models"""
    bedrock_client = boto3.client(
        'bedrock',
        region_name=os.environ.get("AWS_REGION_NAME", "us-west-2")
    )
    response = bedrock_client.list_foundation_models()
    return {model['modelId']: model for model in response['modelSummaries']}

class BedrockClient:
    def __init__(self):
        self.region = os.environ.get("AWS_REGION_NAME", "us-west-2")
        self.session = boto3.Session()

    def _prepare_request(self, url, data):
        """Prepare and sign request with SigV4"""
        # Create request for signing
        request = AWSRequest(
            method='POST',
            url=url,
            data=json.dumps(data)
        )

        # Add SigV4 auth
        SigV4Auth(self.session.get_credentials(), "bedrock", self.region).add_auth(request)
        return request

    async def converse(self, **kwargs):
        """Forward request to Bedrock with SigV4 auth"""
        model_id = kwargs.pop('modelId')
        url = f"{BEDROCK_ENDPOINT}/model/{model_id}/converse"

        prepped_request = self._prepare_request(url, kwargs)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                prepped_request.url,
                headers=prepped_request.headers,
                data=prepped_request.body
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def converse_stream(self, **kwargs):
        """Forward streaming request to Bedrock with SigV4 auth"""
        model_id = kwargs.pop('modelId')
        url = f"{BEDROCK_ENDPOINT}/model/{model_id}/converse-stream"

        prepped_request = self._prepare_request(url, kwargs)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                prepped_request.url,
                headers=prepped_request.headers,
                data=prepped_request.body
            ) as response:
                response.raise_for_status()
                return {
                    'body': self._stream_response(response)
                }

    async def _stream_response(self, response):
        """Process streaming response from Bedrock"""
        async for line in response.content.iter_chunks():
            if line:
                try:
                    yield {'chunk': json.loads(line[0].decode())}
                except json.JSONDecodeError:
                    continue

@lru_cache()
def get_bedrock_client():
    """Get Bedrock client instance"""
    return BedrockClient()
