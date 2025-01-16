import json
import time
import logging
import litellm
from fastapi.responses import StreamingResponse
from typing import Dict, Any

from ...utils import map_to_deepseek_messages, map_deepseek_to_bedrock_response
from .. import handle_api_error, prepare_inference_config

logger = logging.getLogger(__name__)

class DeepseekHandler:
    async def handle_converse(self, model_id: str, request: Dict[str, Any], api_key: str, request_id: str, start_time: float):
        try:
            messages = map_to_deepseek_messages(request)
            logger.debug(f"[{request_id}] Mapped messages for Deepseek: {messages}")

            kwargs = prepare_inference_config(request)
            logger.debug(f"[{request_id}] Deepseek inference config: {kwargs}")

            response = await litellm.acompletion(
                model=model_id,
                messages=messages,
                api_key=api_key,
                **kwargs
            )
            logger.debug(f"[{request_id}] Deepseek response: {response}")

            bedrock_response = map_deepseek_to_bedrock_response(response, start_time)
            logger.info(f"[{request_id}] Successfully completed Deepseek request in {time.time() - start_time:.2f}s")
            return bedrock_response

        except Exception as e:
            handle_api_error(e, request_id)

    async def handle_stream(self, model_id: str, request: Dict[str, Any], api_key: str, request_id: str, start_time: float):
        async def generate():
            try:
                content_block_index = 0

                start_event = {
                    "type": "message_start",
                    "message": {"role": "assistant"}
                }
                logger.debug(f"[{request_id}] Sending start event: {json.dumps(start_event)}")
                yield "data: " + json.dumps(start_event) + "\n\n"

                messages = map_to_deepseek_messages(request)
                kwargs = prepare_inference_config(request)
                kwargs["stream"] = True
                logger.debug(f"[{request_id}] Deepseek streaming inference config: {kwargs}")

                response = await litellm.acompletion(
                    model=model_id,
                    messages=messages,
                    api_key=api_key,
                    **kwargs
                )

                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        chunk_event = {
                            "type": "content_block_delta",
                            "index": content_block_index,
                            "delta": {"text": chunk.choices[0].delta.content}
                        }
                        logger.debug(f"[{request_id}] Sending chunk: {json.dumps(chunk_event)}")
                        yield "data: " + json.dumps(chunk_event) + "\n\n"

                stop_event = {
                    "type": "message_stop",
                    "message": {"role": "assistant"}
                }
                logger.debug(f"[{request_id}] Sending stop event: {json.dumps(stop_event)}")
                yield "data: " + json.dumps(stop_event) + "\n\n"

                logger.info(f"[{request_id}] Successfully completed Deepseek streaming request in {time.time() - start_time:.2f}s")

            except Exception as e:
                logger.error(f"[{request_id}] Error in Deepseek stream: {str(e)}", exc_info=True)
                raise

        return StreamingResponse(generate(), media_type="text/event-stream")
