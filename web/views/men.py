"""Teacher's own workload table for the selected academic year."""

from collections import defaultdict

from django.views.generic import TemplateView

from plans import dashboard, services
from plans.models import SoatTuri, Yuklama
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
            .select_related("fan_semestr__variant__fan__reja", "guruh")
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


def _tur_jami(yuklamalar: list[Yuklama]) -> list[tuple[str, int]]:
    jami: dict[str, int] = defaultdict(int)
    for yuklama in yuklamalar:
        jami[yuklama.tur] += yuklama.soat
    return [(SoatTuri(tur).label, soat) for tur, soat in jami.items()]
