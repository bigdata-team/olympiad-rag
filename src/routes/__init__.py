from .default import router as default_router
from .chat import router as chat_router
from .knowledge import router as knowledge_router
from .eval import router as eval_router
from .reval import router as reval_router

routers = [
    default_router,
    chat_router,
    knowledge_router,
    eval_router,
    reval_router,
]

__all__ = routers
