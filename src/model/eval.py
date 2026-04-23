from pydantic import BaseModel, Field
import uuid
from typing import Literal

from src.model.chat import Message


class EvalJob(BaseModel):
    id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    response: str


class EvalJobStatus(BaseModel):
    id: str
    status: Literal["pending", "started", "completed", "failure"]
    score: float | None = None


class EvalJobBatch(BaseModel):
    id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))
    jobs: list[EvalJob]


class EvalJobBatchStatus(BaseModel):
    id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))
    jobs: list[EvalJobStatus]
    status: Literal["pending", "started", "completed", "failure"]


EvalRequest = EvalJob
EvalResponse = EvalJobStatus

EvalBatchRequest = EvalJobBatch
EvalBatchResponse = EvalJobBatchStatus


class REvalJob(BaseModel):
    id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))
    workspace_id: str
    user_id: str
    files: list[str] | None = None
    messages: list[Message]
    top_p: float = 1.0
    top_k: int = 0
    temperature: float = 1.0


class REvalJobBatch(BaseModel):
    id: str | None = Field(default_factory=lambda: str(uuid.uuid4()))
    jobs: list[REvalJob]


REvalRequest = REvalJob
REvalResponse = EvalResponse

REvalBatchRequest = REvalJobBatch
REvalBatchResponse = EvalBatchResponse
