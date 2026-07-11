"""Role-based access control for the web UI."""

from collections.abc import Callable
from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from accounts.models import Department, Rol


class RolTalabMixin(LoginRequiredMixin):
    """Allow only the listed roles; others are sent back with a message."""

    ruxsat_etilgan_rollar: tuple[str, ...] = ()

    def dispatch(
        self, request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if request.user.rol not in self.ruxsat_etilgan_rollar:
            messages.error(request, "Bu sahifaga kirish huquqingiz yo'q.")
            return redirect("bosh_sahifa")
        return super().dispatch(request, *args, **kwargs)


class OfficeAdminTalabMixin(RolTalabMixin):
    ruxsat_etilgan_rollar = (Rol.OFFICE_ADMIN, Rol.SUPERADMIN)


class OqituvchiTalabMixin(RolTalabMixin):
    ruxsat_etilgan_rollar = (Rol.TEACHER,)


class KafedraMudiriTalabMixin(RolTalabMixin):
    """Resolves the head's own kafedra; it is the only tenancy source.

    Views under /kafedra/ must read scope from self.kafedra, never from
    URL parameters — that is what keeps one mudir out of another's data.
    """

    ruxsat_etilgan_rollar = (Rol.DEPARTMENT_ADMIN, Rol.SUPERADMIN)

    def dispatch(
        self, request: HttpRequest, *args: object, **kwargs: object
    ) -> HttpResponse:
        if request.user.is_authenticated:
            kafedra = _boshqarayotgan_kafedra(request)
            if request.user.rol in self.ruxsat_etilgan_rollar and kafedra is None:
                messages.error(request, "Sizga kafedra biriktirilmagan.")
                return redirect("bosh_sahifa")
            self.kafedra = kafedra
        return super().dispatch(request, *args, **kwargs)


def _boshqarayotgan_kafedra(request: HttpRequest) -> Department | None:
    profil = getattr(request.user, "oqituvchi_profil", None)
    if profil is None:
        return None
    return getattr(profil, "boshqarayotgan_kafedra", None)


def office_admin_talab(
    view: Callable[..., HttpResponse],
) -> Callable[..., HttpResponse]:
    """Function-view counterpart of OfficeAdminTalabMixin for HTMX endpoints."""

    @wraps(view)
    def wrapper(request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        if not request.user.is_authenticated:
            return redirect("kirish")
        if request.user.rol not in (Rol.OFFICE_ADMIN, Rol.SUPERADMIN):
            messages.error(request, "Bu sahifaga kirish huquqingiz yo'q.")
            return redirect("bosh_sahifa")
        return view(request, *args, **kwargs)

    return wrapper
