from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from config import settings
from models import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Single pre-hashed credential from .env — not stored in DB for simplicity
_HASHED_PASSWORD = _pwd_ctx.hash(settings.APP_PASSWORD)


def _create_token(username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(token: Annotated[str, Depends(_oauth2_scheme)]) -> str:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exc
    except JWTError:
        raise credentials_exc
    return username


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest):
    valid_user = body.username == settings.APP_USERNAME
    valid_pass = _pwd_ctx.verify(body.password, _HASHED_PASSWORD)
    if not (valid_user and valid_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = _create_token(body.username)
    return TokenResponse(
        access_token=token,
        expires_in_seconds=settings.JWT_EXPIRE_HOURS * 3600,
    )
