from sqlalchemy import select, text

from app.database import AsyncSessionLocal, engine
from app.models import (
    Role, OrderStatus,
    Category, PartManufacturer,
    Brand, CarModel, Car, Product, ProductCarCompatibility,
    Service,
)


async def _get_or_create(db, model, filter_kwargs, create_kwargs=None):
    res = await db.execute(select(model).filter_by(**filter_kwargs))
    obj = res.scalar_one_or_none()
    if obj is None:
        obj = model(**(create_kwargs or filter_kwargs))
        db.add(obj)
        await db.flush()
    return obj


async def _run_migrations() -> None:
    """Apply lightweight schema migrations that create_all cannot handle."""
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE services ADD COLUMN IF NOT EXISTS "
            "requires_gibdd BOOLEAN NOT NULL DEFAULT FALSE"
        ))


async def seed() -> None:
    await _run_migrations()

    async with AsyncSessionLocal() as db:
        # ── Роли и статусы заказов ────────────────────────────────────────────
        for name in ("admin", "customer"):
            await _get_or_create(db, Role, {"role_name": name})

        for name in ("pending", "confirmed", "processing", "shipped", "delivered", "cancelled"):
            await _get_or_create(db, OrderStatus, {"status_name": name})

        # ── Категории ─────────────────────────────────────────────────────────
        cat_suspension = await _get_or_create(db, Category, {"category_name": "Подвеска"})
        cat_brakes     = await _get_or_create(db, Category, {"category_name": "Тормоза"})
        cat_engine     = await _get_or_create(db, Category, {"category_name": "Двигатель"})
        cat_electric   = await _get_or_create(db, Category, {"category_name": "Электрика"})
        cat_body       = await _get_or_create(db, Category, {"category_name": "Кузов"})

        # ── Производители ─────────────────────────────────────────────────────
        mfr_kyb    = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "KYB"})
        mfr_brembo = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "Brembo"})
        mfr_ngk    = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "NGK"})
        mfr_bosch  = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "Bosch"})
        mfr_mann   = await _get_or_create(db, PartManufacturer, {"manufacturer_name": "Mann"})

        # ── Бренды и модели ───────────────────────────────────────────────────
        brand_toyota = await _get_or_create(db, Brand, {"brand_name": "Toyota"})
        brand_bmw    = await _get_or_create(db, Brand, {"brand_name": "BMW"})
        brand_lada   = await _get_or_create(db, Brand, {"brand_name": "LADA"})

        model_camry   = await _get_or_create(db, CarModel, {"brand_id": brand_toyota.brand_id, "model_name": "Camry"})
        model_3series = await _get_or_create(db, CarModel, {"brand_id": brand_bmw.brand_id,    "model_name": "3 Series"})
        model_vesta   = await _get_or_create(db, CarModel, {"brand_id": brand_lada.brand_id,   "model_name": "Vesta"})

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

        # ── Товары ────────────────────────────────────────────────────────────
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

        # ── Услуги тюнинга ────────────────────────────────────────────────────
        # requires_gibdd=True: услуга требует внесения изменений в конструкцию
        # ТС и регистрации в ГИБДД согласно ст. 12.5 КоАП и Постановлению
        # Правительства РФ №413.
        services_data = [
            # ── Без регистрации ГИБДД ─────────────────────────────────────────
            {
                "name": "Чип-тюнинг ECU (Stage 1)",
                "description": "Программная оптимизация блока управления двигателем: прирост мощности и крутящего момента без замены агрегатов. Не меняет тип двигателя — регистрация в ГИБДД не требуется.",
                "price_from": 8000,
                "duration": "2–3 часа",
                "category": "Двигатель",
                "requires_gibdd": False,
            },
            {
                "name": "Замена тормозных дисков и колодок",
                "description": "Установка тюнинговых дисков и колодок (Brembo, Endless, DBA) вместо штатных аналогов. Замена эквивалентными сертифицированными компонентами не требует регистрации.",
                "price_from": 3500,
                "duration": "1–2 часа",
                "category": "Тормоза",
                "requires_gibdd": False,
            },
            {
                "name": "Замена амортизаторов и пружин",
                "description": "Монтаж спортивных амортизаторов и пружин (KYB, Bilstein, Eibach) взамен штатных. При изменении клиренса не более допустимого — регистрация не нужна.",
                "price_from": 4500,
                "duration": "2–4 часа",
                "category": "Подвеска",
                "requires_gibdd": False,
            },
            {
                "name": "Развал-схождение на 3D-стенде",
                "description": "Точная регулировка углов установки колёс. Обязательна после замены элементов подвески. Не является изменением конструкции.",
                "price_from": 1500,
                "duration": "30–60 минут",
                "category": "Подвеска",
                "requires_gibdd": False,
            },
            {
                "name": "Антигравийная плёнка PPF",
                "description": "Оклейка прозрачной полиуретановой плёнкой для защиты лакокрасячного покрытия. Не меняет цвет — регистрация в ГИБДД не требуется.",
                "price_from": 12000,
                "duration": "1–2 дня",
                "category": "Кузов",
                "requires_gibdd": False,
            },
            {
                "name": "Полировка и нанесение керамики",
                "description": "Машинная полировка кузова, нанесение керамического или тефлонового защитного состава. Сохраняет оригинальный цвет — регистрация не нужна.",
                "price_from": 6000,
                "duration": "1–2 дня",
                "category": "Кузов",
                "requires_gibdd": False,
            },
            {
                "name": "Установка мультимедиа, камер, парктроников",
                "description": "Замена штатной магнитолы на Android-головное устройство, установка камер 360°, парктроников и видеорегистраторов. Аксессуарное оборудование не требует регистрации.",
                "price_from": 2500,
                "duration": "2–4 часа",
                "category": "Электрика",
                "requires_gibdd": False,
            },
            {
                "name": "Промывка форсунок",
                "description": "Ультразвуковая очистка топливных форсунок на стенде. Восстанавливает характеристики распыла и расход топлива. Ремонтная операция — регистрация не нужна.",
                "price_from": 2000,
                "duration": "1–2 часа",
                "category": "Двигатель",
                "requires_gibdd": False,
            },
            # ── Требуют регистрации ГИБДД ─────────────────────────────────────
            {
                "name": "Установка ГБО (газобаллонное оборудование)",
                "description": "Монтаж пропан-бутановой или метановой системы питания. Увеличивает пробег на одном баке, снижает затраты на топливо. Внесение изменений в конструкцию ТС — требует регистрации в ГИБДД.",
                "price_from": 25000,
                "duration": "1–2 дня",
                "category": "Двигатель",
                "requires_gibdd": True,
            },
            {
                "name": "Оклейка / покраска в другой цвет",
                "description": "Полная или частичная смена цвета кузова виниловой плёнкой или краской. Изменение цвета фиксируется в ПТС — необходима регистрация изменений в ГИБДД.",
                "price_from": 35000,
                "duration": "3–7 дней",
                "category": "Кузов",
                "requires_gibdd": True,
            },
            {
                "name": "Установка нештатных фар (ксенон / LED в рефлекторы)",
                "description": "Установка ксеноновых или светодиодных источников света в штатные рефлекторные блок-фары. Изменение типа источника света — требует сертификации и регистрации в ГИБДД.",
                "price_from": 8000,
                "duration": "2–3 часа",
                "category": "Электрика",
                "requires_gibdd": True,
            },
        ]

        for sdata in services_data:
            existing = await db.execute(select(Service).where(Service.name == sdata["name"]))
            service = existing.scalar_one_or_none()
            if service is None:
                db.add(Service(**sdata))
            else:
                # update mutable fields on re-seed
                for field in ("description", "price_from", "duration", "category", "requires_gibdd"):
                    setattr(service, field, sdata[field])

        await db.commit()
