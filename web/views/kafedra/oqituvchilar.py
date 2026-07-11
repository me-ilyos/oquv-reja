"""Mudir's own-department teacher list and CRUD (kafedra locked)."""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView, TemplateView

from accounts.models import OqituvchiProfil
from plans import dashboard, services
from web.forms.oqituvchi import (
    KafedraOqituvchiTahrirForm,
    KafedraOqituvchiYaratishForm,
)
from web.mixins import KafedraMudiriTalabMixin
from web.views.office.dashboard import yilni_tanlash


class KafedraOqituvchiListView(KafedraMudiriTalabMixin, TemplateView):
    template_name = "web/kafedra/oqituvchilar/list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
        yil = yil or dashboard.joriy_akademik_yil()
        context.update(
            {
                "yillar": yillar,
                "yil": yil,
                "kafedra": self.kafedra,
                "holatlar": services.yuklama_kamomadi(yil, kafedra=self.kafedra),
            }
        )
        return context


class KafedraOqituvchiYangiView(KafedraMudiriTalabMixin, FormView):
    template_name = "web/kafedra/oqituvchilar/form.html"
    form_class = KafedraOqituvchiYaratishForm

    def get_form_kwargs(self) -> dict[str, object]:
        kwargs = super().get_form_kwargs()
        kwargs["kafedra"] = self.kafedra
        return kwargs

    def form_valid(self, form: KafedraOqituvchiYaratishForm) -> HttpResponse:
        profil = form.saqlash()
        messages.success(self.request, f"{profil} yaratildi.")
        return redirect("kafedra:oqituvchi_list")


class KafedraOqituvchiTahrirView(KafedraMudiriTalabMixin, FormView):
    template_name = "web/kafedra/oqituvchilar/form.html"
    form_class = KafedraOqituvchiTahrirForm

    def get_form_kwargs(self) -> dict[str, object]:
        kwargs = super().get_form_kwargs()
        kwargs["profil"] = get_object_or_404(
            OqituvchiProfil.objects.select_related("foydalanuvchi"),
            pk=self.kwargs["pk"],
            kafedra=self.kafedra,
        )
        return kwargs

    def form_valid(self, form: KafedraOqituvchiTahrirForm) -> HttpResponse:
        form.saqlash()
        messages.success(self.request, f"{form.profil} saqlandi.")
        return redirect("kafedra:oqituvchi_list")
