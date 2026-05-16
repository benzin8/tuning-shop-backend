from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_admin
from app.models import Category, PartManufacturer
from app.schemas import CategoryCreate, CategoryOut, ManufacturerCreate, ManufacturerOut

router = APIRouter(tags=["Catalog"])


# ── Categories ────────────────────────────────────────────────────────────────

@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    return result.scalars().all()


@router.post("/categories", response_model=CategoryOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db)):
    cat = Category(**data.model_dump())
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categories/{category_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category).where(Category.category_id == category_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(cat)
    await db.commit()


# ── Part Manufacturers ────────────────────────────────────────────────────────

@router.get("/manufacturers", response_model=list[ManufacturerOut])
async def list_manufacturers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PartManufacturer))
    return result.scalars().all()


@router.post("/manufacturers", response_model=ManufacturerOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_manufacturer(data: ManufacturerCreate, db: AsyncSession = Depends(get_db)):
    mfr = PartManufacturer(**data.model_dump())
    db.add(mfr)
    await db.commit()
    await db.refresh(mfr)
    return mfr


@router.delete("/manufacturers/{manufacturer_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_manufacturer(manufacturer_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(PartManufacturer).where(PartManufacturer.manufacturer_id == manufacturer_id))
    mfr = result.scalar_one_or_none()
    if not mfr:
        raise HTTPException(status_code=404, detail="Manufacturer not found")
    await db.delete(mfr)
    await db.commit()
