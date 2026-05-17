from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_admin
from app.models import Brand, CarModel, Car
from app.schemas import BrandCreate, BrandOut, CarModelCreate, CarModelOut, CarCreate, CarOut

router = APIRouter(prefix="/cars", tags=["Cars"])


# ── Brands ────────────────────────────────────────────────────────────────────

@router.get("/brands", response_model=list[BrandOut])
async def list_brands(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand))
    return result.scalars().all()


@router.post("/brands", response_model=BrandOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_brand(data: BrandCreate, db: AsyncSession = Depends(get_db)):
    brand = Brand(**data.model_dump())
    db.add(brand)
    await db.commit()
    await db.refresh(brand)
    return brand


@router.delete("/brands/{brand_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_brand(brand_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Brand).where(Brand.brand_id == brand_id))
    brand = result.scalar_one_or_none()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    await db.delete(brand)
    await db.commit()


# ── Models ────────────────────────────────────────────────────────────────────

@router.get("/models", response_model=list[CarModelOut])
async def list_models(brand_id: int | None = None, db: AsyncSession = Depends(get_db)):
    q = select(CarModel).options(selectinload(CarModel.brand))
    if brand_id:
        q = q.where(CarModel.brand_id == brand_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/models", response_model=CarModelOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_model(data: CarModelCreate, db: AsyncSession = Depends(get_db)):
    model = CarModel(**data.model_dump())
    db.add(model)
    await db.commit()
    result = await db.execute(
        select(CarModel).options(selectinload(CarModel.brand)).where(CarModel.model_id == model.model_id)
    )
    return result.scalar_one()


@router.delete("/models/{model_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_model(model_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(CarModel).where(CarModel.model_id == model_id))
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    await db.delete(model)
    await db.commit()


# ── Cars ──────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[CarOut])
async def list_cars(model_id: int | None = None, db: AsyncSession = Depends(get_db)):
    q = select(Car).options(
        selectinload(Car.model).selectinload(CarModel.brand)
    )
    if model_id:
        q = q.where(Car.model_id == model_id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{car_id}", response_model=CarOut)
async def get_car(car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Car)
        .options(selectinload(Car.model).selectinload(CarModel.brand))
        .where(Car.car_id == car_id)
    )
    car = result.scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.post("/", response_model=CarOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_car(data: CarCreate, db: AsyncSession = Depends(get_db)):
    car = Car(**data.model_dump())
    db.add(car)
    await db.commit()
    result = await db.execute(
        select(Car)
        .options(selectinload(Car.model).selectinload(CarModel.brand))
        .where(Car.car_id == car.car_id)
    )
    return result.scalar_one()


@router.delete("/{car_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_car(car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Car).where(Car.car_id == car_id))
    car = result.scalar_one_or_none()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    await db.delete(car)
    await db.commit()
