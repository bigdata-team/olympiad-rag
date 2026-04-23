from celery.result import AsyncResult
from fastapi import APIRouter

from src.jobs import celery
from src.jobs.tasks import dispatch_reval, dispatch_reval_batch
from src.model.eval import (
    REvalBatchRequest,
    REvalBatchResponse,
    REvalRequest,
    REvalResponse,
)


router = APIRouter(tags=["rag eval"])


@router.post("/api/v1/reval", response_model=REvalResponse)
async def create_reval(payload: REvalRequest):
    task_id = dispatch_reval(payload.model_dump())
    return REvalResponse(id=task_id, status="pending")


@router.get("/api/v1/reval/job/{job_id}", response_model=REvalResponse)
async def get_reval_job(job_id: str):
    result = AsyncResult(job_id, app=celery)
    if result.state in ("PENDING", "STARTED", "FAILURE"):
        return REvalResponse(id=job_id, status=result.state.lower())
    return REvalResponse(**result.result)


@router.post("/api/v1/reval/batch", response_model=REvalBatchResponse)
async def create_reval_batch(payload: REvalBatchRequest):
    jobs = [job.model_dump() for job in payload.jobs]
    task_id = dispatch_reval_batch(payload.id, jobs)
    return REvalBatchResponse(id=task_id, jobs=[], status="pending")


@router.get("/api/v1/reval/batch/job/{job_id}", response_model=REvalBatchResponse)
async def get_reval_batch_job(job_id: str):
    result = AsyncResult(job_id, app=celery)
    if result.state in ("PENDING", "STARTED", "FAILURE"):
        return REvalBatchResponse(id=job_id, jobs=[], status=result.state.lower())
    return REvalBatchResponse(**result.result)
