import json
from urllib import request
from urllib.error import HTTPError

from src.config import API_BASE, API_KEY, CHAT_MODEL, EMBEDDING_MODEL, EMBEDDING_SIZE
from src.model.chat import ChatRequest


def embed_text(text: str) -> list[float]:
    req = request.Request(
        url=f"{API_BASE.rstrip('/')}/embeddings",
        data=json.dumps({"model": EMBEDDING_MODEL, "input": text}).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req) as response:
        embedding = json.load(response)["data"][0]["embedding"]

    if len(embedding) == EMBEDDING_SIZE:
        return embedding
    if len(embedding) > EMBEDDING_SIZE:
        return embedding[:EMBEDDING_SIZE]
    return embedding + [0.0] * (EMBEDDING_SIZE - len(embedding))


def complete_chat(messages: list[dict], payload: ChatRequest) -> dict:
    req = request.Request(
        url=f"{API_BASE.rstrip('/')}/chat/completions",
        data=json.dumps(
            {
                "model": CHAT_MODEL,
                "messages": messages,
                "top_p": payload.top_p,
                "temperature": payload.temperature,
                "stream": False,
            }
        ).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with request.urlopen(req) as response:
        return json.load(response)


def stream_chat(messages: list[dict], payload: ChatRequest):
    req = request.Request(
        url=f"{API_BASE.rstrip('/')}/chat/completions",
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
            "Authorization": f"Bearer {API_KEY}",
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
        if body:
            yield body
        raise
