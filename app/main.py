from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import engine, Base, AsyncSessionLocal
from app.models import (
    Role, OrderStatus, Category, PartManufacturer,
    Brand, CarModel, Car, Product, ProductCarCompatibility,
)
from app.routers import auth, users, products, categories, cars, orders
from app.routers import roles


async def _get_or_create(db, model, filter_kwargs, create_kwargs=None):
    res = await db.execute(select(model).filter_by(**filter_kwargs))
    obj = res.scalar_one_or_none()
    if obj is None:
        obj = model(**(create_kwargs or filter_kwargs))
        db.add(obj)
        await db.flush()
    return obj


async def _seed_defaults() -> None:
    async with AsyncSessionLocal() as db:
        # Роли и статусы заказов
        for name in ("admin", "customer"):
            await _get_or_create(db, Role, {"role_name": name})

        for name in ("pending", "confirmed", "processing", "shipped", "delivered", "cancelled"):
            await _get_or_create(db, OrderStatus, {"status_name": name})

        # Категории
        cat_suspension = await _get_or_create(db, Category, {"category_name": "Подвеска"})
        cat_brakes = await _get_or_create(db, Category, {"category_name": "Тормоза"})
        cat_engine = await _get_or_create(db, Category, {"category_name": "Двигатель"})
        cat_electric = await _get_or_create(db, Category, {"category_name": "Электрика"})
        cat_body = await _get_or_create(db, Category, {"category_name": "Кузов"})

        # Производители
        mfr_kyb = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "KYB"})
        mfr_brembo = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "Brembo"})
        mfr_ngk = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "NGK"})
        mfr_bosch = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "Bosch"})
        mfr_mann = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "Mann"})

        # Бренды и модели авто
        brand_toyota = await _get_or_create(db, Brand, {"brand_name": "Toyota"})
        brand_bmw = await _get_or_create(db, Brand, {"brand_name": "BMW"})
        brand_lada = await _get_or_create(db, Brand, {"brand_name": "LADA"})

        model_camry = await _get_or_create(db, CarModel, {"brand_id": brand_toyota.brand_id, "model_name": "Camry"})
        model_3series = await _get_or_create(db, CarModel, {"brand_id": brand_bmw.brand_id, "model_name": "3 Series"})
        model_vesta = await _get_or_create(db, CarModel, {"brand_id": brand_lada.brand_id, "model_name": "Vesta"})

        car_camry = await _get_or_create(
            db, Car, {"model_id": model_camry.model_id, "year_start": 2018},
            {"model_id": model_camry.model_id, "generation": "XV70", "year_start": 2018, "year_end": 2024},
        )
        car_3series = await _get_or_create(
            db, Car, {"model_id": model_3series.model_id, "year_start": 2019},
            {"model_id": model_3series.model_id, "generation": "G20", "year_start": 2019, "year_end": None},
        )
        car_vesta = await _get_or_create(
            db, Car, {"model_id": model_vesta.model_id, "year_start": 2015},
            {"model_id": model_vesta.model_id, "generation": None, "year_start": 2015, "year_end": None},
        )

        # Товары
        products_data = [
            {
                "sku": "SUS-KYB-001",
                "product_name": "Амортизатор передний KYB Excel-G",
                "description": "Газомасляный амортизатор для передней подвески. Обеспечивает комфортное управление и стабильность.",
                "price": "4590.00",
                "stock_quantity": 24,
                "category_id": cat_suspension.category_id,
                "manufacturer_id": mfr_kyb.manufacturer_id,
                "cars": [car_camry, car_3series],
            },
            {
                "sku": "SUS-KYB-002",
                "product_name": "Амортизатор задний KYB Gas-A-Just",
                "description": "Однотрубный газовый амортизатор задней оси. Повышенный ресурс, спортивные характеристики.",
                "price": "3990.00",
                "stock_quantity": 18,
                "category_id": cat_suspension.category_id,
                "manufacturer_id": mfr_kyb.manufacturer_id,
                "cars": [car_camry],
            },
            {
                "sku": "BRK-BRE-001",
                "product_name": "Колодки тормозные передние Brembo P50078",
                "description": "Высокоэффективные тормозные колодки из органического состава. Минимальный шум и пыль.",
                "price": "3200.00",
                "stock_quantity": 32,
                "category_id": cat_brakes.category_id,
                "manufacturer_id": mfr_brembo.manufacturer_id,
                "cars": [car_camry, car_3series],
            },
            {
                "sku": "BRK-BRE-002",
                "product_name": "Тормозной диск Brembo 09.A262.11",
                "description": "Вентилируемый тормозной диск с антикоррозийным покрытием. Улучшенное охлаждение.",
                "price": "5800.00",
                "stock_quantity": 14,
                "category_id": cat_brakes.category_id,
                "manufacturer_id": mfr_brembo.manufacturer_id,
                "cars": [car_3series],
            },
            {
                "sku": "ENG-NGK-001",
                "product_name": "Свечи зажигания NGK Iridium IX (4 шт.)",
                "description": "Иридиевые свечи зажигания с улучшенным воспламенением. Ресурс до 100 000 км.",
                "price": "2400.00",
                "stock_quantity": 56,
                "category_id": cat_engine.category_id,
                "manufacturer_id": mfr_ngk.manufacturer_id,
                "cars": [car_camry, car_vesta],
            },
            {
                "sku": "ENG-MAN-001",
                "product_name": "Масляный фильтр Mann W 712/75",
                "description": "Фильтр тонкой очистки масла. Двойное уплотнение, антидренажный клапан.",
                "price": "420.00",
                "stock_quantity": 120,
                "category_id": cat_engine.category_id,
                "manufacturer_id": mfr_mann.manufacturer_id,
                "cars": [car_camry, car_3series, car_vesta],
            },
            {
                "sku": "ENG-MAN-002",
                "product_name": "Воздушный фильтр Mann C 25 004",
                "description": "Фильтр очистки воздуха двигателя. Высокая степень фильтрации, долгий ресурс.",
                "price": "680.00",
                "stock_quantity": 88,
                "category_id": cat_engine.category_id,
                "manufacturer_id": mfr_mann.manufacturer_id,
                "cars": [car_vesta],
            },
            {
                "sku": "ELC-BOS-001",
                "product_name": "Аккумулятор Bosch S4 60Ah 540A",
                "description": "Стартерный аккумулятор с кальциевой технологией. Низкий саморазряд, необслуживаемый.",
                "price": "8900.00",
                "stock_quantity": 9,
                "category_id": cat_electric.category_id,
                "manufacturer_id": mfr_bosch.manufacturer_id,
                "cars": [car_camry, car_3series, car_vesta],
            },
        ]

        for pdata in products_data:
            cars_list = pdata.pop("cars")
            res = await db.execute(select(Product).where(Product.sku == pdata["sku"]))
            product = res.scalar_one_or_none()
            if product is None:
                product = Product(**pdata)
                db.add(product)
                await db.flush()
                for car in cars_list:
                    compat_res = await db.execute(
                        select(ProductCarCompatibility).where(
                            ProductCarCompatibility.product_id == product.product_id,
                            ProductCarCompatibility.car_id == car.car_id,
                        )
                    )
                    if compat_res.scalar_one_or_none() is None:
                        db.add(ProductCarCompatibility(product_id=product.product_id, car_id=car.car_id))

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
    allow_origins=["http://localhost:5173"],
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
