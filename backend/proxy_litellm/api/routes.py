import json
import time
import traceback
import litellm
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Annotated

from ..models.request_models import ConverseRequest
from ..models.response_models import ConverseResponse
from ..utils.bedrock import get_bedrock_models, get_bedrock_client
from ..utils.message_mapper import map_to_deepseek_messages, map_deepseek_to_bedrock_response
from .auth import get_api_key

router = APIRouter()

@router.post("/model/{model_id}/converse")
async def converse(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
) -> ConverseResponse:
    start_time = time.time()

    try:
        # Check if model is available in Bedrock
        bedrock_models = get_bedrock_models()
        if model_id in bedrock_models:
            # Use Bedrock API directly
            bedrock_runtime = get_bedrock_client()

            # Forward the request directly
            response = bedrock_runtime.converse(
                modelId=model_id,
                body=json.dumps(request.dict())
            )

            return ConverseResponse(**json.loads(response['body'].read()))

        elif model_id.startswith("deepseek"):
            # Convert request format for Deepseek
            messages = map_to_deepseek_messages(request)

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

            # Call Deepseek API through litellm
            response = await litellm.acompletion(
                model=model_id,
                messages=messages,
                api_key=api_key,
                **kwargs
            )

            # Convert response back to Bedrock format
            return map_deepseek_to_bedrock_response(response, start_time)

        else:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found in either Bedrock or Deepseek"
            )

    except Exception as e:
        error_traceback = traceback.format_exc()
        error_message = str(e)

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
    try:
        # Check if model is available in Bedrock
        bedrock_models = get_bedrock_models()
        if model_id in bedrock_models:
            # Use Bedrock API directly
            bedrock_runtime = get_bedrock_client()

            async def generate():
                # Forward the request directly
                response = bedrock_runtime.converse_stream(
                    modelId=model_id,
                    body=json.dumps(request.dict())
                )

                async for event in response['body']:
                    if event.get('chunk'):
                        yield f"data: {json.dumps(event['chunk'])}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

        elif model_id.startswith("deepseek"):
            # Convert request format for Deepseek
            messages = map_to_deepseek_messages(request)

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

            async def generate():
                content_block_index = 0

                # Send message start event
                yield "data: " + json.dumps({
                    "type": "message_start",
                    "message": {"role": "assistant"}
                }) + "\n\n"

                response = await litellm.acompletion(
                    model=model_id,
                    messages=messages,
                    api_key=api_key,
                    **kwargs
                )

                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        yield "data: " + json.dumps({
                            "type": "content_block_delta",
                            "index": content_block_index,
                            "delta": {"text": chunk.choices[0].delta.content}
                        }) + "\n\n"

                # Send final events
                yield "data: " + json.dumps({
                    "type": "message_stop",
                    "message": {"role": "assistant"}
                }) + "\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )

        else:
            raise HTTPException(
                status_code=404,
                detail=f"Model {model_id} not found in either Bedrock or Deepseek"
            )

    except Exception as e:
        error_traceback = traceback.format_exc()
        error_message = str(e)

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
