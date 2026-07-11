"""Office-wide teacher administration and coverage list."""

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.views.generic import FormView, TemplateView

from accounts.models import Department, OqituvchiProfil
from plans import dashboard, services
from web.forms.oqituvchi import OqituvchiTahrirForm, OqituvchiYaratishForm
from web.mixins import OfficeAdminTalabMixin, office_admin_talab
from web.views.office.dashboard import yilni_tanlash


class OqituvchiListView(OfficeAdminTalabMixin, TemplateView):
    template_name = "web/office/oqituvchilar/list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
        yil = yil or dashboard.joriy_akademik_yil()
        kafedra = self._tanlangan_kafedra()
        context.update(
            {
                "yillar": yillar,
                "yil": yil,
                "kafedralar": Department.objects.order_by("nomi"),
                "kafedra": kafedra,
                "holatlar": services.yuklama_kamomadi(yil, kafedra=kafedra),
            }
        )
        return context

    def _tanlangan_kafedra(self) -> Department | None:
        kafedra_id = self.request.GET.get("kafedra")
        if not kafedra_id or not kafedra_id.isdigit():
            return None
        return Department.objects.filter(pk=kafedra_id).first()


class OqituvchiYangiView(OfficeAdminTalabMixin, FormView):
    template_name = "web/office/oqituvchilar/form.html"
    form_class = OqituvchiYaratishForm

    def form_valid(self, form: OqituvchiYaratishForm) -> HttpResponse:
        profil = form.saqlash()
        messages.success(self.request, f"{profil} yaratildi.")
        return redirect("office:oqituvchi_list")


class OqituvchiTahrirView(OfficeAdminTalabMixin, FormView):
    template_name = "web/office/oqituvchilar/form.html"
    form_class = OqituvchiTahrirForm

    def get_form_kwargs(self) -> dict[str, object]:
        kwargs = super().get_form_kwargs()
        kwargs["profil"] = get_object_or_404(
            OqituvchiProfil.objects.select_related("foydalanuvchi"),
            pk=self.kwargs["pk"],
        )
        return kwargs

    def form_valid(self, form: OqituvchiTahrirForm) -> HttpResponse:
        form.saqlash()
        messages.success(self.request, f"{form.profil} saqlandi.")
        return redirect("office:oqituvchi_list")


@require_POST
@office_admin_talab
def oqituvchi_ochirish(request: HttpRequest, pk: int) -> HttpResponse:
    profil = get_object_or_404(
        OqituvchiProfil.objects.select_related("foydalanuvchi"), pk=pk
    )
    if profil.yuklamalar.exists():
        foydalanuvchi = profil.foydalanuvchi
        foydalanuvchi.is_active = False
        foydalanuvchi.save(update_fields=["is_active"])
        messages.warning(
            request,
            f"{profil} yuklamalarga ega — hisob o'chirilmasdan faolsizlantirildi.",
        )
    else:
        profil.foydalanuvchi.delete()
        messages.success(request, f"{profil} o'chirildi.")
    return redirect("office:oqituvchi_list")
