import json
import logging

from src.config import EVAL_API_BASE, EVAL_API_KEY, EVAL_MODEL
from src.model.eval import EvalJobStatus
from src.services.llm import complete
from src.templates import env

logger = logging.getLogger(__name__)

_eval_template = env.get_template("eval_prompt.j2")


def evaluate(job_id: str, query: str, response: str) -> dict:
    prompt = _eval_template.render(query=query, response=response)
    messages = [{"role": "user", "content": prompt}]
    result = complete(messages, model=EVAL_MODEL, temperature=0.0,
                      api_base=EVAL_API_BASE, api_key=EVAL_API_KEY)
    content = result["choices"][0]["message"]["content"]

    try:
        score = json.loads(content)["score"]
        score = max(0.0, min(1.0, float(score)))
    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        logger.warning("eval parse failed job_id=%s content=%s", job_id, content)
        return EvalJobStatus(id=job_id, status="failure", score=None).model_dump()

    return EvalJobStatus(id=job_id, status="completed", score=score).model_dump()
