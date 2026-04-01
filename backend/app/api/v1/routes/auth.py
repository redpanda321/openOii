from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import OptionalUserDep

router = APIRouter()


@router.get("/me")
async def get_me(current_user: dict | None = OptionalUserDep):
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return {"user_id": current_user["user_id"]}
