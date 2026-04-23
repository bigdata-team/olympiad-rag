from celery import chain, chord

from .celery_app import celery
from src.services.eval import evaluate
from src.services.reval import generate_rag_response
from src.model.eval import EvalBatchResponse, REvalBatchResponse


# --- eval tasks ---

@celery.task(name="eval.run")
def run_eval(job_id: str, query: str, response: str) -> dict:
    return evaluate(job_id, query, response)


@celery.task(name="eval.batch_callback")
def eval_batch_callback(results: list[dict], batch_id: str) -> dict:
    return EvalBatchResponse(
        id=batch_id,
        jobs=results,
        status="completed",
    ).model_dump()


def dispatch_eval_batch(batch_id: str, jobs: list[dict]) -> str:
    callback = eval_batch_callback.s(batch_id=batch_id)
    header = [run_eval.s(j["id"], j["query"], j["response"]) for j in jobs]
    result = chord(header)(callback)
    return result.id


# --- reval tasks ---

@celery.task(name="reval.rag")
def run_rag(job: dict) -> dict:
    query, response = generate_rag_response(job)
    return {"job_id": job["id"], "query": query, "response": response}


@celery.task(name="reval.eval")
def run_reval_eval(rag_result: dict) -> dict:
    return evaluate(rag_result["job_id"], rag_result["query"], rag_result["response"])


@celery.task(name="reval.batch_callback")
def reval_batch_callback(results: list[dict], batch_id: str) -> dict:
    return REvalBatchResponse(
        id=batch_id,
        jobs=results,
        status="completed",
    ).model_dump()


def dispatch_reval(job: dict) -> str:
    c = chain(run_rag.s(job), run_reval_eval.s())
    result = c.apply_async()
    return result.id


def dispatch_reval_batch(batch_id: str, jobs: list[dict]) -> str:
    header = [chain(run_rag.s(j), run_reval_eval.s()) for j in jobs]
    callback = reval_batch_callback.s(batch_id=batch_id)
    result = chord(header)(callback)
    return result.id
