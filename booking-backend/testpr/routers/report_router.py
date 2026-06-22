from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from auth import get_db, get_current_admin_user
from models.user import User
from models.resource import Resource
from models.booking import Booking

router = APIRouter(prefix="/reports", tags=["Отчёты"])


@router.get("/utilization")
def get_utilization_report(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Отчёт о загрузке ресурсов за период (FR-22).
    Доступен только администратору.
    """
    if start_date >= end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Дата начала должна быть раньше даты окончания"
        )
    
    # Получаем все активные ресурсы
    resources = db.query(Resource).filter(Resource.is_archived == False).all()
    
    total_hours = (end_date - start_date).total_seconds() / 3600
    
    report = []
    
    for resource in resources:
        # Получаем все брони для этого ресурса за период
        bookings = db.query(Booking).filter(
            Booking.resource_id == resource.id,
            Booking.status == "confirmed",
            Booking.start_datetime >= start_date,
            Booking.end_datetime <= end_date
        ).all()
        
        # Считаем занятые часы
        booked_hours = sum(
            (b.end_datetime - b.start_datetime).total_seconds() / 3600
            for b in bookings
        )
        
        # Процент загрузки
        utilization = (booked_hours / total_hours * 100) if total_hours > 0 else 0
        
        report.append({
            "resource_id": resource.id,
            "resource_name": resource.name,
            "resource_type": resource.type_id,
            "capacity": resource.capacity,
            "total_hours": round(total_hours, 2),
            "booked_hours": round(booked_hours, 2),
            "utilization_percentage": round(utilization, 2),
            "bookings_count": len(bookings)
        })
    
    # Сортируем по загрузке (убывание)
    report.sort(key=lambda x: x["utilization_percentage"], reverse=True)
    
    return {
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "total_resources": len(resources),
        "report": report
    }