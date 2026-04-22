from fastapi import APIRouter, Response, status

from src.model.knowledge import (
    KnowledgeCreateRequest,
    KnowledgeCreateResponse,
    KnowledgeDeleteRequest,
    KnowledgeDeleteResponse,
    KnowledgeListRequest,
    KnowledgeListResponse,
)
from src.services.knowledge import (
    create_knowledge as create_knowledge_record,
    delete_knowledge as delete_knowledge_records,
    list_knowledge_files,
)


router = APIRouter(tags=["knowledge"])


@router.get("/api/v1/knowledge", response_model=KnowledgeListResponse)
async def get_knowledge_files(workspace_id: str, user_id: str):
    payload = KnowledgeListRequest(workspace_id=workspace_id, user_id=user_id)
    files = await list_knowledge_files(payload)
    return {"files": files}


@router.post("/api/v1/knowledge", response_model=KnowledgeCreateResponse)
async def create_knowledge(payload: KnowledgeCreateRequest, response: Response):
    created = await create_knowledge_record(payload)
    if created:
        response.status_code = status.HTTP_201_CREATED
        return {"message": "created"}
    response.status_code = status.HTTP_409_CONFLICT
    return {"message": "already exists"}


@router.delete("/api/v1/knowledge", response_model=KnowledgeDeleteResponse)
async def delete_knowledge(payload: KnowledgeDeleteRequest, response: Response):
    deleted = await delete_knowledge_records(payload)
    if deleted:
        response.status_code = status.HTTP_200_OK
        return {"message": "deleted"}
    response.status_code = status.HTTP_404_NOT_FOUND
    return {"message": "not found"}
