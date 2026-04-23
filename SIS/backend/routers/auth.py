from fastapi import APIRouter, HTTPException, Depends
import re
from pydantic import BaseModel, field_validator

from services.auth_service import register_user, authenticate_user, create_token
from dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


class AuthRequest(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not EMAIL_RE.match(v):
            raise ValueError("Invalid email format")
        return v


class AuthResponse(BaseModel):
    token: str
    user: dict


@router.post("/register", response_model=AuthResponse)
async def register(body: AuthRequest):
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    try:
        user = await register_user(body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    token = create_token(user["id"])
    return AuthResponse(
        token=token,
        user={"id": user["id"], "email": user["email"], "created_at": user["created_at"]},
    )


@router.post("/login", response_model=AuthResponse)
async def login(body: AuthRequest):
    user = await authenticate_user(body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(user["id"])
    return AuthResponse(
        token=token,
        user={"id": user["id"], "email": user["email"], "created_at": user["created_at"]},
    )


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return user
