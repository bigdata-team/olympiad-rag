import os

API_BASE = os.getenv("API_BASE", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("API_KEY", "supersecret!")

CHAT_API_BASE = os.getenv("CHAT_API_BASE") or API_BASE
CHAT_API_KEY = os.getenv("CHAT_API_KEY") or API_KEY
CHAT_MODEL = os.getenv("CHAT_MODEL", "openai/gpt-4o-mini")

EMBEDDING_API_BASE = os.getenv("EMBEDDING_API_BASE") or API_BASE
EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY") or API_KEY
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_SIZE = int(os.getenv("EMBEDDING_SIZE", "1536"))

EVAL_API_BASE = os.getenv("EVAL_API_BASE") or API_BASE
EVAL_API_KEY = os.getenv("EVAL_API_KEY") or API_KEY
EVAL_MODEL = os.getenv("EVAL_MODEL", "openai/gpt-4o-mini")

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "postgres")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:{REDIS_PORT}/1"
