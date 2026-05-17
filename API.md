# Tuning Shop API — Документация

Base URL: `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

---

## Аутентификация

Все защищённые эндпоинты требуют заголовок:
```
Authorization: Bearer <access_token>
```

---

## Auth

### POST /auth/register
Регистрация нового пользователя.

**Body:**
```json
{
  "username": "string",
  "email": "user@example.com",
  "phone": "string | null",
  "password": "string (мин. 6 символов)"
}
```

**Response 201:**
```json
{
  "user_id": 1,
  "username": "string",
  "email": "string",
  "phone": "string | null",
  "role": { "role_id": 2, "role_name": "customer" },
  "created_at": "2024-01-01T00:00:00"
}
```

---

### POST /auth/login
Логин. Принимает `application/x-www-form-urlencoded`.

**Body (form):**
```
username=string&password=string
```

**Response 200:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

---

## Users

### GET /users/me 🔒
Профиль текущего пользователя.

**Response 200:** `UserOut`

---

### PATCH /users/me 🔒
Обновить свой профиль.

**Body:**
```json
{
  "username": "string | null",
  "phone": "string | null"
}
```

**Response 200:** `UserOut`

---

### GET /users/ 🔒👑
Список всех пользователей. Только admin.

**Response 200:** `UserOut[]`

---

### GET /users/{user_id} 🔒👑
Получить пользователя по ID. Только admin.

**Response 200:** `UserOut`

---

### PATCH /users/{user_id}/role 🔒
Изменить роль пользователя.

- Если в системе **нет ни одного админа** — доступно любому авторизованному пользователю (первоначальная настройка).
- Если админ уже есть — только admin.

**Body:**
```json
{ "role_id": 1 }
```

Роли: `1` = admin, `2` = customer.

**Response 200:** `UserOut`

---

## Products

### GET /products/
Список товаров с фильтрацией.

**Query params:**
| Параметр | Тип | Описание |
|---|---|---|
| category_id | int | Фильтр по категории |
| manufacturer_id | int | Фильтр по производителю |
| car_id | int | Только совместимые с авто |
| skip | int | Пагинация (default: 0) |
| limit | int | Пагинация (default: 50) |

**Response 200:** `ProductOut[]`

---

### GET /products/{product_id}
Получить товар по ID.

**Response 200:** `ProductOut`

---

### POST /products/ 🔒👑
Создать товар. Только admin.

**Body:**
```json
{
  "category_id": 1,
  "manufacturer_id": 1,
  "sku": "string",
  "product_name": "string",
  "description": "string | null",
  "image_url": "string | null",
  "price": "decimal",
  "stock_quantity": 0
}
```

**Response 201:** `ProductOut`

---

### PATCH /products/{product_id} 🔒👑
Обновить товар. Только admin.

**Body:** любые поля из `ProductCreate` кроме sku/category/manufacturer, все опциональны.

**Response 200:** `ProductOut`

---

### DELETE /products/{product_id} 🔒👑
Удалить товар. Только admin.

**Response 204**

---

### POST /products/{product_id}/compatibility 🔒👑
Добавить совместимость товара с автомобилем.

**Body:**
```json
{ "product_id": 1, "car_id": 1 }
```

**Response 201:** `CompatibilityOut`

---

### DELETE /products/{product_id}/compatibility/{car_id} 🔒👑
Удалить совместимость. Только admin.

**Response 204**

---

## Categories

### GET /categories/
Список категорий.

**Response 200:** `CategoryOut[]`

---

### POST /categories/ 🔒👑
Создать категорию. Только admin.

**Body:** `{ "category_name": "string" }`

**Response 201:** `CategoryOut`

---

### DELETE /categories/{category_id} 🔒👑
Удалить категорию. Только admin.

**Response 204**

---

## Cars

### GET /cars/brands/
Список брендов автомобилей.

**Response 200:** `BrandOut[]`

---

### POST /cars/brands/ 🔒👑
Создать бренд.

**Body:** `{ "brand_name": "string" }`

**Response 201:** `BrandOut`

---

### GET /cars/models/
Список моделей. Query param: `brand_id` (опционально).

**Response 200:** `CarModelOut[]`

---

### POST /cars/models/ 🔒👑
Создать модель.

**Body:** `{ "brand_id": 1, "model_name": "string" }`

**Response 201:** `CarModelOut`

---

### GET /cars/
Список автомобилей. Query param: `model_id` (опционально).

**Response 200:** `CarOut[]`

---

### POST /cars/ 🔒👑
Создать автомобиль.

**Body:**
```json
{
  "model_id": 1,
  "generation": "string | null",
  "year_start": 2010,
  "year_end": 2015
}
```

**Response 201:** `CarOut`

---

## Orders

### POST /orders/ 🔒
Создать заказ. Автоматически списывает остатки.

**Body:**
```json
{
  "delivery_address": "string",
  "payment_method": "string",
  "items": [
    { "product_id": 1, "quantity": 2 }
  ]
}
```

**Response 201:** `OrderOut`

---

### GET /orders/my 🔒
Мои заказы.

**Response 200:** `OrderOut[]`

---

### GET /orders/{order_id} 🔒
Получить заказ. Пользователь видит только свои, admin — любые.

**Response 200:** `OrderOut`

---

### GET /orders/ 🔒👑
Все заказы. Только admin.

**Response 200:** `OrderOut[]`

---

### PATCH /orders/{order_id}/status 🔒👑
Сменить статус заказа. Только admin.

**Body:** `{ "status_id": 2 }`

Статусы: `pending → confirmed → processing → shipped → delivered → cancelled`

**Response 200:** `OrderOut`

---

## Схемы ответов

### UserOut
```json
{
  "user_id": 1,
  "username": "string",
  "email": "string",
  "phone": "string | null",
  "role": { "role_id": 1, "role_name": "admin" },
  "created_at": "2024-01-01T00:00:00"
}
```

### ProductOut
```json
{
  "product_id": 1,
  "sku": "string",
  "product_name": "string",
  "description": "string | null",
  "image_url": "string | null",
  "price": "0.00",
  "stock_quantity": 0,
  "category": { "category_id": 1, "category_name": "string" },
  "manufacturer": { "manufacturer_id": 1, "manufacturer_name": "string" }
}
```

### OrderOut
```json
{
  "order_id": 1,
  "user_id": 1,
  "status": { "status_id": 1, "status_name": "pending" },
  "delivery_address": "string",
  "payment_method": "string",
  "payment_status": "pending",
  "total_amount": "0.00",
  "created_at": "2024-01-01T00:00:00",
  "items": [
    {
      "item_id": 1,
      "product_id": 1,
      "quantity": 1,
      "price_at_purchase": "0.00"
    }
  ]
}
```

---

🔒 — требует авторизации  
👑 — только admin
