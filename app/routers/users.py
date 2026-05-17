from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_admin
from app.models import User, Role
from app.schemas import UserOut, UserUpdate, UserRoleUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await db.refresh(current_user, ["role"])
    return current_user


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.username is not None:
        current_user.username = data.username
    if data.phone is not None:
        current_user.phone = data.phone
    await db.commit()
    await db.refresh(current_user, ["role"])
    return current_user


@router.get("/", response_model=list[UserOut], dependencies=[Depends(require_admin)])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    for u in users:
        await db.refresh(u, ["role"])
    return users


@router.get("/{user_id}", response_model=UserOut, dependencies=[Depends(require_admin)])
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.refresh(user, ["role"])
    return user


@router.patch("/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Разрешено только если: текущий пользователь — админ,
    # ИЛИ в системе ещё нет ни одного админа (первоначальная настройка).
    admin_role_result = await db.execute(select(Role).where(Role.role_name == "admin"))
    admin_role = admin_role_result.scalar_one_or_none()

    is_caller_admin = admin_role and current_user.role_id == admin_role.role_id

    if not is_caller_admin:
        if admin_role:
            admin_count_result = await db.execute(
                select(func.count(User.user_id)).where(User.role_id == admin_role.role_id)
            )
            admin_count = admin_count_result.scalar()
        else:
            admin_count = 0
        if admin_count > 0:
            raise HTTPException(status_code=403, detail="Admins only")

    # Проверяем что целевая роль существует
    role_result = await db.execute(select(Role).where(Role.role_id == data.role_id))
    if not role_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Role not found")

    result = await db.execute(select(User).where(User.user_id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role_id = data.role_id
    await db.commit()
    await db.refresh(user, ["role"])
    return user
