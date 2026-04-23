from celery.result import AsyncResult
from fastapi import APIRouter

from src.jobs import celery
from src.jobs.tasks import run_eval, dispatch_eval_batch
from src.model.eval import (
    EvalBatchRequest,
    EvalBatchResponse,
    EvalRequest,
    EvalResponse,
)


router = APIRouter(tags=["eval"])


@router.post("/api/v1/eval", response_model=EvalResponse)
async def create_eval(payload: EvalRequest):
    task = run_eval.delay(payload.id, payload.query, payload.response)
    return EvalResponse(id=task.id, status="pending")


@router.get("/api/v1/eval/job/{job_id}", response_model=EvalResponse)
async def get_eval_job(job_id: str):
    result = AsyncResult(job_id, app=celery)
    if result.state in ("PENDING", "STARTED", "FAILURE"):
        return EvalResponse(id=job_id, status=result.state.lower())
    return EvalResponse(**result.result)


@router.post("/api/v1/eval/batch", response_model=EvalBatchResponse)
async def create_eval_batch(payload: EvalBatchRequest):
    jobs = [job.model_dump() for job in payload.jobs]
    task_id = dispatch_eval_batch(payload.id, jobs)
    return EvalBatchResponse(id=task_id, jobs=[], status="pending")


@router.get("/api/v1/eval/batch/job/{job_id}", response_model=EvalBatchResponse)
async def get_eval_batch_job(job_id: str):
    result = AsyncResult(job_id, app=celery)
    if result.state in ("PENDING", "STARTED", "FAILURE"):
        return EvalBatchResponse(id=job_id, jobs=[], status=result.state.lower())
    return EvalBatchResponse(**result.result)
