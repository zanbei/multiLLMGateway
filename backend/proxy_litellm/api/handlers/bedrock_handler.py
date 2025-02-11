from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json
from botocore.exceptions import ClientError, BotoCoreError

from ...utils.bedrock import get_bedrock_client
from .utils import BaseHandler

class BedrockHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.bedrock_client = get_bedrock_client()

    def _handle_error(self, error: Exception, request_id: str):
        """Handle AWS-specific errors"""
        error_message = str(error)

        if isinstance(error, ClientError):
            error_code = error.response['Error']['Code']
            error_message = error.response['Error']['Message']
            self.logger.error(f"[{request_id}] AWS ClientError: {error_code} - {error_message}")
            raise ValueError(error_message)

        elif isinstance(error, BotoCoreError):
            self.logger.error(f"[{request_id}] AWS BotoCoreError: {error_message}")
            raise ValueError(error_message)

        # Call base handler for other errors
        super()._handle_error(error, request_id)

    async def handle_converse(self, model_id: str, request: Dict[str, Any], api_key: str, request_id: str, start_time: float):
        try:
            request_params = {"modelId": model_id, **request}
            self._log_request(request_id, request_params)

            response = await self._execute_with_timeout(
                self.bedrock_client.converse(**request_params),
                request_id
            )
            self._log_success(request_id, start_time)
            return response
        except Exception as e:
            self._handle_error(e, request_id)

    async def handle_stream(self, model_id: str, request: Dict[str, Any], api_key: str, request_id: str, start_time: float):
        """Handle streaming conversation requests by passing through raw Bedrock response"""
        try:
            request_params = {"modelId": model_id, **request}
            self._log_request(request_id, request_params)

            response = await self._execute_with_timeout(
                self.bedrock_client.converse_stream(**request_params),
                request_id
            )
            self._log_success(request_id, start_time)

            async def generate():
                async for event in response['body']:
                    if event.get('chunk'):
                        # Pass through the raw chunk data without any transformation
                        yield f"data: {json.dumps(event['chunk'])}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        except Exception as e:
            self._handle_error(e, request_id)
