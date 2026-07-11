"""Department administration: CRUD, coverage overview and mudir assignment."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, TemplateView, UpdateView

from accounts.models import Department, OqituvchiProfil
from accounts.services import mudir_tayinlash
from plans import dashboard
from web.forms.kafedra import KafedraForm
from web.mixins import OfficeAdminTalabMixin, office_admin_talab
from web.views.office.dashboard import yilni_tanlash


class KafedraListView(OfficeAdminTalabMixin, TemplateView):
    template_name = "web/office/kafedralar/list.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
        yil = yil or dashboard.joriy_akademik_yil()
        context.update(
            {
                "yillar": yillar,
                "yil": yil,
                "qamrovlar": dashboard.kafedra_qamrovi(yil),
            }
        )
        return context


class KafedraYangiView(OfficeAdminTalabMixin, CreateView):
    template_name = "web/office/kafedralar/form.html"
    form_class = KafedraForm
    success_url = reverse_lazy("office:kafedra_list")

    def form_valid(self, form: KafedraForm) -> HttpResponse:
        messages.success(self.request, "Kafedra yaratildi.")
        return super().form_valid(form)


class KafedraTahrirView(OfficeAdminTalabMixin, UpdateView):
    template_name = "web/office/kafedralar/form.html"
    form_class = KafedraForm
    queryset = Department.objects.all()
    success_url = reverse_lazy("office:kafedra_list")

    def form_valid(self, form: KafedraForm) -> HttpResponse:
        messages.success(self.request, "Kafedra saqlandi.")
        return super().form_valid(form)


@require_POST
@office_admin_talab
def kafedra_ochirish(request: HttpRequest, pk: int) -> HttpResponse:
    kafedra = get_object_or_404(Department, pk=pk)
    try:
        kafedra.delete()
        messages.success(request, f"{kafedra.nomi} o'chirildi.")
    except ProtectedError:
        messages.error(
            request,
            f"{kafedra.nomi} kafedrasida o'qituvchilar yoki fanlar bor — "
            "avval ularni boshqa kafedraga ko'chiring.",
        )
    return redirect("office:kafedra_list")


@require_POST
@office_admin_talab
def kafedra_mudir(request: HttpRequest, pk: int) -> HttpResponse:
    kafedra = get_object_or_404(Department, pk=pk)
    profil_id = request.POST.get("profil") or None
    profil = get_object_or_404(OqituvchiProfil, pk=profil_id) if profil_id else None
    try:
        mudir_tayinlash(kafedra, profil)
        if profil is None:
            messages.success(request, f"{kafedra.nomi}: mudir bekor qilindi.")
        else:
            messages.success(
                request, f"{kafedra.nomi}: {profil} mudir etib tayinlandi."
            )
    except ValidationError as xato:
        messages.error(request, " ".join(xato.messages))
    return redirect("office:kafedra_list")
