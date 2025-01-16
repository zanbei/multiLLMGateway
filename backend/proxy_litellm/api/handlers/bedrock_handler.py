import time
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import requests

from ...utils.bedrock import get_bedrock_client
from .. import handle_api_error
from .utils import prepare_bedrock_request, log_successful_request, generate_streaming_response

class BedrockHandler:
    def __init__(self):
        self.bedrock_client = get_bedrock_client()

    async def handle_converse(self, model_id: str, request: Dict[str, Any], request_id: str, start_time: float):
        try:
            request_params = prepare_bedrock_request(model_id, request, request_id)
            response = self.bedrock_client.converse(**request_params)
            log_successful_request(request_id, start_time)
            return response
        except requests.exceptions.RequestException as e:
            handle_api_error(e, request_id)
        except Exception as e:
            handle_api_error(e, request_id)

    async def handle_stream(self, model_id: str, request: Dict[str, Any], request_id: str, start_time: float):
        try:
            request_params = prepare_bedrock_request(model_id, request, request_id)
            response = self.bedrock_client.converse_stream(**request_params)
            log_successful_request(request_id, start_time)
            return StreamingResponse(
                generate_streaming_response(response, request_id),
                media_type="text/event-stream"
            )
        except requests.exceptions.RequestException as e:
            handle_api_error(e, request_id)
        except Exception as e:
            handle_api_error(e, request_id)
