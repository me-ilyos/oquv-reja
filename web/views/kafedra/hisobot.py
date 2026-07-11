"""Printable coverage report for one kafedra's teachers."""

from django.views.generic import TemplateView

from plans import dashboard, services
from web.mixins import KafedraMudiriTalabMixin
from web.views.office.dashboard import yilni_tanlash


class HisobotView(KafedraMudiriTalabMixin, TemplateView):
    template_name = "web/kafedra/hisobot.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
        yil = yil or dashboard.joriy_akademik_yil()
        holatlar = services.yuklama_kamomadi(yil, kafedra=self.kafedra)
        jami_yuklama = sum(h.jami_soat for h in holatlar)
        jami_min = sum(h.min_soat for h in holatlar)
        context.update(
            {
                "yillar": yillar,
                "yil": yil,
                "kafedra": self.kafedra,
                "holatlar": holatlar,
                "jami_yuklama": jami_yuklama,
                "jami_min": jami_min,
            }
        )
        return context
