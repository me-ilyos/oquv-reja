"""HTMX endpoints creating and removing Yuklama rows for one kafedra.

Every endpoint resolves objects THROUGH self.kafedra (from the mixin), so a
mudir can only ever touch fan-semestrs delegated to, and teachers employed
by, their own department.
"""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from accounts.models import OqituvchiProfil
from plans import dashboard, delegation, services
from plans.models import FanSemestr, Yuklama
from web.forms.yuklama import (
    GuruhYuklamaForm,
    KursIshiYuklamaForm,
    MaruzaYuklamaForm,
    YuklamaAsosForm,
)
from web.mixins import KafedraMudiriTalabMixin

FORMALAR: dict[str, type[YuklamaAsosForm]] = {
    "maruza": MaruzaYuklamaForm,
    "guruh": GuruhYuklamaForm,
    "kurs_ishi": KursIshiYuklamaForm,
}


class PanelAsosView(KafedraMudiriTalabMixin, View):
    """Shared helpers: kafedra-scoped lookups and the panel response."""

    def fan_semestr(self, pk: int) -> FanSemestr:
        return get_object_or_404(
            FanSemestr.objects.select_related("variant__fan__reja"),
            pk=pk,
            variant__kafedra=self.kafedra,
        )

    def panel_javobi(
        self,
        request: HttpRequest,
        fs: FanSemestr,
        *,
        xato: str | None = None,
        oob: bool = False,
    ) -> HttpResponse:
        shablon = (
            "web/kafedra/_panel_va_qator.html" if oob else "web/kafedra/_panel.html"
        )
        return render(
            request,
            shablon,
            {
                "fs": fs,
                "holatlar": delegation.fan_semestr_holati(fs),
                "satr": delegation.fs_satri(fs),
                "oqituvchilar": OqituvchiProfil.objects.filter(
                    kafedra=self.kafedra
                ).select_related("foydalanuvchi"),
                "stat": dashboard.statlarni_hisoblash(
                    services.kafedra_taqsimoti(self.kafedra, fs.akademik_yil)
                ),
                "xato": xato,
            },
        )


class TaqsimotPanelView(PanelAsosView):
    def get(self, request: HttpRequest, pk: int) -> HttpResponse:
        return self.panel_javobi(request, self.fan_semestr(pk))


class YuklamaYaratishView(PanelAsosView):
    """POST /fan-semestr/<pk>/<shakl>/ — one endpoint per Yuklama shape."""

    shakl = ""

    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        fs = self.fan_semestr(pk)
        form = FORMALAR[self.shakl](fs, self.kafedra, request.POST)
        if form.is_valid():
            form.save()
            return self.panel_javobi(request, fs, oob=True)
        return self.panel_javobi(request, fs, xato=_xato_matni(form), oob=True)


def _xato_matni(form: YuklamaAsosForm) -> str:
    qismlar = []
    for maydon, xatolar in form.errors.items():
        nomi = "" if maydon == "__all__" else f"{maydon}: "
        qismlar.append(f"{nomi}{' '.join(xatolar)}")
    return " ".join(qismlar)


class YuklamaOchirishView(PanelAsosView):
    def post(self, request: HttpRequest, pk: int) -> HttpResponse:
        yuklama = get_object_or_404(
            Yuklama.objects.select_related("fan_semestr__variant__fan__reja"),
            pk=pk,
            fan_semestr__variant__kafedra=self.kafedra,
        )
        fs = yuklama.fan_semestr
        yuklama.delete()
        return self.panel_javobi(request, fs, oob=True)

    def delete(self, request: HttpRequest, pk: int) -> HttpResponse:
        return self.post(request, pk)
