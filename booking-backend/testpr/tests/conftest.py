import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from database import Base, get_db
from main import app
from models import User, Resource, ResourceType, Booking, BookingLimit, ResourceSchedule
from auth import hash_password

# Используем ТУ ЖЕ БАЗУ, что и в приложении
from database import engine

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Создаём таблицы перед каждым тестом и очищаем после."""
    Base.metadata.create_all(bind=engine)
    yield
    # Очищаем все таблицы после теста
    for table in reversed(Base.metadata.sorted_tables):
        engine.execute(table.delete())
    # Или просто:
    # Base.metadata.drop_all(bind=engine)
    # Base.metadata.create_all(bind=engine)


@pytest.fixture
def test_user():
    """Создаём тестового пользователя."""
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpass123"),
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


@pytest.fixture
def test_admin():
    """Создаём тестового администратора."""
    db = TestingSessionLocal()
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("adminpass123"),
        role="admin",
        is_active=True
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    db.close()
    return admin


@pytest.fixture
def test_resource():
    """Создаём тестовый ресурс."""
    db = TestingSessionLocal()
    
    resource_type = ResourceType(name="Переговорная")
    db.add(resource_type)
    db.commit()
    db.refresh(resource_type)
    
    resource = Resource(
        type_id=resource_type.id,
        name="Тестовая переговорная",
        capacity=10,
        location="3 этаж, комната 301",
        description="Тестовый ресурс",
        is_archived=False
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    db.close()
    return resource


@pytest.fixture
def test_resource_small():
    """Создаём тестовый ресурс с малой вместимостью."""
    db = TestingSessionLocal()
    
    resource_type = ResourceType(name="Рабочее место")
    db.add(resource_type)
    db.commit()
    db.refresh(resource_type)
    
    resource = Resource(
        type_id=resource_type.id,
        name="Малое рабочее место",
        capacity=2,
        location="2 этаж",
        is_archived=False
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    db.close()
    return resource


@pytest.fixture
def test_limits():
    """Создаём тестовые лимиты."""
    db = TestingSessionLocal()
    limits = BookingLimit(
        min_duration_minutes=30,
        max_duration_minutes=240,
        max_active_bookings=3,
        booking_horizon_days=30,
        buffer_minutes=15
    )
    db.add(limits)
    db.commit()
    db.refresh(limits)
    db.close()
    return limits


@pytest.fixture
def test_schedule(test_resource):
    """Создаём расписание для тестового ресурса."""
    db = TestingSessionLocal()
    
    schedule = ResourceSchedule(
        resource_id=test_resource.id,
        weekday=1,  # Понедельник
        start_time=datetime.strptime("09:00", "%H:%M").time(),
        end_time=datetime.strptime("18:00", "%H:%M").time()
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    db.close()
    return schedule


@pytest.fixture
def auth_token(test_user):
    """Получаем JWT токен для тестового пользователя."""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(test_admin):
    """Получаем JWT токен для администратора."""
    response = client.post(
        "/auth/login",
        data={"username": "admin", "password": "adminpass123"}
    )
    return response.json()["access_token"]


@pytest.fixture
def test_booking(test_user, test_resource):
    """Создаём тестовую бронь."""
    db = TestingSessionLocal()
    
    start = datetime.utcnow() + timedelta(days=1, hours=10)
    end = start + timedelta(hours=1)
    
    booking = Booking(
        user_id=test_user.id,
        resource_id=test_resource.id,
        start_datetime=start,
        end_datetime=end,
        purpose="Тестовая встреча",
        seats=1,
        status="confirmed"
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    db.close()
    return booking