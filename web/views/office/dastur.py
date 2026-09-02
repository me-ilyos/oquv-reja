"""AOH review of submitted O'quv Dastur files: list, accept, decline, open."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from plans.dastur.topshirish import dastur_qabul_qilish, dastur_rad_etish
from plans.models import DasturTopshirish
from web.forms.dastur import DasturRadEtishForm
from web.mixins import OfficeAdminTalabMixin, office_admin_talab


class DasturTopshirishlarView(OfficeAdminTalabMixin, ListView):
    template_name = "web/office/dasturlar/list.html"
    context_object_name = "topshirishlar"

    def get_queryset(self) -> object:
        queryset = DasturTopshirish.objects.select_related(
            "variant__fan__reja", "variant__kafedra", "oqituvchi__foydalanuvchi"
        )
        holat = self.request.GET.get("holat")
        if holat:
            queryset = queryset.filter(holat=holat)
        return queryset

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["holat"] = self.request.GET.get("holat", "")
        return context


@require_POST
@office_admin_talab
def dastur_qabul(request: HttpRequest, pk: int) -> HttpResponse:
    topshirish = get_object_or_404(DasturTopshirish, pk=pk)
    dastur_qabul_qilish(topshirish, request.user)
    messages.success(request, f"{topshirish.variant} dasturi qabul qilindi.")
    return redirect(reverse("office:dastur_topshirishlar"))


@require_POST
@office_admin_talab
def dastur_rad(request: HttpRequest, pk: int) -> HttpResponse:
    topshirish = get_object_or_404(DasturTopshirish, pk=pk)
    form = DasturRadEtishForm(request.POST)
    if form.is_valid():
        try:
            dastur_rad_etish(topshirish, request.user, form.cleaned_data["izoh"])
        except ValidationError as xato:
            messages.error(request, " ".join(xato.messages))
        else:
            messages.success(request, f"{topshirish.variant} dasturi rad etildi.")
    else:
        for xatolar in form.errors.values():
            for xato in xatolar:
                messages.error(request, xato)
    return redirect(reverse("office:dastur_topshirishlar"))


@office_admin_talab
def dastur_fayl(request: HttpRequest, pk: int) -> HttpResponse:
    topshirish = get_object_or_404(DasturTopshirish, pk=pk)
    return FileResponse(topshirish.fayl.open("rb"), as_attachment=True)
