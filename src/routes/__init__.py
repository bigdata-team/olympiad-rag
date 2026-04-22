from .default import router as default_router
from .chat import router as chat_router
from .knowledge import router as knowledge_router

routers = [
    chat_router,
    knowledge_router,
]

__all__ = routers
