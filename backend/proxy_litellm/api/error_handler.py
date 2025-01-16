import logging
from fastapi import HTTPException
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)

def handle_api_error(error: Exception, request_id: str):
    error_message = str(error)

    if isinstance(error, ClientError):
        error_code = error.response['Error']['Code']
        error_message = error.response['Error']['Message']
        logger.error(f"[{request_id}] AWS ClientError: {error_code} - {error_message}")

        if error_code == "ResourceNotFoundException":
            raise HTTPException(status_code=404, detail=error_message)
        elif error_code == "ValidationException":
            raise HTTPException(status_code=400, detail=error_message)
        elif error_code == "ModelTimeoutException":
            raise HTTPException(status_code=408, detail=error_message)
        elif error_code == "ThrottlingException":
            raise HTTPException(status_code=429, detail=error_message)
        elif error_code == "ServiceUnavailableException":
            raise HTTPException(status_code=503, detail=error_message)

    elif isinstance(error, BotoCoreError):
        logger.error(f"[{request_id}] AWS BotoCoreError: {error_message}")
        raise HTTPException(status_code=500, detail=error_message)

    elif "ResourceNotFoundException" in error_message:
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
        logger.error(f"[{request_id}] Unexpected error: {error_message}")
        raise HTTPException(status_code=500, detail=error_message)
