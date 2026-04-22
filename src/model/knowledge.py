from pydantic import BaseModel


class KnowledgeCreateRequest(BaseModel):
    workspace_id: str
    user_id: str
    file_id: str
    content: str


class KnowledgeDeleteRequest(BaseModel):
    workspace_id: str
    user_id: str
    file_id: str


class KnowledgeListRequest(BaseModel):
    workspace_id: str
    user_id: str


class KnowledgeCreateResponse(BaseModel):
    message: str


class KnowledgeDeleteResponse(BaseModel):
    message: str


class KnowledgeListResponse(BaseModel):
    files: list[str]
