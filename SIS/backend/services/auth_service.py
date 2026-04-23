from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS
from services.supabase_service import supabase

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


async def register_user(email: str, password: str) -> dict:
    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise ValueError("Email already registered")

    password_hash = hash_password(password)
    result = supabase.table("users").insert({
        "email": email,
        "password_hash": password_hash,
    }).execute()
    return result.data[0]


async def authenticate_user(email: str, password: str) -> dict | None:
    result = supabase.table("users").select("*").eq("email", email).execute()
    if not result.data:
        return None
    user = result.data[0]
    if not verify_password(password, user["password_hash"]):
        return None
    return user


async def get_user_by_id(user_id: str) -> dict | None:
    result = supabase.table("users").select("id, email, created_at").eq("id", user_id).execute()
    if result.data:
        return result.data[0]
    return None
