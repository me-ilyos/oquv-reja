"""AOH review of submitted O'quv Dastur files: list, accept, decline, open."""

from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from plans.dastur.topshirish import (
    dastur_qabul_qilish,
    dastur_rad_etish,
    joriy_topshirishlar,
)
from plans.models import DasturTopshirish, FanVariant
from web.forms.dastur import DasturRadEtishForm
from web.mixins import OfficeAdminTalabMixin, office_admin_talab


class DasturTopshirishlarView(OfficeAdminTalabMixin, ListView):
    template_name = "web/office/dasturlar/list.html"
    context_object_name = "topshirishlar"

    def get_queryset(self) -> list[DasturTopshirish]:
        qs = DasturTopshirish.objects.select_related(
            "variant__fan__reja", "variant__kafedra", "oqituvchi__foydalanuvchi"
        )
        topshirishlar = joriy_topshirishlar(qs)
        holat = self.request.GET.get("holat")
        if holat:
            topshirishlar = [t for t in topshirishlar if t.holat == holat]
        return topshirishlar

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["holat"] = self.request.GET.get("holat", "")
        return context


def _panel_kontekst(
    variant: FanVariant, *, xato: str | None = None
) -> dict[str, object]:
    urinishlar = list(
        variant.dastur_topshirishlari.select_related(
            "korib_chiqqan", "oqituvchi__foydalanuvchi"
        )
    )
    return {
        "variant": variant,
        "urinishlar": urinishlar,
        "t": urinishlar[0] if urinishlar else None,
        "xato": xato,
    }


def _javob(
    request: HttpRequest, variant: FanVariant, *, xato: str | None = None
) -> HttpResponse:
    return render(
        request,
        "web/office/dasturlar/_qator_va_panel.html",
        _panel_kontekst(variant, xato=xato),
    )


@require_POST
@office_admin_talab
def dastur_qabul(request: HttpRequest, pk: int) -> HttpResponse:
    topshirish = get_object_or_404(DasturTopshirish, pk=pk)
    dastur_qabul_qilish(topshirish, request.user)
    return _javob(request, topshirish.variant)


@require_POST
@office_admin_talab
def dastur_rad(request: HttpRequest, pk: int) -> HttpResponse:
    topshirish = get_object_or_404(DasturTopshirish, pk=pk)
    form = DasturRadEtishForm(request.POST)
    xato = None
    if form.is_valid():
        try:
            dastur_rad_etish(topshirish, request.user, form.cleaned_data["izoh"])
        except ValidationError as e:
            xato = " ".join(e.messages)
    else:
        xato = " ".join(x for xs in form.errors.values() for x in xs)
    return _javob(request, topshirish.variant, xato=xato)


@office_admin_talab
def dastur_fayl(request: HttpRequest, pk: int) -> HttpResponse:
    topshirish = get_object_or_404(DasturTopshirish, pk=pk)
    return FileResponse(topshirish.fayl.open("rb"), as_attachment=True)


@office_admin_talab
def dastur_tarixi(request: HttpRequest, variant_id: int) -> HttpResponse:
    variant = get_object_or_404(FanVariant, pk=variant_id)
    return render(
        request, "web/office/dasturlar/_tarix_panel.html", _panel_kontekst(variant)
    )
