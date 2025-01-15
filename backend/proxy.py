import time
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
from typing import Annotated

from openai import AsyncOpenAI

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

app = FastAPI()

async def get_api_key(x_bedrock_api_key: Annotated[str, Header()] = None) -> str:
    if not x_bedrock_api_key:
        raise HTTPException(
            status_code=401,
            detail="x-bedrock-api-key header is required"
        )
    return x_bedrock_api_key

# Bedrock request models
class ContentBlock(BaseModel):
    text: str

class Message(BaseModel):
    role: str
    content: List[ContentBlock]

class SystemBlock(BaseModel):
    text: str

class InferenceConfig(BaseModel):
    maxTokens: Optional[int] = None
    temperature: Optional[float] = None
    topP: Optional[float] = None
    stopSequences: Optional[List[str]] = None

class ConverseRequest(BaseModel):
    messages: List[Message]
    system: Optional[List[SystemBlock]] = None
    inferenceConfig: Optional[InferenceConfig] = None
    additionalModelRequestFields: Optional[Dict[str, Any]] = None

# Bedrock response models
class ResponseMessage(BaseModel):
    role: str
    content: List[ContentBlock]

class ConverseOutput(BaseModel):
    message: ResponseMessage

class TokenUsage(BaseModel):
    inputTokens: int
    outputTokens: int
    totalTokens: int

class Metrics(BaseModel):
    latencyMs: int

class ConverseResponse(BaseModel):
    output: ConverseOutput
    usage: TokenUsage
    metrics: Metrics
    stopReason: str = "end_turn"

# Streaming response models
class ContentBlockDeltaEvent(BaseModel):
    contentBlockIndex: int
    delta: Dict[str, Any]

class ContentBlockStartEvent(BaseModel):
    contentBlockIndex: int
    start: Dict[str, Any]

class ContentBlockStopEvent(BaseModel):
    contentBlockIndex: int

class MessageStartEvent(BaseModel):
    role: str

class MessageStopEvent(BaseModel):
    additionalModelResponseFields: Optional[Dict[str, Any]] = None
    stopReason: str = "end_turn"

class ConverseStreamMetadataEvent(BaseModel):
    metrics: Optional[Metrics] = None
    usage: Optional[TokenUsage] = None

def map_bedrock_to_openai_messages(request: ConverseRequest) -> List[Dict[str, str]]:
    messages = []

    # Add system message if present
    if request.system:
        messages.append({
            "role": "system",
            "content": request.system[0].text  # Take first system message
        })

    # Add conversation messages
    for msg in request.messages:
        messages.append({
            "role": msg.role,
            "content": msg.content[0].text  # Take first content block
        })

    return messages

def map_openai_to_bedrock_response(openai_response: Any, start_time: float) -> ConverseResponse:
    """Maps OpenAI response to Bedrock response format for non-streaming responses"""
    import time

    response_message = ResponseMessage(
        role="assistant",
        content=[ContentBlock(text=openai_response.choices[0].message.content)]
    )

    usage = TokenUsage(
        inputTokens=openai_response.usage.prompt_tokens,
        outputTokens=openai_response.usage.completion_tokens,
        totalTokens=openai_response.usage.total_tokens
    )

    metrics = Metrics(
        latencyMs=int((time.time() - start_time) * 1000)
    )

    return ConverseResponse(
        output=ConverseOutput(message=response_message),
        usage=usage,
        metrics=metrics
    )

@app.post("/model/{model_id}/converse")
async def converse(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
) -> ConverseResponse:
    import traceback
    start_time = time.time()

    logger.debug(f"Received converse request for model {model_id}")
    logger.debug(f"Request data: {request.dict()}")

    try:
        logger.debug("Mapping Bedrock request to OpenAI format")
        messages = map_bedrock_to_openai_messages(request)
        logger.debug(f"Mapped messages: {messages}")

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

        # Add any additional model fields
        if request.additionalModelRequestFields:
            kwargs.update(request.additionalModelRequestFields)

        # Configure OpenAI client with the provided API key
        aclient = AsyncOpenAI(base_url="http://127.0.0.1:4000", api_key=api_key)
        # Call OpenAI API
        logger.debug(f"Calling OpenAI API with model {model_id}")
        logger.debug(f"OpenAI request parameters: model={model_id}, messages={messages}, kwargs={kwargs}")

        response = await aclient.chat.completions.create(model=model_id,
        messages=messages,
        **kwargs)

        logger.debug(f"OpenAI API response: {response}")

        bedrock_response = map_openai_to_bedrock_response(response, start_time)
        logger.debug(f"Mapped Bedrock response: {bedrock_response}")

        return bedrock_response

    except Exception as e:
        logger.error(f"Error in converse endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/model/{model_id}/converse-stream")
async def converse_stream(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
):
    import traceback
    logger.debug(f"Received converse-stream request for model {model_id}")
    logger.debug(f"Request data: {request.dict()}")

    try:
        messages = map_bedrock_to_openai_messages(request)
        start_time = time.time()

        # Map inference config
        kwargs = {
            "stream": True  # Enable streaming
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

        # Add any additional model fields
        if request.additionalModelRequestFields:
            kwargs.update(request.additionalModelRequestFields)

        # Configure OpenAI client with the provided API key

        aclient = AsyncOpenAI(base_url="http://127.0.0.1:4000", api_key=api_key)

        async def generate():
            content_block_index = 0
            current_content = ""
            total_tokens = 0
            input_tokens = 0
            output_tokens = 0

            # Send message start event
            yield "data: " + MessageStartEvent(role="assistant").json() + "\n\n"

            # Send content block start event
            yield "data: " + ContentBlockStartEvent(
                contentBlockIndex=content_block_index,
                start={"text": ""}
            ).json() + "\n\n"

            logger.debug(f"Starting OpenAI streaming request with model {model_id}")
            logger.debug(f"OpenAI stream request parameters: model={model_id}, messages={messages}, kwargs={kwargs}")

            async for chunk in aclient.chat.completions.create(model=model_id,
            messages=messages,
            **kwargs):
                logger.debug(f"Received chunk: {chunk}")
                if chunk.choices[0].delta.content:
                    # Send content block delta event
                    yield "data: " + ContentBlockDeltaEvent(
                        contentBlockIndex=content_block_index,
                        delta={"text": chunk.choices[0].delta.content}
                    ).json() + "\n\n"
                    current_content += chunk.choices[0].delta.content

                # Update token counts if available
                if hasattr(chunk, 'usage'):
                    if hasattr(chunk.usage, 'prompt_tokens'):
                        input_tokens = chunk.usage.prompt_tokens
                    if hasattr(chunk.usage, 'completion_tokens'):
                        output_tokens = chunk.usage.completion_tokens
                    total_tokens = input_tokens + output_tokens

            # Send content block stop event
            yield "data: " + ContentBlockStopEvent(
                contentBlockIndex=content_block_index
            ).json() + "\n\n"

            # Send message stop event with usage information
            yield "data: " + MessageStopEvent(
                stopReason="end_turn"
            ).json() + "\n\n"

            # Send final metadata event
            yield "data: " + ConverseStreamMetadataEvent(
                metrics=Metrics(latencyMs=int((time.time() - start_time) * 1000)),
                usage=TokenUsage(
                    inputTokens=input_tokens,
                    outputTokens=output_tokens,
                    totalTokens=total_tokens
                )
            ).json() + "\n\n"

        return StreamingResponse(
            generate(),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error(f"Error in converse-stream endpoint: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug", log_config="log_conf.yaml")
