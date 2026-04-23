from fastapi import APIRouter


router = APIRouter(tags=["default"])


@router.get("/ping")
async def ping():
    return "pong"
