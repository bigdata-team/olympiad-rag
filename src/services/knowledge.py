import asyncio
import logging
from src.connection.postgres import get_pool
from src.model.knowledge import (
    KnowledgeCreateRequest,
    KnowledgeDeleteRequest,
    KnowledgeListRequest,
)
from src.services.llm import embed_text


logger_name = "uvicorn.error"


async def create_knowledge(payload: KnowledgeCreateRequest) -> bool:
    embedding = await asyncio.to_thread(embed_text, payload.content)
    embedding_literal = "[" + ",".join(str(value) for value in embedding) + "]"

    pool = await get_pool()
    async with pool.acquire() as conn:
        knowledge_id = await conn.fetchval(
            """
            INSERT INTO knowledge (workspace_id, user_id, file_id, content, embedding)
            VALUES ($1, $2, $3, $4, $5::vector)
            ON CONFLICT (workspace_id, user_id, file_id) DO NOTHING
            RETURNING id
            """,
            payload.workspace_id,
            payload.user_id,
            payload.file_id,
            payload.content,
            embedding_literal,
        )
    return knowledge_id is not None


async def delete_knowledge(payload: KnowledgeDeleteRequest) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            DELETE FROM knowledge
            WHERE workspace_id = $1 AND user_id = $2 AND file_id = $3
            RETURNING id
            """,
            payload.workspace_id,
            payload.user_id,
            payload.file_id,
        )

    deleted_count = len(rows)
    if deleted_count > 1:
        raise RuntimeError("delete_knowledge removed more than one row")
    return deleted_count == 1


async def list_knowledge_files(payload: KnowledgeListRequest) -> list[str]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT file_id
            FROM knowledge
            WHERE workspace_id = $1 AND user_id = $2
            ORDER BY file_id
            """,
            payload.workspace_id,
            payload.user_id,
        )

    return [row["file_id"] for row in rows]


async def search_knowledge(
    workspace_id: str,
    user_id: str,
    query: str,
    file_ids: list[str] | None = None,
    limit: int = 5,
) -> list[str]:
    query_embedding = await asyncio.to_thread(embed_text, query)
    embedding_literal = "[" + ",".join(str(value) for value in query_embedding) + "]"

    pool = await get_pool()
    async with pool.acquire() as conn:
        if file_ids:
            rows = await conn.fetch(
                """
                SELECT file_id, content
                FROM knowledge
                WHERE workspace_id = $1
                  AND user_id = $2
                  AND file_id = ANY($3::text[])
                ORDER BY embedding <=> $4::vector
                LIMIT $5
                """,
                workspace_id,
                user_id,
                file_ids,
                embedding_literal,
                limit,
            )
        else:
            rows = await conn.fetch(
                """
                SELECT file_id, content
                FROM knowledge
                WHERE workspace_id = $1 AND user_id = $2
                ORDER BY embedding <=> $3::vector
                LIMIT $4
                """,
                workspace_id,
                user_id,
                embedding_literal,
                limit,
            )

    if rows:
        logging.getLogger(logger_name).info(
            "rag chunks selected workspace_id=%s user_id=%s count=%s",
            workspace_id,
            user_id,
            len(rows),
        )
        for index, row in enumerate(rows, start=1):
            logging.getLogger(logger_name).info(
                "rag chunk %s file_id=%s content_length=%s",
                index,
                row["file_id"],
                len(row["content"]),
            )
    else:
        logging.getLogger(logger_name).info(
            "rag chunks selected workspace_id=%s user_id=%s count=0",
            workspace_id,
            user_id,
        )

    return [row["content"] for row in rows]
