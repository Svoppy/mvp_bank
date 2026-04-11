from ninja import NinjaAPI
from apps.auth_app.api import router as auth_router
from apps.loans.api import router as loans_router
from apps.audit.api import router as audit_router

api = NinjaAPI(
    title="MVP Bank — Credit Approval API",
    version="1.0.0",
    description="Banking credit approval and monitoring system",
)

api.add_router("/auth", auth_router)
api.add_router("/loans", loans_router)
api.add_router("/audit", audit_router)

from django.urls import path
urlpatterns = [
    path("api/", api.urls),
]
