"""O'quv reja screens: list, Excel import, detail (semestrovka) and edit."""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, FormView, ListView, UpdateView

from accounts.models import Department
from plans import dashboard, services
from plans.importer import ImportNatija, ImportXato
from plans.models import OquvReja
from plans.uploads import fayldan_import_qilish
from web.forms.reja import RejaImportForm, RejaTahrirForm
from web.mixins import OfficeAdminTalabMixin


class RejaListView(OfficeAdminTalabMixin, ListView):
    template_name = "web/office/rejalar/list.html"
    context_object_name = "rejalar"
    queryset = OquvReja.objects.order_by("-boshlanish_yili", "yonalish_nomi")


class RejaImportView(OfficeAdminTalabMixin, FormView):
    template_name = "web/office/rejalar/yangi.html"
    form_class = RejaImportForm

    def form_valid(self, form: RejaImportForm) -> HttpResponse:
        try:
            natija = fayldan_import_qilish(
                form.cleaned_data["fayl"], form.parametrlar()
            )
        except ImportXato as xato:
            form.add_error(None, str(xato))
            return self.form_invalid(form)
        self._xabarlar(natija)
        return redirect("office:reja_detail", pk=natija.reja.pk)

    def _xabarlar(self, natija: ImportNatija) -> None:
        holat = "yaratildi" if natija.yaratildi else "yangilandi"
        messages.success(
            self.request,
            f"{natija.reja} {holat}: {natija.fan_soni} fan, "
            f"{natija.variant_soni} variant.",
        )
        for ogohlantirish in natija.ogohlantirishlar:
            messages.warning(self.request, ogohlantirish)


class RejaDetailView(OfficeAdminTalabMixin, DetailView):
    template_name = "web/office/rejalar/detail.html"
    context_object_name = "reja"
    queryset = OquvReja.objects.prefetch_related("guruhlar")

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        reja = self.object
        satrlar = dashboard.reja_semestrovkasi(reja)
        context.update(
            {
                "satrlar": satrlar,
                "majburiy_satrlar": [s for s in satrlar if s.fan.turi == "MAJBURIY"],
                "tanlov_satrlar": [s for s in satrlar if s.fan.turi == "TANLOV"],
                "semestr_raqamlari": range(1, reja.semestrlar_soni + 1),
                "stat": dashboard.statlarni_hisoblash(services.taqsimot_hisoboti(reja)),
                "kafedralar": Department.objects.order_by("nomi"),
            }
        )
        return context


class RejaTahrirView(OfficeAdminTalabMixin, UpdateView):
    template_name = "web/office/rejalar/tahrir.html"
    form_class = RejaTahrirForm
    queryset = OquvReja.objects.all()
    context_object_name = "reja"

    def form_valid(self, form: RejaTahrirForm) -> HttpResponse:
        javob = super().form_valid(form)
        services.guruhlarni_sinxronlash(self.object)
        messages.success(self.request, "Reja saqlandi, guruhlar yangilandi.")
        return javob

    def get_success_url(self) -> str:
        return reverse("office:reja_detail", kwargs={"pk": self.object.pk})
