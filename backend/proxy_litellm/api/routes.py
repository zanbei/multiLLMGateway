from fastapi import APIRouter, Depends
from typing import Annotated

from ..models.request_models import ConverseRequest
from .auth import get_api_key
from ..core.handler import handler

router = APIRouter()

@router.post("/model/{model_id}/converse")
async def converse(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
):
    return await handler.handle_request(model_id, request.dict(), api_key)

@router.post("/model/{model_id}/converse-stream")
async def converse_stream(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
):
    return await handler.handle_request(model_id, request.dict(), api_key, stream=True)
