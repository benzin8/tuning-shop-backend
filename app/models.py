from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Integer, String, Text, Numeric, ForeignKey, DateTime, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.role_id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    role: Mapped["Role"] = relationship("Role", back_populates="users")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    service_requests: Mapped[list["ServiceRequest"]] = relationship("ServiceRequest", back_populates="user")


class OrderStatus(Base):
    __tablename__ = "order_statuses"

    status_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="status")


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    status_id: Mapped[int] = mapped_column(ForeignKey("order_statuses.status_id"), nullable=False)
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    payment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="orders")
    status: Mapped["OrderStatus"] = relationship("OrderStatus", back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price_at_purchase: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")


class Category(Base):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="category")


class PartManufacturer(Base):
    __tablename__ = "part_manufacturers"

    manufacturer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manufacturer_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    products: Mapped[list["Product"]] = relationship("Product", back_populates="manufacturer")


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.category_id"), nullable=False)
    manufacturer_id: Mapped[int] = mapped_column(ForeignKey("part_manufacturers.manufacturer_id"), nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    category: Mapped["Category"] = relationship("Category", back_populates="products")
    manufacturer: Mapped["PartManufacturer"] = relationship("PartManufacturer", back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="product")
    compatibilities: Mapped[list["ProductCarCompatibility"]] = relationship(
        "ProductCarCompatibility", back_populates="product"
    )


class Brand(Base):
    __tablename__ = "brands"

    brand_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    car_models: Mapped[list["CarModel"]] = relationship("CarModel", back_populates="brand")


class CarModel(Base):
    __tablename__ = "car_models"

    model_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.brand_id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)

    brand: Mapped["Brand"] = relationship("Brand", back_populates="car_models")
    cars: Mapped[list["Car"]] = relationship("Car", back_populates="model")


class Car(Base):
    __tablename__ = "cars"

    car_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("car_models.model_id"), nullable=False)
    generation: Mapped[str | None] = mapped_column(String(100))
    year_start: Mapped[int | None] = mapped_column(Integer)
    year_end: Mapped[int | None] = mapped_column(Integer)

    model: Mapped["CarModel"] = relationship("CarModel", back_populates="cars")
    compatibilities: Mapped[list["ProductCarCompatibility"]] = relationship(
        "ProductCarCompatibility", back_populates="car"
    )


class ProductCarCompatibility(Base):
    __tablename__ = "product_car_compatibility"

    compatibility_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.car_id"), nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="compatibilities")
    car: Mapped["Car"] = relationship("Car", back_populates="compatibilities")


class Service(Base):
    __tablename__ = "services"

    service_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    price_from: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    duration: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(100))

    requests: Mapped[list["ServiceRequest"]] = relationship("ServiceRequest", back_populates="service")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    request_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    service_id: Mapped[int] = mapped_column(ForeignKey("services.service_id"), nullable=False)
    car_info: Mapped[str] = mapped_column(String(200), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship("User", back_populates="service_requests")
    service: Mapped["Service"] = relationship("Service", back_populates="requests")
