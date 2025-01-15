# Bedrock to OpenAI Proxy

This is a reverse proxy that translates Amazon Bedrock Converse API requests to OpenAI chat completion API requests.

## Setup

1. Install dependencies:
```bash
pip install fastapi uvicorn python-dotenv openai
```

1. Configure your environment variables:
- `OPENAI_API_BASE`: OpenAI API base URL (defaults to http://127.0.0.1:4000)

## Running the Proxy

Start the server:
```bash
python proxy.py
```

The proxy will run on http://localhost:8000

## API Usage

The proxy implements the Bedrock Converse API endpoint. You can make requests to:

```
POST /model/{model_id}/converse
```

Example request:
```json
{
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "text": "Hello world"
                }
            ]
        }
    ],
    "system": [
        {
            "text": "You are a helpful assistant"
        }
    ],
    "inferenceConfig": {
        "temperature": 0.7,
        "maxTokens": 100,
        "topP": 0.9,
        "stopSequences": ["STOP"]
    }
}
```

Example response:
```json
{
    "output": {
        "message": {
            "role": "assistant",
            "content": [
                {
                    "text": "Hello! How can I help you today?"
                }
            ]
        }
    },
    "usage": {
        "inputTokens": 20,
        "outputTokens": 8,
        "totalTokens": 28
    },
    "metrics": {
        "latencyMs": 500
    },
    "stopReason": "end_turn"
}
```

## Features

- Translates Bedrock request format to OpenAI format
- Maps inference configuration parameters:
  - maxTokens → max_tokens
  - temperature → temperature
  - topP → top_p
  - stopSequences → stop

### Parameter Mapping Details

#### Supported Parameters
1. Messages:
   - role (user/assistant/system) → maps directly
   - content.text → maps to content string

2. System Messages:
   - text → maps to system role message

3. Inference Configuration:
   - maxTokens → max_tokens
   - temperature → temperature
   - topP → top_p
   - stopSequences → stop

#### Unsupported Bedrock Parameters
1. Request Parameters:
   - guardrailConfig - No equivalent in OpenAI API
   - performanceConfig - No equivalent in OpenAI API
   - promptVariables - No equivalent in OpenAI API
   - requestMetadata - No equivalent in OpenAI API
   - toolConfig - Partially supported through functions in OpenAI API but requires custom mapping

2. Response Parameters:
   - trace - No equivalent in OpenAI API
   - performanceConfig - No equivalent in OpenAI API

Note: Any unsupported parameters sent in the request will be ignored. If you need specific functionality from these parameters, you'll need to implement custom handling logic.

Other Features:
- Handles token usage metrics
- Supports additional model request fields via additionalModelRequestFields
- Error handling with appropriate status codes
- Configurable API endpoint

## Error Handling

The proxy returns appropriate HTTP status codes:
- 400: Invalid request format
- 500: Internal server error or OpenAI API error
