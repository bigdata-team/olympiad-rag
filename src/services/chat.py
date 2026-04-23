import asyncio
import threading

from src.model.chat import ChatRequest
from src.services.knowledge import search_knowledge
from src.services.llm import complete_chat, stream_chat
from src.templates import env

_rag_template = env.get_template("rag_system_prompt.j2")


def _build_rag_system_prompt(system_messages: list[str], contexts: list[str]) -> str:
    return _rag_template.render(
        system_messages=system_messages,
        contexts=contexts,
    ).strip()


async def build_rag_messages(payload: ChatRequest) -> list[dict] | None:
    user_messages = [message for message in payload.messages if message.role == "user"]
    if not user_messages:
        return None

    system_messages = [
        message.content for message in payload.messages if message.role == "system"
    ]

    query = user_messages[-1].content
    contexts = await search_knowledge(
        payload.workspace_id,
        payload.user_id,
        query,
        payload.files,
    )

    messages = [
        message.model_dump() for message in payload.messages if message.role != "system"
    ]
    system_prompt = _build_rag_system_prompt(system_messages, contexts)
    if system_prompt:
        messages.insert(
            0,
            {"role": "system", "content": system_prompt},
        )

    return messages


async def create_rag_chat_completion(payload: ChatRequest) -> dict:
    messages = await build_rag_messages(payload)
    if messages is None:
        return {
            "id": "local-empty-user-message",
            "object": "chat.completion",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "A user message is required.",
                    },
                    "finish_reason": "stop",
                }
            ],
        }

    return await asyncio.to_thread(complete_chat, messages, payload)


async def stream_rag_chat_completion(payload: ChatRequest):
    messages = await build_rag_messages(payload)
    if messages is None:
        yield b'data: {"id":"local-empty-user-message","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant","content":"A user message is required."},"finish_reason":"stop"}]}\n\n'
        yield b"data: [DONE]\n\n"
        return

    queue: asyncio.Queue[bytes | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _stream_worker() -> None:
        try:
            for chunk in stream_chat(messages, payload):
                asyncio.run_coroutine_threadsafe(queue.put(chunk), loop).result()
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(None), loop).result()

    threading.Thread(target=_stream_worker, daemon=True).start()

    while True:
        chunk = await queue.get()
        if chunk is None:
            break
        yield chunk
