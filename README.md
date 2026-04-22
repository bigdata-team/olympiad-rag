# olympiad-rag

Minimal FastAPI service for knowledge storage and RAG-style chat backed by PostgreSQL with `pgvector`.

## Requirements

- Docker and Docker Compose

## Environment

Copy `.env.example` to `.env` and fill in a valid API key.

Main variables:

- `API_BASE`
- `API_KEY`
- `CHAT_MODEL`
- `EMBEDDING_MODEL`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`

If `API_KEY` is missing or invalid, embedding/chat requests will fail with `401 Unauthorized`.

## Run

Development:

```bash
docker compose --profile dev up --build
```

Production-style:

```bash
docker compose --profile prod up --build
```

Ports:

- `dev`: `http://127.0.0.1:8000`
- `prod`: `http://127.0.0.1:80`

## Reset

```bash
docker compose down -v
```

## API

### Health

```bash
curl http://127.0.0.1:8000/ping
```

### Knowledge

#### Create Knowledge

`POST /api/v1/knowledge`

curl example:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/knowledge \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id":"ws-1",
    "user_id":"user-1",
    "file_id":"file-1",
    "content":"This is the knowledge content."
  }'
```

request body:

```json
{
  "workspace_id": "ws-1",
  "user_id": "user-1",
  "file_id": "file-1",
  "content": "This is the knowledge content."
}
```

response body:

`201 Created`

```json
{
  "message": "created"
}
```

`409 Conflict`

```json
{
  "message": "already exists"
}
```

Uniqueness is enforced by `(workspace_id, user_id, file_id)`.

#### Get Knowledge

`GET /api/v1/knowledge?workspace_id=...&user_id=...`

curl example:

```bash
curl "http://127.0.0.1:8000/api/v1/knowledge?workspace_id=ws-1&user_id=user-1"
```

request body:

- none

response body:

`200 OK`

```json
{
  "files": ["file-1", "file-2"]
}
```

#### Delete Knowledge

`DELETE /api/v1/knowledge`

curl example:

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/knowledge \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id":"ws-1",
    "user_id":"user-1",
    "file_id":"file-1"
  }'
```

request body:

```json
{
  "workspace_id": "ws-1",
  "user_id": "user-1",
  "file_id": "file-1"
}
```

response body:

`200 OK`

```json
{
  "message": "deleted"
}
```

`404 Not Found`

```json
{
  "message": "not found"
}
```

### Chat Completions

`POST /api/v1/chat/completions`

curl example:

non-stream:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id":"ws-1",
    "user_id":"user-1",
    "files":["file-1"],
    "messages":[
      {"role":"user","content":"Summarize the stored document."}
    ],
    "stream":false
  }'
```

stream:

```bash
curl -N -X POST http://127.0.0.1:8000/api/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id":"ws-1",
    "user_id":"user-1",
    "files":["file-1"],
    "messages":[
      {"role":"user","content":"Summarize the stored document."}
    ],
    "stream":true
  }'
```

request body:

```json
{
  "workspace_id": "ws-1",
  "user_id": "user-1",
  "files": ["file-1"],
  "messages": [{ "role": "user", "content": "Summarize the stored document." }],
  "top_p": 1.0,
  "top_k": 0,
  "temperature": 1.0,
  "stream": false
}
```

response body:

non-stream:

`200 OK`

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ]
}
```

stream:

`200 OK`

- `text/event-stream`
- SSE chunks are forwarded from the upstream chat API

notes:

- `workspace_id`: search scope
- `user_id`: search scope
- `files`: optional; when omitted or `null`, RAG searches across all files for that `workspace_id` and `user_id`
- `messages`: chat messages
- `top_p`, `temperature`: forwarded to the upstream chat API
- `top_k`: accepted by the request model but not currently forwarded upstream
- `stream`: `false` for JSON response, `true` for SSE streaming

`curl -N` is important for seeing streamed chunks without client-side buffering.

## RAG Behavior

- Knowledge is embedded at ingest time and stored in PostgreSQL with `pgvector`.
- Chat requests embed the last user message and perform vector similarity search.
- If `files` is provided, retrieval is limited to those `file_id` values.
- If `files` is omitted or `null`, retrieval runs across all files for the same `workspace_id` and `user_id`.

## Logs

When a chat request performs RAG, the selected chunks are logged in the app container output.

Example log lines:

```text
rag chunks selected workspace_id=ws-1 user_id=user-1 count=2
rag chunk 1 file_id=file-1 content=...
rag chunk 2 file_id=file-2 content=...
```
