from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    TokenResponse,
    UserCreate,
    UserRead,
    UserChangePassword
)


REFRESH_COOKIE_NAME = "refresh_token"

router = APIRouter(prefix="/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


async def get_user_from_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        sub = payload.get("sub")
        if sub is None:
            raise JWTError("Missing sub")
        user_id = UUID(sub)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def create_token(sub: str, expires_delta: timedelta) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": sub,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
    max_age: int,
) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        max_age=max_age,
        path="/auth/refresh",
        samesite="lax",
        secure=False,  # переключите на True в проде за HTTPS
    )


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    
    # Проверяем, что email уникален
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    data: UserCreate,  # переиспользуем форму: email + password
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_expires = timedelta(minutes=settings.access_token_expires_minutes)
    refresh_expires = timedelta(days=settings.refresh_token_expires_days)

    access_token = create_token(sub=str(user.id), expires_delta=access_expires)
    refresh_token = create_token(sub=str(user.id), expires_delta=refresh_expires)

    set_refresh_cookie(
        response=response,
        refresh_token=refresh_token,
        max_age=int(refresh_expires.total_seconds()),
    )

    return TokenResponse(
        access_token=access_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    response: Response,
    user: User = Depends(get_user_from_access_token),
):

    access_expires = timedelta(minutes=settings.access_token_expires_minutes)
    refresh_expires = timedelta(days=settings.refresh_token_expires_days)

    access_token = create_token(sub=str(user.id), expires_delta=access_expires)
    new_refresh_token = create_token(sub=str(user.id), expires_delta=refresh_expires)

    set_refresh_cookie(
        response=response,
        refresh_token=new_refresh_token,
        max_age=int(refresh_expires.total_seconds()),
    )

    return TokenResponse(
        access_token=access_token,
    )

@router.post("/change-password", response_model=TokenResponse)
async def change_password(
    data: UserChangePassword,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Обновляем пароль
    user.password_hash = hash_password(data.newPassword)
    await db.commit()
    await db.refresh(user)

    access_expires = timedelta(minutes=settings.access_token_expires_minutes)
    refresh_expires = timedelta(days=settings.refresh_token_expires_days)

    access_token = create_token(sub=str(user.id), expires_delta=access_expires)
    refresh_token = create_token(sub=str(user.id), expires_delta=refresh_expires)

    set_refresh_cookie(
        response=response,
        refresh_token=refresh_token,
        max_age=int(refresh_expires.total_seconds()),
    )

    return TokenResponse(
        access_token=access_token,
    )



@router.post("/logout")
async def logout(
    response: Response,
    user: User = Depends(get_user_from_access_token),
):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        httponly=True,
        path="/auth/refresh",
        samesite="lax",
        secure=False,  # переключите на True в проде за HTTPS
    )
    return {"detail": "Logged out"}
