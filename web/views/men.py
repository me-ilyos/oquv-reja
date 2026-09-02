"""Teacher's own workload table for the selected academic year."""

from collections import defaultdict

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from plans import dashboard, services
from plans.dastur.service import dastur_egasimi, dastur_render
from plans.dastur.topshirish import dastur_topshirish
from plans.models import FanVariant, SoatTuri, Yuklama
from web.forms.dastur import DasturTopshirishForm
from web.mixins import OqituvchiTalabMixin
from web.views.office.dashboard import yilni_tanlash


class MenYuklamalarimView(OqituvchiTalabMixin, TemplateView):
    template_name = "web/men/yuklamalar.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        profil = getattr(self.request.user, "oqituvchi_profil", None)
        context["profil"] = profil
        if profil is None:
            return context
        yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
        yil = yil or dashboard.joriy_akademik_yil()
        yuklamalar = list(
            Yuklama.objects.filter(oqituvchi=profil)
            .akademik_yilda(yil)
            .select_related(
                "fan_semestr__variant__fan__reja",
                "fan_semestr__variant__dastur_topshirish",
                "guruh",
            )
            .order_by("fan_semestr__variant__nomi", "fan_semestr__semestr", "tur")
        )
        context.update(
            {
                "yillar": yillar,
                "yil": yil,
                "yuklamalar": yuklamalar,
                "tur_jami": _tur_jami(yuklamalar),
                "jami_soat": services.oqituvchi_yillik_yuklamasi(profil, yil),
            }
        )
        return context


class MenOquvDasturView(OqituvchiTalabMixin, View):
    def get(self, request: HttpRequest, variant_id: int) -> HttpResponse:
        variant = get_object_or_404(FanVariant, pk=variant_id)
        profil = getattr(request.user, "oqituvchi_profil", None)
        if profil is None or not dastur_egasimi(variant, profil):
            return HttpResponseForbidden(
                "Bu fan dasturini faqat ma'ruza egasi yaratishi mumkin."
            )
        return FileResponse(
            dastur_render(variant),
            as_attachment=True,
            filename=f"{variant.kodi or variant.nomi}_oquv_dastur.docx",
        )


class MenDasturTopshirishView(OqituvchiTalabMixin, View):
    def post(self, request: HttpRequest, variant_id: int) -> HttpResponse:
        variant = get_object_or_404(FanVariant, pk=variant_id)
        profil = getattr(request.user, "oqituvchi_profil", None)
        if profil is None or not dastur_egasimi(variant, profil):
            return HttpResponseForbidden(
                "Bu fan dasturini faqat ma'ruza egasi topshirishi mumkin."
            )
        form = DasturTopshirishForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                dastur_topshirish(variant, profil, form.cleaned_data["fayl"])
            except ValidationError as xato:
                messages.error(request, " ".join(xato.messages))
            else:
                messages.success(request, "Dastur topshirildi.")
        else:
            for xatolar in form.errors.values():
                for xato in xatolar:
                    messages.error(request, xato)
        return redirect(reverse("men:yuklamalar"))


def _tur_jami(yuklamalar: list[Yuklama]) -> list[tuple[str, int]]:
    jami: dict[str, int] = defaultdict(int)
    for yuklama in yuklamalar:
        jami[yuklama.tur] += yuklama.soat
    return [(SoatTuri(tur).label, soat) for tur, soat in jami.items()]
