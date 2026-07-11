"""Kafedra head's dashboard: own-department demand and delegation rows."""

from django.views.generic import TemplateView

from plans import dashboard, delegation, services
from web.mixins import KafedraMudiriTalabMixin
from web.views.office.dashboard import yilni_tanlash


class KafedraDashboardView(KafedraMudiriTalabMixin, TemplateView):
    template_name = "web/kafedra/dashboard.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
        yil = yil or dashboard.joriy_akademik_yil()
        context.update(
            {
                "yillar": yillar,
                "yil": yil,
                "kafedra": self.kafedra,
                "stat": dashboard.statlarni_hisoblash(
                    services.kafedra_taqsimoti(self.kafedra, yil)
                ),
                "fs_satrlar": delegation.kafedra_fs_satrlari(self.kafedra, yil),
            }
        )
        return context
