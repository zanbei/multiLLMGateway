from typing import Dict, Any
import json
import os
import time
from fastapi.responses import StreamingResponse
from .utils import BaseHandler

OPENAI_API_URL = os.environ.get("OPENAI_API_URL", "http://127.0.0.1:4000/v1/chat/completions")

class OpenAIHandler(BaseHandler):
    def _convert_bedrock_to_openai(self, bedrock_request: Dict[str, Any], model_id: str) -> Dict[str, Any]:
        """Convert Bedrock request format to OpenAI format"""
        # Clean up messages by removing None values
        messages = bedrock_request.get("messages", [{
            "role": "user",
            "content": bedrock_request.get("prompt", "")
        }])

        # Clean up message content
        for msg in messages:
            if isinstance(msg.get("content"), list):
                # If content is a list of content items, extract just the text
                msg["content"] = next((
                    item.get("text") for item in msg["content"]
                    if isinstance(item, dict) and item.get("text")
                ), "")

        # Build request without None values
        request = {
            "model": model_id,
            "messages": messages
        }

        # Add optional parameters only if they exist
        if "temperature" in bedrock_request:
            request["temperature"] = bedrock_request["temperature"]
        if "max_tokens" in bedrock_request:
            request["max_tokens"] = bedrock_request["max_tokens"]
        if "stream" in bedrock_request:
            request["stream"] = bedrock_request["stream"]

        return request

    def _convert_to_bedrock_response(self, openai_response: Dict[str, Any], start_time: float) -> Dict[str, Any]:
        """Convert OpenAI response format to Bedrock format"""
        # Extract message from first choice
        choice = openai_response["choices"][0] if openai_response["choices"] else {}
        message = choice.get("message", {})

        # Build output with message structure
        output = {
            "message": {
                "role": message.get("role", "assistant"),
                "content": [{"text": message.get("content", "")}]
            }
        }

        # Calculate elapsed time in milliseconds
        elapsed_ms = int((time.time() - start_time) * 1000)

        # Basic Bedrock response structure
        bedrock_response = {
            "output": output,
            "stopReason": openai_response["choices"][0]["finish_reason"] if openai_response["choices"] else "stop",
            "metrics": {
                "latencyMs": elapsed_ms
            },
            "usage": {
                "inputTokens": openai_response["usage"]["prompt_tokens"],
                "outputTokens": openai_response["usage"]["completion_tokens"],
                "totalTokens": openai_response["usage"]["total_tokens"]
            },
            "performanceConfig": {
                "latency": "low"  # Default value
            },
            "trace": {
                "promptRouter": {
                    "invokedModelId": openai_response["model"]
                }
            },
            # Preserve original OpenAI fields that might be useful
            "additionalModelResponseFields": {
                "id": openai_response.get("id"),
                "created": openai_response.get("created"),
                "model": openai_response.get("model"),
                "system_fingerprint": openai_response.get("system_fingerprint"),
                "object": openai_response.get("object"),
                # Preserve function/tool calls if present
                "function_call": openai_response["choices"][0]["message"].get("function_call") if openai_response["choices"] else None,
                "tool_calls": openai_response["choices"][0]["message"].get("tool_calls") if openai_response["choices"] else None
            }
        }
        return bedrock_response

    def _convert_to_bedrock_stream_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Convert OpenAI stream chunk to Bedrock format"""
        if not chunk.get("choices"):
            return {}

        delta = chunk["choices"][0].get("delta", {})
        content = delta.get("content", "")
        finish_reason = chunk["choices"][0].get("finish_reason")
        index = chunk["choices"][0].get("index", 0)

        # If this is the first chunk with role, send messageStart and contentBlockStart
        if delta.get("role"):
            return {
                "messageStart": {
                    "role": delta["role"]
                },
                "contentBlockStart": {
                    "contentBlockIndex": index,
                    "start": {}
                }
            }

        # If we have a finish reason, send contentBlockStop and messageStop
        if finish_reason:
            return {
                "contentBlockStop": {
                    "contentBlockIndex": index
                },
                "messageStop": {
                    "stopReason": finish_reason,
                    "metrics": {
                        "latencyMs": 0
                    },
                    "usage": {
                        "inputTokens": chunk.get("usage", {}).get("prompt_tokens", 0),
                        "outputTokens": chunk.get("usage", {}).get("completion_tokens", 0),
                        "totalTokens": chunk.get("usage", {}).get("total_tokens", 0)
                    }
                }
            }

        # For content, send contentBlockDelta
        if content:
            return {
                "contentBlockDelta": {
                    "contentBlockIndex": index,
                    "delta": {
                        "text": content
                    }
                }
            }

        return {}

    async def handle_converse(self, model_id: str, request: Dict[str, Any],
                            api_key: str, request_id: str, start_time: float):
        """Handle non-streaming conversation requests"""
        openai_request = self._convert_bedrock_to_openai(request, model_id)
        self._log_request(request_id, openai_request)

        # Extract AWS access key from Credential header if it exists
        headers = {"Authorization": f"Bearer {api_key}"}
        if "Authorization" in request:
            credential = request["Authorization"]
            try:
                # Split by 'Credential=' and get the second part
                credential_part = credential.split('Credential=')[1]
                # Split by '/' and get the first part (access key)
                headers["x-aws-accesskey"] = credential_part.split('/')[0]
            except (IndexError, AttributeError):
                pass

        session = await self.session
        async with session.post(
            OPENAI_API_URL,
            headers=headers,
            json=openai_request
        ) as response:
            if response.status != 200:
                self._handle_error(ValueError(await response.text()), request_id)

            data = await response.json()
            self._log_success(request_id, start_time)

            return self._convert_to_bedrock_response(data, start_time)

    async def handle_stream(self, model_id: str, request: Dict[str, Any],
                          api_key: str, request_id: str, start_time: float):
        """Handle streaming conversation requests"""
        openai_request = self._convert_bedrock_to_openai(request, model_id)
        openai_request["stream"] = True
        self._log_request(request_id, openai_request)

        # Extract AWS access key from Credential header if it exists
        headers = {"Authorization": f"Bearer {api_key}"}
        if "Credential" in request:
            credential = request["Credential"]
            access_key = credential.split("/")[0].replace("Credential=", "")
            headers["x-aws-accesskey"] = access_key

        async def generate():
            session = await self.session
            async with session.post(
                OPENAI_API_URL,
                headers=headers,
                json=openai_request
            ) as response:
                if response.status != 200:
                    self._handle_error(ValueError(await response.text()), request_id)

                async for line in response.content:
                    if line.startswith(b"data: "):
                        chunk = line[6:].strip()
                        if chunk == b"[DONE]":
                            self._log_success(request_id, start_time)
                            break

                        try:
                            data = json.loads(chunk)
                            bedrock_chunk = self._convert_to_bedrock_stream_chunk(data)
                            yield f"data: {json.dumps(bedrock_chunk)}\n\n"
                        except json.JSONDecodeError:
                            continue

        return StreamingResponse(generate(), media_type="text/event-stream")
