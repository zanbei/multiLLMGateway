import json
import time
import logging
from typing import Dict, Any

def prepare_bedrock_request(model_id: str, request: Dict[str, Any], request_id: str):
    """Prepare and log Bedrock request parameters"""
    request_params = {"modelId": model_id, **request}
    logging.debug(f"[{request_id}] Bedrock request params: {json.dumps(request_params)}")
    return request_params

def log_successful_request(request_id: str, start_time: float):
    """Log successful request completion"""
    logging.info(f"[{request_id}] Successfully completed request in {time.time() - start_time:.2f}s")

def generate_streaming_response(response, request_id: str):
    """Generate streaming response from Bedrock chunks"""
    async def generate():
        async for event in response['body']:
            if event.get('chunk'):
                chunk_data = event['chunk']
                logging.debug(f"[{request_id}] Received Bedrock chunk: {json.dumps(chunk_data)}")
                yield f"data: {json.dumps(chunk_data)}\n\n"
    return generate()
