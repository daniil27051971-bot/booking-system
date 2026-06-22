from .auth_router import router
from .resource_router import router as resource_router
from .booking_router import router as booking_router

__all__ = [
    'router',           # auth_router
    'resource_router',
    'booking_router',
]