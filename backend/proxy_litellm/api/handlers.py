import time
import logging
from typing import Dict, Any

from .handlers.bedrock_handler import BedrockHandler
from .handlers.deepseek_handler import DeepseekHandler
from ..utils.bedrock import get_bedrock_models
from .model_utils import validate_model
from .error_handler import handle_api_error

logger = logging.getLogger(__name__)

class HandlerFactory:
    def __init__(self):
        self.bedrock_handler = BedrockHandler()
        self.deepseek_handler = DeepseekHandler()

    async def handle_converse(self, model_id: str, request: Dict[str, Any], api_key: str):
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        logger.info(f"[{request_id}] Starting converse request for model: {model_id}")

        try:
            validate_model(model_id)

            if model_id in get_bedrock_models():
                return await self.bedrock_handler.handle_converse(
                    model_id, request, request_id, start_time
                )
            elif model_id.startswith("deepseek"):
                return await self.deepseek_handler.handle_converse(
                    model_id, request, api_key, request_id, start_time
                )

        except Exception as e:
            handle_api_error(e, request_id)

    async def handle_converse_stream(self, model_id: str, request: Dict[str, Any], api_key: str):
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        logger.info(f"[{request_id}] Starting streaming request for model: {model_id}")

        try:
            validate_model(model_id)

            if model_id in get_bedrock_models():
                return await self.bedrock_handler.handle_stream(
                    model_id, request, request_id, start_time
                )
            elif model_id.startswith("deepseek"):
                return await self.deepseek_handler.handle_stream(
                    model_id, request, api_key, request_id, start_time
                )

        except Exception as e:
            handle_api_error(e, request_id)

handler_factory = HandlerFactory()

handle_converse = handler_factory.handle_converse
handle_converse_stream = handler_factory.handle_converse_stream
