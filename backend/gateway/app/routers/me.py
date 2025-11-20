from fastapi import APIRouter, Depends

from app.deps.auth import get_current_user, TokenPayload

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/ping")
async def me_ping(current_user: TokenPayload = Depends(get_current_user)):
    return {
        "message": "pong",
        "user_id": current_user.sub,
    }
