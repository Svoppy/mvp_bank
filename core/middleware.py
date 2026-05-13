from __future__ import annotations


class DisableApiCsrfMiddleware:
    """
    The browser dashboard uses Authorization: Bearer JWT against /api/.
    CSRF protection is unnecessary for these token-based API calls and would
    block same-origin fetch requests from the built-in UI.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/api/"):
            request._dont_enforce_csrf_checks = True
        return self.get_response(request)
