from __future__ import annotations

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render


def index(request):
    return render(
        request,
        "index.html",
        {
            "app_name": "MVP Bank",
            "api_base": "/api",
            "debug": settings.DEBUG,
        },
    )


def healthz(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "mvp-bank",
            "api_docs": "/api/docs",
        }
    )
