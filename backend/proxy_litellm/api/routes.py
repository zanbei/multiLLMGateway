from fastapi import APIRouter, Depends
from typing import Annotated

from ..models.request_models import ConverseRequest
from .auth import get_api_key
from .handlers import handle_converse, handle_converse_stream

router = APIRouter()

@router.post("/model/{model_id}/converse")
async def converse(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
):
    return await handle_converse(model_id, request, api_key)

@router.post("/model/{model_id}/converse-stream")
async def converse_stream(
    model_id: str,
    request: ConverseRequest,
    api_key: Annotated[str, Depends(get_api_key)]
):
    return await handle_converse_stream(model_id, request, api_key)
