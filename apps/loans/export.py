from __future__ import annotations

import csv

from django.conf import settings
from django.http import StreamingHttpResponse


class _CsvBuffer:
    def write(self, value: str) -> str:
        return value


def sanitize_csv_cell(value) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def stream_loans_csv_response(queryset, *, filename: str = "loan-applications.csv") -> StreamingHttpResponse:
    buffer = _CsvBuffer()
    writer = csv.writer(buffer)
    chunk_size = int(settings.LOAN_EXPORT_CHUNK_SIZE)

    def rows():
        yield writer.writerow(["id", "amount", "term_months", "purpose", "status", "created_at", "updated_at"])
        for loan in queryset.iterator(chunk_size=chunk_size):
            yield writer.writerow(
                [
                    loan.pk,
                    loan.amount,
                    loan.term_months,
                    sanitize_csv_cell(loan.purpose),
                    loan.status,
                    loan.created_at.isoformat(),
                    loan.updated_at.isoformat(),
                ]
            )

    response = StreamingHttpResponse(rows(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["X-Content-Type-Options"] = "nosniff"
    return response
