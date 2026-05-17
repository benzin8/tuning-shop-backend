from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import engine, Base, AsyncSessionLocal
from app.models import Role, OrderStatus
from app.routers import auth, users, products, categories, cars, orders
from app.routers import roles


async def _seed_defaults() -> None:
    async with AsyncSessionLocal() as db:
        for name in ("admin", "customer"):
            res = await db.execute(select(Role).where(Role.role_name == name))
            if res.scalar_one_or_none() is None:
                db.add(Role(role_name=name))

        for name in ("pending", "confirmed", "processing", "shipped", "delivered", "cancelled"):
            res = await db.execute(select(OrderStatus).where(OrderStatus.status_name == name))
            if res.scalar_one_or_none() is None:
                db.add(OrderStatus(status_name=name))

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_defaults()
    yield


app = FastAPI(
    title="Tuning Shop API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(roles.router)
app.include_router(products.router)
app.include_router(categories.router)
app.include_router(cars.router)
app.include_router(orders.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
