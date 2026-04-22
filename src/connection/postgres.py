import asyncpg

from src.config import (
    EMBEDDING_SIZE,
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
)


_pool: asyncpg.Pool | None = None


def _postgres_dsn() -> str:
    return (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
        f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=_postgres_dsn())
    return _pool


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS knowledge (
                id BIGSERIAL PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                file_id TEXT NOT NULL,
                content TEXT NOT NULL,
                embedding VECTOR({EMBEDDING_SIZE}) NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        await conn.execute(
            """
            ALTER TABLE knowledge
            ADD COLUMN IF NOT EXISTS user_id TEXT
            """
        )
        await conn.execute(
            """
            ALTER TABLE knowledge
            ADD COLUMN IF NOT EXISTS file_id TEXT
            """
        )
        await conn.execute(
            """
            UPDATE knowledge
            SET user_id = ''
            WHERE user_id IS NULL
            """
        )
        await conn.execute(
            """
            UPDATE knowledge
            SET file_id = ''
            WHERE file_id IS NULL
            """
        )
        await conn.execute(
            """
            ALTER TABLE knowledge
            ALTER COLUMN user_id SET NOT NULL
            """
        )
        await conn.execute(
            """
            ALTER TABLE knowledge
            ALTER COLUMN file_id SET NOT NULL
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS knowledge_workspace_id_idx
            ON knowledge (workspace_id)
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS knowledge_workspace_file_id_idx
            ON knowledge (workspace_id, file_id)
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS knowledge_workspace_user_file_id_idx
            ON knowledge (workspace_id, user_id, file_id)
            """
        )
        await conn.execute(
            """
            DELETE FROM knowledge
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY workspace_id, user_id, file_id
                               ORDER BY created_at DESC, id DESC
                           ) AS row_num
                    FROM knowledge
                ) ranked
                WHERE row_num > 1
            )
            """
        )
        await conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS knowledge_workspace_user_file_unique_idx
            ON knowledge (workspace_id, user_id, file_id)
            """
        )


async def close_db() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
