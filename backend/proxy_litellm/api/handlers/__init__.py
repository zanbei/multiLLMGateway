import time
import logging
from typing import Dict, Any

from .bedrock_handler import BedrockHandler
from .deepseek_handler import DeepseekHandler
from ...models import ConverseRequest

logger = logging.getLogger(__name__)

bedrock_handler = BedrockHandler()
deepseek_handler = DeepseekHandler()

async def handle_converse(model_id: str, request: ConverseRequest, api_key: str):
    request_id = str(int(time.time() * 1000))  # Generate request_id using timestamp
    start_time = time.time()

    if model_id.startswith("anthropic.claude"):
        return await bedrock_handler.handle_converse(model_id, request.dict(), request_id, start_time)
    else:
        return await deepseek_handler.handle_converse(model_id, request.dict(), api_key, request_id, start_time)

async def handle_converse_stream(model_id: str, request: ConverseRequest, api_key: str):
    request_id = str(int(time.time() * 1000))  # Generate request_id using timestamp
    start_time = time.time()

    if model_id.startswith("anthropic.claude"):
        return await bedrock_handler.handle_stream(model_id, request.dict(), request_id, start_time)
    else:
        return await deepseek_handler.handle_stream(model_id, request.dict(), api_key, request_id, start_time)
