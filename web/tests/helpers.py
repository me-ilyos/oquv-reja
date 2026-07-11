"""Role-aware user builders and login helpers for web view tests."""

from itertools import count

from django.test import Client

from accounts.models import Department, Foydalanuvchi, Rol
from plans.tests.factories import make_oqituvchi

_raqam = count(1)

PAROL = "test-parol-123"


def foydalanuvchi_yarat(rol: str) -> Foydalanuvchi:
    n = next(_raqam)
    return Foydalanuvchi.objects.create_user(
        telefon=f"+9988{n:08d}",
        password=PAROL,
        first_name="Web",
        last_name=f"Test{n}",
        rol=rol,
    )


def office_admin_yarat() -> Foydalanuvchi:
    return foydalanuvchi_yarat(Rol.OFFICE_ADMIN)


def mudir_yarat(kafedra: Department | None = None) -> Foydalanuvchi:
    """A DEPARTMENT_ADMIN with a profile set as their kafedra's mudir."""
    profil = make_oqituvchi(kafedra=kafedra)
    foydalanuvchi = profil.foydalanuvchi
    foydalanuvchi.rol = Rol.DEPARTMENT_ADMIN
    foydalanuvchi.save(update_fields=["rol"])
    profil.kafedra.mudir = profil
    profil.kafedra.save(update_fields=["mudir"])
    return foydalanuvchi


def oqituvchi_yarat(kafedra: Department | None = None) -> Foydalanuvchi:
    return make_oqituvchi(kafedra=kafedra).foydalanuvchi


def login(client: Client, foydalanuvchi: Foydalanuvchi) -> None:
    client.force_login(foydalanuvchi)
