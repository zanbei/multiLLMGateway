from typing import Dict, Any

def map_request_to_bedrock_params(model_id: str, request: Any) -> Dict[str, Any]:
    """
    Maps a ConverseRequest to Bedrock API parameters.

    Args:
        model_id: The ID of the model to use
        request: The ConverseRequest object

    Returns:
        Dict containing the properly formatted parameters for Bedrock's converse API
    """
    # Start with required parameters
    params = {
        "modelId": model_id,
        "messages": [
            {
                "role": message.role,
                "content": _map_content(message.content)
            }
            for message in request.messages
        ]
    }

    # Add optional parameters only if they have values
    if request.system:
        params["system"] = [
            {
                "text": system.text,
                **({"guardContent": system.guardContent} if system.guardContent else {})
            }
            for system in request.system
        ]

    if request.inferenceConfig:
        inference_config = {}
        if request.inferenceConfig.maxTokens is not None:
            inference_config["maxTokens"] = request.inferenceConfig.maxTokens
        if request.inferenceConfig.temperature is not None:
            inference_config["temperature"] = request.inferenceConfig.temperature
        if request.inferenceConfig.topP is not None:
            inference_config["topP"] = request.inferenceConfig.topP
        if request.inferenceConfig.stopSequences is not None:
            inference_config["stopSequences"] = request.inferenceConfig.stopSequences
        if inference_config:
            params["inferenceConfig"] = inference_config

    if request.toolConfig:
        params["toolConfig"] = request.toolConfig.model_dump(exclude_none=True)
    if request.guardrailConfig:
        params["guardrailConfig"] = request.guardrailConfig.model_dump(exclude_none=True)
    if request.promptVariables:
        params["promptVariables"] = request.promptVariables
    if request.additionalModelRequestFields:
        params["additionalModelRequestFields"] = request.additionalModelRequestFields
    if request.additionalModelResponseFieldPaths:
        params["additionalModelResponseFieldPaths"] = request.additionalModelResponseFieldPaths
    if request.requestMetadata:
        params["requestMetadata"] = request.requestMetadata
    if request.performanceConfig:
        params["performanceConfig"] = request.performanceConfig.model_dump(exclude_none=True)

    return params

def _map_content(content: Any) -> list:
    """
    Maps message content to the format expected by Bedrock.

    Args:
        content: The content from the message (can be str or list of ContentBlock)

    Returns:
        List of properly formatted content blocks
    """
    if isinstance(content, str):
        return [{"text": content}]
    elif isinstance(content, list):
        mapped_content = []
        for block in content:
            if isinstance(block, dict):
                mapped_content.append(block)
            else:
                # Convert ContentBlock to dict, excluding None values
                block_dict = block.model_dump(exclude_none=True)
                if block_dict:  # Only add if there are non-None values
                    mapped_content.append(block_dict)
        return mapped_content
    return []
