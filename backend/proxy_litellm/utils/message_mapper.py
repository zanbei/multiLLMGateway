import time
from typing import List, Dict, Any
from ..models.request_models import ConverseRequest, ContentBlock
from ..models.response_models import ConverseResponse, ResponseMessage, TokenUsage, Metrics, ConverseOutput

def map_to_deepseek_messages(request: ConverseRequest) -> List[Dict[str, str]]:
    """Convert Bedrock format messages to Deepseek format"""
    messages = []

    # Add system message if present
    if request.system:
        messages.append({
            "role": "system",
            "content": request.system[0].text
        })

    # Add conversation messages
    for msg in request.messages:
        if isinstance(msg.content, str):
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        else:
            # For complex content, concatenate text blocks
            content = ""
            for block in msg.content:
                if isinstance(block, dict) and "text" in block:
                    content += block["text"] + "\n"
                elif isinstance(block, ContentBlock) and block.text:
                    content += block.text + "\n"

            if content:
                messages.append({
                    "role": msg.role,
                    "content": content.strip()
                })

    return messages

def map_deepseek_to_bedrock_response(deepseek_response: Any, start_time: float) -> ConverseResponse:
    """Convert Deepseek response to Bedrock format"""
    response_message = ResponseMessage(
        role="assistant",
        content=[ContentBlock(text=deepseek_response.choices[0].message.content)]
    )

    usage = TokenUsage(
        inputTokens=deepseek_response.usage.prompt_tokens,
        outputTokens=deepseek_response.usage.completion_tokens,
        totalTokens=deepseek_response.usage.total_tokens
    )

    metrics = Metrics(
        latencyMs=int((time.time() - start_time) * 1000)
    )

    return ConverseResponse(
        output=ConverseOutput(message=response_message),
        usage=usage,
        metrics=metrics,
        stopReason="end_turn"
    )
