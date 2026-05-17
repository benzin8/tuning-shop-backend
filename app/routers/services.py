from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dependencies import get_db, get_current_user, require_admin
from app.models import Service, ServiceRequest
from app.schemas import ServiceOut, ServiceRequestCreate, ServiceRequestOut, ServiceRequestStatusUpdate

router = APIRouter(prefix="/services", tags=["services"])


@router.get("/", response_model=list[ServiceOut])
async def get_services(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Service).order_by(Service.service_id))
    return result.scalars().all()


@router.get("/requests/my", response_model=list[ServiceRequestOut])
async def get_my_requests(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceRequest)
        .options(selectinload(ServiceRequest.service))
        .where(ServiceRequest.user_id == current_user.user_id)
        .order_by(ServiceRequest.created_at.desc())
    )
    return result.scalars().all()


@router.get("/requests/", response_model=list[ServiceRequestOut])
async def get_all_requests(
    _=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ServiceRequest)
        .options(selectinload(ServiceRequest.service))
        .order_by(ServiceRequest.created_at.desc())
    )
    return result.scalars().all()


@router.post("/requests/", response_model=ServiceRequestOut, status_code=201)
async def create_request(
    body: ServiceRequestCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = await db.get(Service, body.service_id)
    if not service:
        raise HTTPException(404, "Service not found")
    req = ServiceRequest(
        user_id=current_user.user_id,
        service_id=body.service_id,
        car_info=body.car_info,
        notes=body.notes,
        status="new",
    )
    db.add(req)
    await db.commit()
    await db.refresh(req, ["service", "created_at"])
    return req


@router.patch("/requests/{request_id}", response_model=ServiceRequestOut)
async def update_request_status(
    request_id: int,
    body: ServiceRequestStatusUpdate,
    _=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    req = await db.get(ServiceRequest, request_id)
    if not req:
        raise HTTPException(404, "Request not found")
    req.status = body.status
    await db.commit()
    await db.refresh(req, ["service", "created_at"])
    return req
