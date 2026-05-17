from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_current_user, require_admin
from app.models import Order, OrderItem, OrderStatus, Product, User
from app.schemas import OrderCreate, OrderOut, OrderStatusUpdate, OrderStatusOut

router = APIRouter(prefix="/orders", tags=["Orders"])

_load = [
    selectinload(Order.status),
    selectinload(Order.items),
]


async def _fetch_order(order_id: int, db: AsyncSession) -> Order:
    result = await db.execute(
        select(Order).options(*_load).where(Order.order_id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderOut, status_code=201)
async def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    status_result = await db.execute(select(OrderStatus).where(OrderStatus.status_name == "pending"))
    default_status = status_result.scalar_one_or_none()
    if not default_status:
        raise HTTPException(status_code=500, detail="No order statuses configured")

    total = 0
    items_to_add = []
    for item_data in data.items:
        prod_result = await db.execute(
            select(Product).where(Product.product_id == item_data.product_id)
        )
        product = prod_result.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")
        if product.stock_quantity < item_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product {product.product_name}",
            )
        total += product.price * item_data.quantity
        items_to_add.append((product, item_data.quantity))

    order = Order(
        user_id=current_user.user_id,
        status_id=default_status.status_id,
        delivery_address=data.delivery_address,
        payment_method=data.payment_method,
        payment_status="pending",
        total_amount=total,
    )
    db.add(order)
    await db.flush()

    for product, qty in items_to_add:
        db.add(OrderItem(
            order_id=order.order_id,
            product_id=product.product_id,
            quantity=qty,
            price_at_purchase=product.price,
        ))
        product.stock_quantity -= qty

    await db.commit()
    return await _fetch_order(order.order_id, db)


@router.get("/statuses", response_model=list[OrderStatusOut])
async def list_statuses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OrderStatus))
    return result.scalars().all()


@router.get("/my", response_model=list[OrderOut])
async def my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Order).options(*_load).where(Order.user_id == current_user.user_id)
    )
    return result.scalars().all()


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await _fetch_order(order_id, db)
    if order.user_id != current_user.user_id and current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="Access denied")
    return order


@router.get("/", response_model=list[OrderOut], dependencies=[Depends(require_admin)])
async def list_all_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).options(*_load))
    return result.scalars().all()


@router.patch("/{order_id}/status", response_model=OrderOut, dependencies=[Depends(require_admin)])
async def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    order = await _fetch_order(order_id, db)

    status_result = await db.execute(
        select(OrderStatus).where(OrderStatus.status_id == data.status_id)
    )
    if not status_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Status not found")

    order.status_id = data.status_id
    await db.commit()
    return await _fetch_order(order_id, db)
