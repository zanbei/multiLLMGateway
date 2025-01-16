import json
import time
import traceback
import litellm
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated
from botocore.exceptions import ClientError, BotoCoreError

from ..models.request_models import ConverseRequest
from ..models.response_models import ConverseResponse
from ..utils.bedrock import get_bedrock_models, get_bedrock_client
from ..utils.message_mapper import map_to_deepseek_messages, map_deepseek_to_bedrock_response
from ..utils.bedrock_mapper import map_request_to_bedrock_params
from .auth import get_api_key

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/model/{model_id}/converse")
async def converse(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
) -> ConverseResponse:
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    logger.info(f"[{request_id}] Starting converse request for model: {model_id}")

    try:
        # Check if model is available in Bedrock
        bedrock_models = get_bedrock_models()
        if model_id in bedrock_models:
            logger.debug(f"[{request_id}] Using Bedrock API for model: {model_id}")
            bedrock_runtime = get_bedrock_client()

            try:
                # Map request to Bedrock parameters
                request_params = map_request_to_bedrock_params(model_id, request)
                logger.debug(f"[{request_id}] Bedrock request params: {json.dumps(request_params)}")

                # Forward the request with proper parameters
                response = bedrock_runtime.converse(**request_params)

                # Log response details
                response_body = json.loads(response['body'].read())
                logger.debug(f"[{request_id}] Bedrock response: {json.dumps(response_body)}")
                logger.info(f"[{request_id}] Successfully completed Bedrock request in {time.time() - start_time:.2f}s")

                return ConverseResponse(**response_body)

            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                logger.error(f"[{request_id}] AWS ClientError: {error_code} - {error_message}")
                raise
            except BotoCoreError as e:
                logger.error(f"[{request_id}] AWS BotoCoreError: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"[{request_id}] Unexpected Bedrock error: {str(e)}", exc_info=True)
                raise

        elif model_id.startswith("deepseek"):
            logger.debug(f"[{request_id}] Using Deepseek API for model: {model_id}")
            # Convert request format for Deepseek
            messages = map_to_deepseek_messages(request)
            logger.debug(f"[{request_id}] Mapped messages for Deepseek: {messages}")

            # Map inference config
            kwargs = {}
            if request.inferenceConfig:
                if request.inferenceConfig.maxTokens:
                    kwargs["max_tokens"] = request.inferenceConfig.maxTokens
                if request.inferenceConfig.temperature:
                    kwargs["temperature"] = request.inferenceConfig.temperature
                if request.inferenceConfig.topP:
                    kwargs["top_p"] = request.inferenceConfig.topP
                if request.inferenceConfig.stopSequences:
                    kwargs["stop"] = request.inferenceConfig.stopSequences
                logger.debug(f"[{request_id}] Deepseek inference config: {kwargs}")

            # Call Deepseek API through litellm
            response = await litellm.acompletion(
                model=model_id,
                messages=messages,
                api_key=api_key,
                **kwargs
            )
            logger.debug(f"[{request_id}] Deepseek response: {response}")

            # Convert response back to Bedrock format
            bedrock_response = map_deepseek_to_bedrock_response(response, start_time)
            logger.info(f"[{request_id}] Successfully completed Deepseek request in {time.time() - start_time:.2f}s")
            return bedrock_response

        else:
            logger.error(f"[{request_id}] Model not found: {model_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found in either Bedrock or Deepseek"
            )

    except Exception as e:
        error_traceback = traceback.format_exc()
        error_message = str(e)
        logger.error(f"[{request_id}] Error processing request: {error_message}\n{error_traceback}")

        if "ResourceNotFoundException" in error_message:
            raise HTTPException(status_code=404, detail=error_message)
        elif "ValidationException" in error_message:
            raise HTTPException(status_code=400, detail=error_message)
        elif "ModelTimeoutException" in error_message:
            raise HTTPException(status_code=408, detail=error_message)
        elif "ThrottlingException" in error_message:
            raise HTTPException(status_code=429, detail=error_message)
        elif "ServiceUnavailableException" in error_message:
            raise HTTPException(status_code=503, detail=error_message)
        else:
            raise HTTPException(status_code=500, detail=error_message)

@router.post("/model/{model_id}/converse-stream")
async def converse_stream(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
):
    start_time = time.time()
    request_id = f"req_{int(start_time * 1000)}"
    logger.info(f"[{request_id}] Starting streaming request for model: {model_id}")

    try:
        # Check if model is available in Bedrock
        bedrock_models = get_bedrock_models()
        if model_id in bedrock_models:
            logger.debug(f"[{request_id}] Using Bedrock streaming API for model: {model_id}")
            bedrock_runtime = get_bedrock_client()

            async def generate():
                try:
                    # Map request to Bedrock parameters
                    request_params = map_request_to_bedrock_params(model_id, request)
                    logger.debug(f"[{request_id}] Bedrock streaming request params: {json.dumps(request_params)}")

                    # Forward the request with proper parameters
                    response = bedrock_runtime.converse_stream(**request_params)

                    async for event in response['body']:
                        if event.get('chunk'):
                            chunk_data = event['chunk']
                            logger.debug(f"[{request_id}] Received Bedrock chunk: {json.dumps(chunk_data)}")
                            yield f"data: {json.dumps(chunk_data)}\n\n"

                    logger.info(f"[{request_id}] Successfully completed Bedrock streaming request in {time.time() - start_time:.2f}s")

                except Exception as e:
                    logger.error(f"[{request_id}] Error in Bedrock stream: {str(e)}", exc_info=True)
                    raise

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

        elif model_id.startswith("deepseek"):
            logger.debug(f"[{request_id}] Using Deepseek streaming API for model: {model_id}")
            # Convert request format for Deepseek
            messages = map_to_deepseek_messages(request)
            logger.debug(f"[{request_id}] Mapped messages for Deepseek streaming: {messages}")

            # Map inference config
            kwargs = {
                "stream": True
            }
            if request.inferenceConfig:
                if request.inferenceConfig.maxTokens:
                    kwargs["max_tokens"] = request.inferenceConfig.maxTokens
                if request.inferenceConfig.temperature:
                    kwargs["temperature"] = request.inferenceConfig.temperature
                if request.inferenceConfig.topP:
                    kwargs["top_p"] = request.inferenceConfig.topP
                if request.inferenceConfig.stopSequences:
                    kwargs["stop"] = request.inferenceConfig.stopSequences
                logger.debug(f"[{request_id}] Deepseek streaming inference config: {kwargs}")

            async def generate():
                try:
                    content_block_index = 0

                    # Send message start event
                    start_event = {
                        "type": "message_start",
                        "message": {"role": "assistant"}
                    }
                    logger.debug(f"[{request_id}] Sending start event: {json.dumps(start_event)}")
                    yield "data: " + json.dumps(start_event) + "\n\n"

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

                    # Send final events
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

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

        else:
            logger.error(f"[{request_id}] Model not found: {model_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found in either Bedrock or Deepseek"
            )

    except Exception as e:
        error_traceback = traceback.format_exc()
        error_message = str(e)
        logger.error(f"[{request_id}] Error processing streaming request: {error_message}\n{error_traceback}")

        if "ResourceNotFoundException" in error_message:
            raise HTTPException(status_code=404, detail=error_message)
        elif "ValidationException" in error_message:
            raise HTTPException(status_code=400, detail=error_message)
        elif "ModelTimeoutException" in error_message:
            raise HTTPException(status_code=408, detail=error_message)
        elif "ThrottlingException" in error_message:
            raise HTTPException(status_code=429, detail=error_message)
        elif "ServiceUnavailableException" in error_message:
            raise HTTPException(status_code=503, detail=error_message)
        else:
            raise HTTPException(status_code=500, detail=error_message)
