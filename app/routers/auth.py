from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models import User, Role
from app.schemas import Token, UserRegister, UserOut
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

DEFAULT_ROLE_NAME = "customer"


@router.post("/register", response_model=UserOut, status_code=201)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where((User.email == data.email) | (User.username == data.username))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email или имя пользователя уже занято")

    role_result = await db.execute(select(Role).where(Role.role_name == DEFAULT_ROLE_NAME))
    role = role_result.scalar_one_or_none()
    if role is None:
        role = Role(role_name=DEFAULT_ROLE_NAME)
        db.add(role)
        await db.flush()

    user = User(
        username=data.username,
        email=data.email,
        phone=data.phone,
        password_hash=hash_password(data.password),
        role_id=role.role_id,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user, ["role", "created_at"])
    return user


@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    token = create_access_token({"sub": str(user.user_id)})
    return {"access_token": token}
