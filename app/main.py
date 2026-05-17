from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import engine, Base, AsyncSessionLocal
from app.models import (
    Role, OrderStatus, Category, PartManufacturer,
    Brand, CarModel, Car, Product, ProductCarCompatibility, Service,
)
from app.routers import auth, users, products, categories, cars, orders, roles
from app.routers import services as services_router


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
                "image_url": "https://loremflickr.com/600/400/shock,absorber?lock=12",
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
                "image_url": "https://loremflickr.com/600/400/shock,absorber?lock=7",
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
                "image_url": "https://loremflickr.com/600/400/brake,pads?lock=3",
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
                "image_url": "https://loremflickr.com/600/400/brake,rotor?lock=1",
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
                "image_url": "https://loremflickr.com/600/400/spark,plug?lock=2",
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
                "image_url": "https://s7g10.scene7.com/is/image/mannhummel/W_712-filter-with-box-1?qlt=82&dpr=off&wid=600",
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
                "image_url": "https://s7g10.scene7.com/is/image/mannhummel/C_25_004-filter-with-box-1?qlt=82&dpr=off&wid=600",
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
                "image_url": "https://loremflickr.com/600/400/car,battery?lock=4",
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
            else:
                if pdata.get("image_url"):
                    product.image_url = pdata["image_url"]

        await db.commit()

        # Услуги тюнинга
        services_data = [
            {
                "name": "Чип-тюнинг двигателя",
                "description": "Перепрошивка ЭБУ для увеличения мощности, крутящего момента и улучшения отклика педали газа. Работаем с большинством марок и моделей.",
                "price_from": 8000,
                "duration": "2–4 часа",
                "category": "Двигатель",
            },
            {
                "name": "Установка спортивной подвески",
                "description": "Монтаж резьбовых стоек, пружин, стабилизаторов. Настройка высоты и жёсткости под ваши задачи — трек или город.",
                "price_from": 5000,
                "duration": "3–5 часов",
                "category": "Подвеска",
            },
            {
                "name": "Монтаж выхлопной системы",
                "description": "Замена штатного выхлопа на спортивный: прямоток, катбэк, даунпайп. Увеличение мощности и характерный звук.",
                "price_from": 4000,
                "duration": "2–3 часа",
                "category": "Выхлоп",
            },
            {
                "name": "Тормозной апгрейд",
                "description": "Замена дисков, колодок и суппортов на спортивные аналоги. Прокачка тормозной системы и проверка геометрии.",
                "price_from": 3500,
                "duration": "1.5–3 часа",
                "category": "Тормоза",
            },
            {
                "name": "Антигравийная плёнка и оклейка",
                "description": "Защита лакокрасочного покрытия антигравийной плёнкой PPF или декоративная оклейка виниловой плёнкой.",
                "price_from": 12000,
                "duration": "1–3 дня",
                "category": "Кузов",
            },
            {
                "name": "Установка мультимедиа и камер",
                "description": "Замена штатной магнитолы, установка камер 360°, парктроников, видеорегистраторов и систем мониторинга слепых зон.",
                "price_from": 2500,
                "duration": "2–4 часа",
                "category": "Электрика",
            },
            {
                "name": "Промывка и настройка форсунок",
                "description": "Ультразвуковая очистка форсунок, проверка производительности и при необходимости замена уплотнений.",
                "price_from": 2000,
                "duration": "1–2 часа",
                "category": "Двигатель",
            },
            {
                "name": "Развал-схождение (стенд)",
                "description": "Точная регулировка углов установки колёс на 3D-стенде. Обязательна после замены элементов подвески или при неравномерном износе шин.",
                "price_from": 1500,
                "duration": "30–60 минут",
                "category": "Подвеска",
            },
        ]

        for sdata in services_data:
            await _get_or_create(db, Service, {"name": sdata["name"]}, sdata)

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
app.include_router(services_router.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
