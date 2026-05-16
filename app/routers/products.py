from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_admin
from app.models import Product, ProductCarCompatibility
from app.schemas import ProductCreate, ProductUpdate, ProductOut, CompatibilityCreate, CompatibilityOut

router = APIRouter(prefix="/products", tags=["Products"])

_load = selectinload(Product.category), selectinload(Product.manufacturer)


@router.get("/", response_model=list[ProductOut])
async def list_products(
    category_id: int | None = Query(None),
    manufacturer_id: int | None = Query(None),
    car_id: int | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    q = select(Product).options(*_load).offset(skip).limit(limit)
    if category_id:
        q = q.where(Product.category_id == category_id)
    if manufacturer_id:
        q = q.where(Product.manufacturer_id == manufacturer_id)
    if car_id:
        compat_ids = (
            await db.execute(
                select(ProductCarCompatibility.product_id).where(
                    ProductCarCompatibility.car_id == car_id
                )
            )
        ).scalars().all()
        q = q.where(Product.product_id.in_(compat_ids))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Product).options(*_load).where(Product.product_id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductOut, status_code=201, dependencies=[Depends(require_admin)])
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    result = await db.execute(
        select(Product).options(*_load).where(Product.product_id == product.product_id)
    )
    return result.scalar_one()


@router.patch("/{product_id}", response_model=ProductOut, dependencies=[Depends(require_admin)])
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.product_id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    await db.commit()
    result = await db.execute(
        select(Product).options(*_load).where(Product.product_id == product_id)
    )
    return result.scalar_one()


@router.delete("/{product_id}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.product_id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await db.delete(product)
    await db.commit()


# ── Compatibility ─────────────────────────────────────────────────────────────

@router.post("/{product_id}/compatibility", response_model=CompatibilityOut, status_code=201, dependencies=[Depends(require_admin)])
async def add_compatibility(product_id: int, data: CompatibilityCreate, db: AsyncSession = Depends(get_db)):
    compat = ProductCarCompatibility(product_id=product_id, car_id=data.car_id)
    db.add(compat)
    await db.commit()
    await db.refresh(compat)
    return compat


@router.delete("/{product_id}/compatibility/{car_id}", status_code=204, dependencies=[Depends(require_admin)])
async def remove_compatibility(product_id: int, car_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ProductCarCompatibility).where(
            ProductCarCompatibility.product_id == product_id,
            ProductCarCompatibility.car_id == car_id,
        )
    )
    compat = result.scalar_one_or_none()
    if not compat:
        raise HTTPException(status_code=404, detail="Compatibility not found")
    await db.delete(compat)
    await db.commit()
