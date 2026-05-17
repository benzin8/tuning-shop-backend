from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, field_validator


# ── Auth ──────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: int | None = None


# ── Role ──────────────────────────────────────────────────────────────────────

class RoleOut(BaseModel):
    role_id: int
    role_name: str
    model_config = {"from_attributes": True}


# ── User ──────────────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    phone: str | None = None
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")
        return v


class UserOut(BaseModel):
    user_id: int
    username: str
    email: str
    phone: str | None
    role: RoleOut
    created_at: datetime
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: str | None = None
    phone: str | None = None


class UserRoleUpdate(BaseModel):
    role_id: int


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    category_name: str


class CategoryOut(BaseModel):
    category_id: int
    category_name: str
    model_config = {"from_attributes": True}


# ── PartManufacturer ──────────────────────────────────────────────────────────

class ManufacturerCreate(BaseModel):
    manufacturer_name: str


class ManufacturerOut(BaseModel):
    manufacturer_id: int
    manufacturer_name: str
    model_config = {"from_attributes": True}


# ── Product ───────────────────────────────────────────────────────────────────

class ProductCreate(BaseModel):
    category_id: int
    manufacturer_id: int
    sku: str | None = None
    product_name: str
    description: str | None = None
    image_url: str | None = None
    price: Decimal
    stock_quantity: int = 0


class ProductUpdate(BaseModel):
    product_name: str | None = None
    description: str | None = None
    image_url: str | None = None
    price: Decimal | None = None
    stock_quantity: int | None = None


class ProductOut(BaseModel):
    product_id: int
    sku: str
    product_name: str
    description: str | None
    image_url: str | None
    price: Decimal
    stock_quantity: int
    is_active: bool
    category: CategoryOut
    manufacturer: ManufacturerOut
    model_config = {"from_attributes": True}


# ── Brand & CarModel & Car ────────────────────────────────────────────────────

class BrandCreate(BaseModel):
    brand_name: str


class BrandOut(BaseModel):
    brand_id: int
    brand_name: str
    model_config = {"from_attributes": True}


class CarModelCreate(BaseModel):
    brand_id: int
    model_name: str


class CarModelOut(BaseModel):
    model_id: int
    model_name: str
    brand: BrandOut
    model_config = {"from_attributes": True}


class CarCreate(BaseModel):
    model_id: int
    generation: str | None = None
    year_start: int | None = None
    year_end: int | None = None


class CarOut(BaseModel):
    car_id: int
    generation: str | None
    year_start: int | None
    year_end: int | None
    model: CarModelOut
    model_config = {"from_attributes": True}


# ── Compatibility ─────────────────────────────────────────────────────────────

class CompatibilityCreate(BaseModel):
    product_id: int
    car_id: int


class CompatibilityOut(BaseModel):
    compatibility_id: int
    product_id: int
    car_id: int
    model_config = {"from_attributes": True}


# ── Order ─────────────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

    @field_validator("quantity")
    @classmethod
    def quantity_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Quantity must be >= 1")
        return v


class OrderCreate(BaseModel):
    delivery_address: str
    payment_method: str
    items: list[OrderItemCreate]


class OrderItemOut(BaseModel):
    item_id: int
    product_id: int
    quantity: int
    price_at_purchase: Decimal
    model_config = {"from_attributes": True}


class OrderStatusOut(BaseModel):
    status_id: int
    status_name: str
    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    order_id: int
    user_id: int
    status: OrderStatusOut
    delivery_address: str
    payment_method: str
    payment_status: str
    total_amount: Decimal
    created_at: datetime
    items: list[OrderItemOut]
    model_config = {"from_attributes": True}


class OrderStatusUpdate(BaseModel):
    status_id: int


# ── Services ──────────────────────────────────────────────────────────────────

class ServiceOut(BaseModel):
    service_id: int
    name: str
    description: str | None
    price_from: Decimal | None
    duration: str | None
    category: str | None
    requires_gibdd: bool
    model_config = {"from_attributes": True}


class ServiceRequestCreate(BaseModel):
    service_id: int
    car_info: str
    notes: str | None = None


class ServiceRequestOut(BaseModel):
    request_id: int
    service_id: int
    car_info: str
    notes: str | None
    status: str
    created_at: datetime
    service: ServiceOut
    model_config = {"from_attributes": True}


class ServiceRequestStatusUpdate(BaseModel):
    status: str
