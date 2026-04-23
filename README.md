# olympiad-rag

Minimal FastAPI service for knowledge storage, RAG-style chat, and response evaluation backed by PostgreSQL with `pgvector`, Redis, and Celery.

## Requirements

- Docker and Docker Compose

## Environment

Copy `.env.example` to `.env` and fill in valid API keys.

Main variables:

| Variable             | Description                   | Fallback                       |
| -------------------- | ----------------------------- | ------------------------------ |
| `API_BASE`           | Default fallback API base URL | `https://openrouter.ai/api/v1` |
| `API_KEY`            | Default fallback API key      | -                              |
| `CHAT_API_BASE`      | Chat completion endpoint      | `API_BASE`                     |
| `CHAT_API_KEY`       | Chat API key                  | `API_KEY`                      |
| `CHAT_MODEL`         | Chat model name               | `openai/gpt-4o-mini`           |
| `EMBEDDING_API_BASE` | Embedding endpoint            | `API_BASE`                     |
| `EMBEDDING_API_KEY`  | Embedding API key             | `API_KEY`                      |
| `EMBEDDING_MODEL`    | Embedding model name          | `text-embedding-3-small`       |
| `EVAL_API_BASE`      | Evaluation endpoint           | `API_BASE`                     |
| `EVAL_API_KEY`       | Evaluation API key            | `API_KEY`                      |
| `EVAL_MODEL`         | Evaluation model name         | `openai/gpt-4o-mini`           |
| `POSTGRES_USER`      | PostgreSQL user               | `postgres`                     |
| `POSTGRES_PASSWORD`  | PostgreSQL password           | `password`                     |
| `POSTGRES_HOST`      | PostgreSQL host               | `localhost`                    |
| `POSTGRES_PORT`      | PostgreSQL port               | `5432`                         |
| `POSTGRES_DB`        | PostgreSQL database           | `postgres`                     |
| `REDIS_HOST`         | Redis host                    | `localhost`                    |
| `REDIS_PORT`         | Redis port                    | `6379`                         |

Chat, embedding, and eval can each point to different API providers. If a specific `*_API_BASE` or `*_API_KEY` is empty or unset, it falls back to `API_BASE` / `API_KEY`.

## Run

Development:

```bash
docker compose --profile dev up --build
```

Production-style:

```bash
docker compose --profile prod up --build -d --scale app=4 --scale worker=4
```

Ports:

- `dev`: `http://127.0.0.1:8000`
- `prod`: `http://0.0.0.0:80`

Services started per profile:

| Service               | dev            | prod |
| --------------------- | -------------- | ---- |
| PostgreSQL (pgvector) | O              | O    |
| Redis                 | O              | O    |
| FastAPI app           | O (hot-reload) | O    |
| Celery worker         | O (hot-reload) | O    |

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

`201 Created`

```json
{ "message": "created" }
```

`409 Conflict`

```json
{ "message": "already exists" }
```

Uniqueness is enforced by `(workspace_id, user_id, file_id)`.

#### List Knowledge

`GET /api/v1/knowledge?workspace_id=...&user_id=...`

```bash
curl "http://127.0.0.1:8000/api/v1/knowledge?workspace_id=ws-1&user_id=user-1"
```

`200 OK`

```json
{ "files": ["file-1", "file-2"] }
```

#### Delete Knowledge

`DELETE /api/v1/knowledge`

```bash
curl -X DELETE http://127.0.0.1:8000/api/v1/knowledge \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id":"ws-1",
    "user_id":"user-1",
    "file_id":"file-1"
  }'
```

`200 OK`

```json
{ "message": "deleted" }
```

`404 Not Found`

```json
{ "message": "not found" }
```

### Chat Completions

`POST /api/v1/chat/completions`

non-stream:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id":"ws-1",
    "user_id":"user-1",
    "files":["file-1"],
    "messages":[{"role":"user","content":"Summarize the stored document."}],
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
    "messages":[{"role":"user","content":"Summarize the stored document."}],
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

- `files`: optional; when omitted, RAG searches across all files for that workspace/user
- `stream`: `false` for JSON response, `true` for SSE streaming
- `curl -N` is important for seeing streamed chunks without client-side buffering

### Eval

Evaluate a query/response pair using an LLM judge. Returns a score from 0.0 to 1.0. Runs asynchronously via Celery.

#### Single Eval

