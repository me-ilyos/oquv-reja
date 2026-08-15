"""Template context shared by every page."""

from django.conf import settings
from django.http import HttpRequest


def debug_rejim(request: HttpRequest) -> dict[str, bool]:
    """Expose DEBUG so the navbar can hide the dev role switcher in production."""
    return {"debug_rejim": settings.DEBUG}
