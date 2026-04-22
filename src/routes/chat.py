from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from src.model.chat import ChatRequest, ChatResponse
from src.services.chat import create_rag_chat_completion, stream_rag_chat_completion


router = APIRouter(tags=["chat"])


@router.post("/api/v1/chat/completions")
async def chat_completion(payload: ChatRequest):
    if payload.stream:
        return StreamingResponse(
            stream_rag_chat_completion(payload),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    return await create_rag_chat_completion(payload)
