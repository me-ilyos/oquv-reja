"""Login, logout and the role-based landing dispatch."""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from accounts.models import Rol
from web.forms.auth import TelefonKirishForm

ROL_SAHIFALARI = {
    Rol.SUPERADMIN: "office:dashboard",
    Rol.OFFICE_ADMIN: "office:dashboard",
    Rol.DEPARTMENT_ADMIN: "kafedra:dashboard",
    Rol.TEACHER: "men:yuklamalar",
}


class KirishView(LoginView):
    template_name = "web/auth/kirish.html"
    form_class = TelefonKirishForm
    redirect_authenticated_user = True


@login_required
def bosh_sahifa(request: HttpRequest) -> HttpResponse:
    return redirect(ROL_SAHIFALARI.get(request.user.rol, "kirish"))
