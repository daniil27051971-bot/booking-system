from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, time
from auth import get_db, get_current_user, get_current_admin_user
from models.user import User
from models.resource import Resource, ResourceType
from models.schedule import ResourceSchedule
from models.unavailable import UnavailablePeriod
from models.limits import BookingLimit
from schemas.resource import (
    ResourceTypeCreate, ResourceTypeResponse,
    ResourceCreate, ResourceUpdate, ResourceResponse,
    ResourceScheduleCreate, ResourceScheduleResponse,
    UnavailablePeriodCreate, UnavailablePeriodResponse,
    BookingLimitCreate, BookingLimitResponse
)

router = APIRouter(prefix="/resources", tags=["Ресурсы"])


# ========== ТИПЫ РЕСУРСОВ (FR-2) ==========

@router.get("/types", response_model=List[ResourceTypeResponse])
def get_resource_types(db: Session = Depends(get_db)):
    """Получить все типы ресурсов."""
    return db.query(ResourceType).all()


@router.post("/types", response_model=ResourceTypeResponse, status_code=status.HTTP_201_CREATED)
def create_resource_type(
    type_data: ResourceTypeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать тип ресурса (только админ)."""
    existing = db.query(ResourceType).filter(ResourceType.name == type_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Тип ресурса '{type_data.name}' уже существует"
        )
    
    new_type = ResourceType(name=type_data.name)
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    return new_type


# ========== РЕСУРСЫ (FR-1) ==========

@router.get("/", response_model=List[ResourceResponse])
def get_resources(
    skip: int = 0,
    limit: int = 100,
    type_id: Optional[int] = None,
    min_capacity: Optional[int] = None,
    search: Optional[str] = None,  # Поиск по названию
    db: Session = Depends(get_db)
):
    """Получить список активных ресурсов с фильтрацией (FR-18)."""
    query = db.query(Resource).filter(Resource.is_archived == False)
    
    if type_id is not None:
        query = query.filter(Resource.type_id == type_id)
    
    if min_capacity is not None:
        query = query.filter(Resource.capacity >= min_capacity)
    
    if search:
        query = query.filter(Resource.name.ilike(f"%{search}%"))
    
    resources = query.offset(skip).limit(limit).all()
    return resources


@router.post("/", response_model=ResourceResponse, status_code=status.HTTP_201_CREATED)
def create_resource(
    resource_data: ResourceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Создать ресурс (только админ)."""
    # Проверяем, что тип ресурса существует
    resource_type = db.query(ResourceType).filter(ResourceType.id == resource_data.type_id).first()
    if not resource_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Указанный тип ресурса не существует"
        )
    
    new_resource = Resource(**resource_data.model_dump())
    db.add(new_resource)
    db.commit()
    db.refresh(new_resource)
    return new_resource


@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    """Получить ресурс по ID."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс не найден"
        )
    
    return resource


@router.put("/{resource_id}", response_model=ResourceResponse)
def update_resource(
    resource_id: int,
    resource_data: ResourceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Редактировать ресурс (только админ)."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс не найден"
        )
    
    update_data = resource_data.model_dump(exclude_unset=True)
    
    # Если меняем тип — проверяем его существование
    if "type_id" in update_data:
        resource_type = db.query(ResourceType).filter(ResourceType.id == update_data["type_id"]).first()
        if not resource_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Указанный тип ресурса не существует"
            )
    
    for key, value in update_data.items():
        setattr(resource, key, value)
    
    db.commit()
    db.refresh(resource)
    return resource


@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Архивировать ресурс (только админ, FR-5)."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс не найден"
        )
    
    resource.is_archived = True
    db.commit()
    
    return {"message": "Ресурс архивирован", "resource_id": resource.id}


# ========== РАСПИСАНИЕ (FR-3) ==========

@router.get("/{resource_id}/schedule", response_model=List[ResourceScheduleResponse])
def get_resource_schedule(resource_id: int, db: Session = Depends(get_db)):
    """Получить расписание ресурса."""
    schedule = db.query(ResourceSchedule).filter(
        ResourceSchedule.resource_id == resource_id
    ).all()
    return schedule


@router.post("/{resource_id}/schedule", response_model=ResourceScheduleResponse)
def add_resource_schedule(
    resource_id: int,
    schedule_data: ResourceScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Добавить расписание для ресурса (только админ)."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс не найден"
        )
    
    # Проверяем, нет ли уже расписания на этот день
    existing = db.query(ResourceSchedule).filter(
        ResourceSchedule.resource_id == resource_id,
        ResourceSchedule.weekday == schedule_data.weekday
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Расписание на день {schedule_data.weekday} уже существует"
        )
    
    new_schedule = ResourceSchedule(
        resource_id=resource_id,
        **schedule_data.model_dump()
    )
    db.add(new_schedule)
    db.commit()
    db.refresh(new_schedule)
    return new_schedule


@router.delete("/{resource_id}/schedule/{schedule_id}")
def delete_resource_schedule(
    resource_id: int,
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить расписание (только админ)."""
    schedule = db.query(ResourceSchedule).filter(
        ResourceSchedule.id == schedule_id,
        ResourceSchedule.resource_id == resource_id
    ).first()
    
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Расписание не найдено"
        )
    
    db.delete(schedule)
    db.commit()
    return {"message": "Расписание удалено"}


# ========== ПЕРИОДЫ НЕДОСТУПНОСТИ (FR-4) ==========

@router.get("/{resource_id}/unavailable", response_model=List[UnavailablePeriodResponse])
def get_unavailable_periods(resource_id: int, db: Session = Depends(get_db)):
    """Получить периоды недоступности ресурса."""
    periods = db.query(UnavailablePeriod).filter(
        UnavailablePeriod.resource_id == resource_id,
        UnavailablePeriod.end_datetime >= datetime.utcnow()
    ).all()
    return periods


@router.post("/{resource_id}/unavailable", response_model=UnavailablePeriodResponse)
def add_unavailable_period(
    resource_id: int,
    period_data: UnavailablePeriodCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Добавить период недоступности (только админ)."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ресурс не найден"
        )
    
    new_period = UnavailablePeriod(
        resource_id=resource_id,
        **period_data.model_dump()
    )
    db.add(new_period)
    db.commit()
    db.refresh(new_period)
    return new_period


@router.delete("/{resource_id}/unavailable/{period_id}")
def delete_unavailable_period(
    resource_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Удалить период недоступности (только админ)."""
    period = db.query(UnavailablePeriod).filter(
        UnavailablePeriod.id == period_id,
        UnavailablePeriod.resource_id == resource_id
    ).first()
    
    if not period:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Период недоступности не найден"
        )
    
    db.delete(period)
    db.commit()
    return {"message": "Период недоступности удален"}


# ========== ЛИМИТЫ (FR-6, FR-7, FR-8, FR-23) ==========

@router.get("/limits", response_model=BookingLimitResponse)
def get_booking_limits(db: Session = Depends(get_db)):
    """Получить текущие лимиты бронирования."""
    limits = db.query(BookingLimit).first()
    if not limits:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лимиты не настроены"
        )
    return limits


@router.put("/limits", response_model=BookingLimitResponse)
def update_booking_limits(
    limits_data: BookingLimitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Обновить лимиты бронирования (только админ)."""
    limits = db.query(BookingLimit).first()
    
    if not limits:
        # Создаем, если нет
        limits = BookingLimit(**limits_data.model_dump())
        db.add(limits)
    else:
        for key, value in limits_data.model_dump().items():
            setattr(limits, key, value)
    
    db.commit()
    db.refresh(limits)
    return limits