`POST /api/v1/eval`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/eval \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "What is the capital of France?",
    "response": "The capital of France is Paris."
  }'
```

`200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "score": null
}
```

Poll for result:

`GET /api/v1/eval/job/{job_id}`

```bash
curl http://127.0.0.1:8000/api/v1/eval/job/550e8400-e29b-41d4-a716-446655440000
```

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "score": 1.0
}
```

#### Batch Eval

`POST /api/v1/eval/batch`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/eval/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "jobs": [
      { "query": "What is 2+2?", "response": "4" },
      { "query": "Capital of Japan?", "response": "I like pizza" }
    ]
  }'
```

`200 OK`

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "jobs": [],
  "status": "pending"
}
```

Poll for result:

`GET /api/v1/eval/batch/job/{job_id}`

```json
{
  "id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "jobs": [
    {
      "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "status": "completed",
      "score": 1.0
    },
    {
      "id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "status": "completed",
      "score": 0.0
    }
  ],
  "status": "completed"
}
```

Individual eval jobs in a batch run in parallel across Celery workers using `chord`.

### RAG Eval (reval)

End-to-end evaluation of the RAG pipeline: retrieves knowledge, generates a RAG response, then evaluates it. Also runs asynchronously via Celery using `chain(rag -> eval)`.

#### Single RAG Eval

`POST /api/v1/reval`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/reval \
  -H 'Content-Type: application/json' \
  -d '{
    "workspace_id": "ws-1",
    "user_id": "user-1",
    "messages": [{"role": "user", "content": "What is the largest planet?"}],
    "temperature": 0.0
  }'
```

`200 OK`

```json
{
  "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "status": "pending",
  "score": null
}
```

Poll for result:

`GET /api/v1/reval/job/{job_id}`

```json
{
  "id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "status": "completed",
  "score": 1.0
}
```

#### Batch RAG Eval

`POST /api/v1/reval/batch`

```bash
curl -X POST http://127.0.0.1:8000/api/v1/reval/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "jobs": [
      {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "messages": [{"role": "user", "content": "What is the capital of South Korea?"}],
        "temperature": 0.0
      },
      {
        "workspace_id": "ws-1",
        "user_id": "user-1",
        "messages": [{"role": "user", "content": "What is the population of Brazil?"}],
        "temperature": 0.0
      }
    ]
  }'
```

Poll for result:

`GET /api/v1/reval/batch/job/{job_id}`

```json
{
  "id": "d4e5f6a7-b8c9-4d0e-1f2a-3b4c5d6e7f8a",
  "jobs": [
    {
      "id": "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d",
      "status": "completed",
      "score": 1.0
    },
    {
      "id": "9f8e7d6c-5b4a-4392-8170-1e2d3c4b5a69",
      "status": "completed",
      "score": 0.0
    }
  ],
  "status": "completed"
}
```

Batch reval runs each job as a `chain(rag -> eval)` in parallel via `chord`.

## Architecture

```text
Client -> FastAPI (app) -> PostgreSQL (pgvector)
                        -> Redis (broker/backend)
                        -> Celery Worker
                              -> eval: LLM judge scoring
                              -> reval: RAG generation + LLM judge scoring
```

### Task Patterns

- **eval single**: `run_eval` task
- **eval batch**: `chord([run_eval, ...], callback)`
- **reval single**: `chain(run_rag, run_reval_eval)`
- **reval batch**: `chord([chain(run_rag, run_reval_eval), ...], callback)`

### Job Status

All eval/reval jobs return one of these statuses:

| Status      | Description                                 |
| ----------- | ------------------------------------------- |
| `pending`   | Task queued, not yet picked up              |
| `started`   | Task is running                             |
| `completed` | Task finished successfully                  |
| `failure`   | Task failed (e.g. LLM response parse error) |

## RAG Behavior

- Knowledge is embedded at ingest time and stored in PostgreSQL with `pgvector`.
- Chat/reval requests embed the last user message and perform vector similarity search.
- If `files` is provided, retrieval is limited to those `file_id` values.
- If `files` is omitted or `null`, retrieval runs across all files for the same `workspace_id` and `user_id`.

## Logs

When a request performs RAG, the selected chunks are logged:

```text
rag chunks selected workspace_id=ws-1 user_id=user-1 count=2
rag chunk 1 file_id=file-1 content_length=378
rag chunk 2 file_id=file-2 content_length=373
```
