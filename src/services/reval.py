import asyncio

from src.config import CHAT_MODEL
from src.model.chat import ChatRequest, Message
from src.services.chat import build_rag_messages
from src.services.llm import complete
import src.connection.postgres as pg


async def _build_rag_response(job: dict) -> tuple[str, str]:
    messages_raw = job["messages"]
    payload = ChatRequest(
        workspace_id=job["workspace_id"],
        user_id=job["user_id"],
        files=job.get("files"),
        messages=[Message(**m) for m in messages_raw],
        top_p=job.get("top_p", 1.0),
        temperature=job.get("temperature", 1.0),
    )

    user_messages = [m for m in messages_raw if m["role"] == "user"]
    query = user_messages[-1]["content"] if user_messages else ""

    messages = await build_rag_messages(payload)
    if messages is None:
        return query, ""

    result = complete(messages, model=CHAT_MODEL, temperature=payload.temperature)
    response = result["choices"][0]["message"]["content"]
    await pg.close_db()
    return query, response


def generate_rag_response(job: dict) -> tuple[str, str]:
    """RAG 응답을 생성하고 (query, response) 튜플을 반환합니다."""
    return asyncio.run(_build_rag_response(job))
