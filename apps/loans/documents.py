from __future__ import annotations

import hashlib
from contextlib import suppress
from pathlib import Path
from uuid import uuid4

from django.conf import settings
from ninja.errors import HttpError
from ninja.files import UploadedFile

from apps.auth_app.models import User
from apps.loans.models import CreditApplication, LoanDocument

ALLOWED_DOCUMENT_TYPES = {
    "application/pdf": {
        "extension": ".pdf",
        "magic": (b"%PDF-",),
    },
    "image/png": {
        "extension": ".png",
        "magic": (b"\x89PNG\r\n\x1a\n",),
    },
    "image/jpeg": {
        "extension": ".jpg",
        "magic": (b"\xff\xd8\xff",),
    },
}


def _clean_original_name(name: str | None) -> str:
    candidate = Path(name or "document").name.strip()
    if not candidate or any(char in candidate for char in "<>:/\\|?*\x00"):
        return "document"
    return candidate[:120]


def _safe_document_dir(loan_id: int) -> Path:
    root = Path(settings.MEDIA_ROOT).resolve()
    target = (root / "loan_documents" / str(loan_id)).resolve()
    if target != root and root not in target.parents:
        raise RuntimeError("Resolved document path escaped MEDIA_ROOT")
    target.mkdir(parents=True, exist_ok=True)
    return target


def _validate_magic(content_type: str, header: bytes) -> None:
    allowed = ALLOWED_DOCUMENT_TYPES[content_type]
    if not any(header.startswith(prefix) for prefix in allowed["magic"]):
        raise HttpError(415, "Unsupported or invalid file content")


def store_loan_document(
    *,
    loan: CreditApplication,
    uploaded_by: User,
    uploaded_file: UploadedFile,
) -> LoanDocument:
    content_type = uploaded_file.content_type or ""
    if content_type not in ALLOWED_DOCUMENT_TYPES:
        raise HttpError(415, "Unsupported file type")

    max_size = int(settings.MAX_LOAN_DOCUMENT_BYTES)
    declared_size = getattr(uploaded_file, "size", None)
    if declared_size is not None and declared_size > max_size:
        raise HttpError(413, "Uploaded file is too large")

    document_dir = _safe_document_dir(loan.pk)
    extension = ALLOWED_DOCUMENT_TYPES[content_type]["extension"]
    stored_name = f"{uuid4().hex}{extension}"
    final_path = document_dir / stored_name

    size = 0
    hasher = hashlib.sha256()
    header = b""

    try:
        with final_path.open("xb") as target:
            for chunk in uploaded_file.chunks():
                if not chunk:
                    continue
                if not header:
                    header = chunk[:16]
                    _validate_magic(content_type, header)

                size += len(chunk)
                if size > max_size:
                    raise HttpError(413, "Uploaded file is too large")

                hasher.update(chunk)
                target.write(chunk)

        if size == 0:
            raise HttpError(400, "Uploaded file is empty")
    except Exception:
        with suppress(Exception):
            final_path.unlink(missing_ok=True)
        raise

    return LoanDocument.objects.create(
        loan=loan,
        uploaded_by=uploaded_by,
        original_name=_clean_original_name(uploaded_file.name),
        stored_name=stored_name,
        content_type=content_type,
        size_bytes=size,
        sha256=hasher.hexdigest(),
    )
