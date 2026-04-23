import json
import logging
from urllib import request
from urllib.error import HTTPError

from src.config import (
    CHAT_API_BASE, CHAT_API_KEY, CHAT_MODEL,
    EMBEDDING_API_BASE, EMBEDDING_API_KEY, EMBEDDING_MODEL, EMBEDDING_SIZE,
)
from src.model.chat import ChatRequest

logger = logging.getLogger(__name__)


def embed_text(text: str) -> list[float]:
    req = request.Request(
        url=f"{EMBEDDING_API_BASE.rstrip('/')}/embeddings",
        data=json.dumps({"model": EMBEDDING_MODEL, "input": text}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            embedding = json.load(response)["data"][0]["embedding"]
    except HTTPError as exc:
        logger.error("embed_text failed: %s %s", exc.code, exc.read().decode())
        raise
    except Exception:
        logger.exception("embed_text unexpected error")
        raise

    if len(embedding) == EMBEDDING_SIZE:
        return embedding
    if len(embedding) > EMBEDDING_SIZE:
        return embedding[:EMBEDDING_SIZE]
    return embedding + [0.0] * (EMBEDDING_SIZE - len(embedding))


def complete(
    messages: list[dict],
    model: str = CHAT_MODEL,
    temperature: float = 1.0,
    api_base: str = CHAT_API_BASE,
    api_key: str = CHAT_API_KEY,
) -> dict:
    req = request.Request(
        url=f"{api_base.rstrip('/')}/chat/completions",
        data=json.dumps(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "stream": False,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            return json.load(response)
    except HTTPError as exc:
        logger.error("complete failed: %s %s", exc.code, exc.read().decode())
        raise
    except Exception:
        logger.exception("complete unexpected error")
        raise


def complete_chat(messages: list[dict], payload: ChatRequest) -> dict:
    return complete(messages, model=CHAT_MODEL, temperature=payload.temperature)


def stream_chat(messages: list[dict], payload: ChatRequest):
    req = request.Request(
        url=f"{CHAT_API_BASE.rstrip('/')}/chat/completions",
        data=json.dumps(
            {
                "model": CHAT_MODEL,
                "messages": messages,
                "top_p": payload.top_p,
                "temperature": payload.temperature,
                "stream": True,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {CHAT_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req) as response:
            while True:
                chunk = response.readline()
                if not chunk:
                    break
                yield chunk
    except HTTPError as exc:
        body = exc.read()
        logger.error("stream_chat failed: %s %s", exc.code, body.decode())
        if body:
            yield body
        raise
