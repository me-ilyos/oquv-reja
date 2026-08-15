from django.urls import path

from web.views.dev import asl_hisobga_qaytish, rol_almashtirish, rol_paneli

urlpatterns = [
    path("panel/", rol_paneli, name="panel"),
    path("almashtirish/", rol_almashtirish, name="almashtirish"),
    path("qaytish/", asl_hisobga_qaytish, name="qaytish"),
]
