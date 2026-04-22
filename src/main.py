from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from src.connection.postgres import close_db, init_db
from src.routes import routers


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    await init_db()
    try:
        yield
    finally:
        await close_db()


app = FastAPI(lifespan=lifespan)

for router in routers:
    app.include_router(router)
