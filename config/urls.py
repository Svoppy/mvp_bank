from ninja import NinjaAPI
from ninja.openapi.docs import Swagger
from apps.auth_app.api import router as auth_router
from apps.loans.api import router as loans_router
from apps.audit.api import router as audit_router

api = NinjaAPI(
    title="MVP Bank - Credit Approval API",
    version="1.0.0",
    description="Banking credit approval and monitoring system",
    docs=Swagger(
        settings={
            "persistAuthorization": True,
            "displayRequestDuration": True,
            "docExpansion": "list",
            "tryItOutEnabled": True,
        }
    ),
    servers=[
        {
            "url": "/",
            "description": "Current server",
        }
    ],
    openapi_extra={
        "tags": [
            {
                "name": "Auth",
                "description": "Client registration, login, token rotation, logout, and current profile.",
            },
            {
                "name": "Loans",
                "description": "Credit application submission, listing, object access control, and manager decisions.",
            },
            {
                "name": "Audit",
                "description": "Administrative audit trail for critical security and business events.",
            },
        ]
    },
)

api.add_router("/auth", auth_router)
api.add_router("/loans", loans_router)
api.add_router("/audit", audit_router)

from django.urls import path
urlpatterns = [
    path("api/", api.urls),
]
