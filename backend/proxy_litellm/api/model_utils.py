import logging
from typing import Dict, Any
from ..models.request_models import ConverseRequest
from ..utils.bedrock import get_bedrock_models

logger = logging.getLogger(__name__)

def validate_model(model_id: str):
    """Validate that the requested model is supported"""
    if model_id not in get_bedrock_models() and not model_id.startswith("deepseek"):
        error_msg = f"Unsupported model: {model_id}"
        logger.error(error_msg)
        raise ValueError(error_msg)

def prepare_inference_config(request: ConverseRequest) -> Dict[str, Any]:
    """Prepare common inference configuration parameters"""
    config = {
        "temperature": request.temperature if request.temperature is not None else 0.7,
        "max_tokens": request.max_tokens if request.max_tokens is not None else 512,
        "top_p": request.top_p if request.top_p is not None else 0.9,
        "stop_sequences": request.stop_sequences if request.stop_sequences else [],
    }

    # Add model-specific configurations
    if request.model_kwargs:
        config.update(request.model_kwargs)

    return config

def transform_model_parameters(model_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Transform model parameters to the required format"""
    transformed = {}

    if model_id.startswith("anthropic"):
        transformed = {
            "prompt": params.get("prompt", ""),
            "max_tokens_to_sample": params.get("max_tokens", 512),
            "temperature": params.get("temperature", 0.7),
            "top_p": params.get("top_p", 0.9),
            "stop_sequences": params.get("stop_sequences", []),
        }
    elif model_id.startswith("ai21"):
        transformed = {
            "prompt": params.get("prompt", ""),
            "maxTokens": params.get("max_tokens", 512),
            "temperature": params.get("temperature", 0.7),
            "topP": params.get("top_p", 0.9),
            "stopSequences": params.get("stop_sequences", []),
        }

    return transformed
