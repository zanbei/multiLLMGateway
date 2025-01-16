# Proxy LiteLLM Server

A FastAPI server that proxies requests to both AWS Bedrock and Deepseek models through LiteLLM.

## Running the Server

There are several ways to run the server:

1. Using Python module:
```bash
python -m proxy_litellm
```

2. Using uvicorn directly:
```bash
uvicorn proxy_litellm.core.app:app --host 0.0.0.0 --port 8000 --log-level debug
```

The server will start on http://localhost:8000

## Configuration

The server requires:

1. LiteLLM configuration file (`litellm_config.yaml`)
2. AWS credentials for Bedrock access:
   - AWS_ACCESS_KEY_ID
   - AWS_SECRET_ACCESS_KEY
   - AWS_REGION_NAME (defaults to "us-east-1")

## API Endpoints

The server exposes two main endpoints:

1. `/model/{model_id}/converse` - For regular chat completions
2. `/model/{model_id}/converse-stream` - For streaming chat completions

Both endpoints require an `x-bedrock-api-key` header for authentication.

### Model IDs

- For AWS Bedrock models: Use the model ID from AWS (e.g., "anthropic.claude-v2")
- For Deepseek models: Use models starting with "deepseek" prefix
