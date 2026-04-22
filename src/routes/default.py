from fastapi import APIRouter, HTTPException, Header

from src.model.knowledge import KnowledgeCreateRequest


router = APIRouter(tags=["default"])


@router.get("/ping")
async def ping():
    return "pong"
