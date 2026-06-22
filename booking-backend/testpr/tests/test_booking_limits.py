import pytest
from datetime import datetime, timedelta
from tests.conftest import client, auth_token, test_resource, test_limits


def test_booking_min_duration(auth_token, test_resource, test_limits):
    """Тест минимальной длительности брони (FR-6)."""
    # Пытаемся забронировать на 15 минут (меньше минимума 30 минут)
    start = (datetime.utcnow() + timedelta(days=1, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=10, minutes=15)).isoformat()
    
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Короткая встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "минимальная" in response.json()["detail"].lower() or "30" in response.json()["detail"]


def test_booking_max_duration(auth_token, test_resource, test_limits):
    """Тест максимальной длительности брони (FR-6)."""
    # Пытаемся забронировать на 5 часов (больше максимума 4 часа)
    start = (datetime.utcnow() + timedelta(days=1, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=1, hours=15)).isoformat()
    
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Длинная встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "максимальная" in response.json()["detail"].lower() or "4" in response.json()["detail"]


def test_booking_horizon(auth_token, test_resource, test_limits):
    """Тест горизонта бронирования (FR-8)."""
    # Пытаемся забронировать на 31 день вперёд (горизонт 30 дней)
    start = (datetime.utcnow() + timedelta(days=31, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=31, hours=11)).isoformat()
    
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Дальняя встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "дальше" in response.json()["detail"].lower() or "30" in response.json()["detail"]


def test_booking_max_active(auth_token, test_resource, test_limits):
    """Тест лимита активных броней (FR-7)."""
    # Создаём 3 брони (максимум)
    for i in range(3):
        start = (datetime.utcnow() + timedelta(days=i+1, hours=10)).isoformat()
        end = (datetime.utcnow() + timedelta(days=i+1, hours=11)).isoformat()
        response = client.post(
            "/bookings/",
            json={
                "resource_id": test_resource.id,
                "start_datetime": start,
                "end_datetime": end,
                "purpose": f"Встреча {i+1}",
                "seats": 1
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 201
    
    # Пытаемся создать 4-ю бронь
    start = (datetime.utcnow() + timedelta(days=4, hours=10)).isoformat()
    end = (datetime.utcnow() + timedelta(days=4, hours=11)).isoformat()
    response = client.post(
        "/bookings/",
        json={
            "resource_id": test_resource.id,
            "start_datetime": start,
            "end_datetime": end,
            "purpose": "Лишняя встреча",
            "seats": 1
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 400
    assert "лимит" in response.json()["detail"].lower()