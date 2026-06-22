from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import User, Resource, ResourceType, Booking, BookingSeries
from models import ResourceSchedule, UnavailablePeriod, BookingLimit, Notification, AuditLog
from routers import router as auth_router, resource_router, booking_router

app = FastAPI(
    title="Booking System API",
    description="Информационная система бронирования ресурсов",
    version="1.0.0"
)

# CORS для фронтенда
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(resource_router)
app.include_router(booking_router)

# Создаём таблицы при запуске
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Таблицы созданы (или уже существуют)")


@app.get("/")
def root():
    return {
        "message": "API работает! Система бронирования ресурсов.",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}