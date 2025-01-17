# LiteLLM Proxy Service

A FastAPI-based proxy service that provides a unified interface for multiple Language Model providers (Bedrock, OpenAI, etc.). This service standardizes the API interface and handles request routing, authentication, and response processing.

## Features

- Unified API interface for multiple LLM providers
- Support for AWS Bedrock and OpenAI
- Request/Response handling and validation
- Streaming support
- Configurable logging
- Multiple deployment options (Docker, CDK, Terraform)

## Project Structure

```
backend/
├── proxy_litellm/          # Main service implementation
│   ├── api/               # API routes and handlers
│   ├── core/             # Core application logic
│   ├── models/           # Request/Response models
│   └── utils/            # Utility functions
├── deploy/               # Deployment configurations
│   ├── cdk/             # AWS CDK deployment
│   ├── docker/          # Docker deployment
│   └── terraform/       # Terraform deployment
└── logs/                # Application logs
```

## Requirements

- Python 3.8+
- FastAPI
- Uvicorn
- boto3 (for AWS Bedrock)
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Running Locally

Start the server:

```bash
python -m proxy_litellm
```

The server will start on `http://localhost:8000`

### Docker Deployment

Build and run using Docker:

```bash
cd deploy/docker
docker build -t litellm-proxy .
docker run -p 8000:8000 litellm-proxy
```

### AWS Deployment

The service can be deployed to AWS using either CDK or Terraform. See the respective directories in `deploy/` for detailed instructions.

## Configuration

The service can be configured using environment variables or configuration files:

- `log_conf.yaml`: Logging configuration


## Logging

Logs are written to both console and file:
- Console: Debug level logging
- File: Configurable via log_conf.yaml
