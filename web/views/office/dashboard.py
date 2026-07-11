"""Office dashboard: year-scoped KPIs, course list and inline allocation."""

from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from accounts.models import Department
from plans import dashboard, services
from plans.models import Fan, FanVariant
from web.mixins import OfficeAdminTalabMixin, office_admin_talab


def yilni_tanlash(sorov_yil: str | None) -> tuple[list[int], int | None]:
    """Validate the requested year against the offered (non-past) list."""
    yillar = dashboard.tanlanadigan_yillar()
    if not yillar:
        return [], None
    if sorov_yil and sorov_yil.isdigit() and int(sorov_yil) in yillar:
        return yillar, int(sorov_yil)
    joriy = dashboard.joriy_akademik_yil()
    return yillar, joriy if joriy in yillar else yillar[0]


def _dashboard_konteksti(yil: int) -> dict[str, object]:
    return {
        "yil": yil,
        "stat": dashboard.statlarni_hisoblash(services.ofis_taqsimoti(yil)),
        "jami_talabalar": dashboard.jami_talabalar(yil),
        "fan_satrlari": dashboard.ofis_fan_satrlari(yil),
        "kafedralar": Department.objects.order_by("nomi"),
    }


class DashboardView(OfficeAdminTalabMixin, TemplateView):
    template_name = "web/office/dashboard.html"

    def get_template_names(self) -> list[str]:
        if self.request.headers.get("HX-Request"):
            return ["web/office/_dashboard_kontent.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
        context["yillar"] = yillar
        if yil is not None:
            context.update(_dashboard_konteksti(yil))
        return context


@require_POST
@office_admin_talab
def variant_tanlash(request: HttpRequest, pk: int) -> HttpResponse:
    fan = get_object_or_404(Fan, pk=pk)
    variant = get_object_or_404(FanVariant, pk=request.POST.get("variant"), fan=fan)
    xato = None
    try:
        services.variantni_tanlash(fan, variant)
    except ValidationError as e:
        xato = " ".join(e.messages)
    return _qator_javobi(request, fan, xato)


@require_POST
@office_admin_talab
def kafedra_biriktirish(request: HttpRequest, pk: int) -> HttpResponse:
    variant = get_object_or_404(FanVariant, pk=pk)
    kafedra_id = request.POST.get("kafedra") or None
    kafedra = get_object_or_404(Department, pk=kafedra_id) if kafedra_id else None
    xato = None
    try:
        services.kafedraga_biriktirish(variant, kafedra)
    except ValidationError as e:
        xato = " ".join(e.messages)
    return _qator_javobi(request, variant.fan, xato)


def _qator_javobi(request: HttpRequest, fan: Fan, xato: str | None) -> HttpResponse:
    """Re-render the mutated course row plus an out-of-band stats block."""
    _, yil = yilni_tanlash(request.POST.get("yil"))
    kontekst = _dashboard_konteksti(yil) if yil is not None else {}
    satr = next(
        (s for s in kontekst.get("fan_satrlari", []) if s.fan.pk == fan.pk), None
    )
    kontekst.update({"satr": satr, "xato": xato})
    return render(request, "web/office/_qator_va_statlar.html", kontekst)
