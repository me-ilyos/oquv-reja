"""Seed departments (kafedra) with random teacher accounts and a head each.

One-off data seeding: teacher names are randomly generated placeholders since
no real HR data is available yet; every created teacher shares one default
password, printed at the end for the operator to hand out and rotate.
"""

import random

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.management.commands.uzbek_names import FIRST_NAMES, LAST_NAMES
from accounts.models import (
    Department,
    Foydalanuvchi,
    OqituvchiProfil,
    OqituvchiTuri,
    Rol,
)

DEPARTMENT_NAMES = [
    "Axborot tizimlari va texnologiyalari",
    "Raqamli texnologiyalar",
    "Menejment",
    "Ijtimoiy fanlar",
    "Buxgalteriya hisobi",
    "Xorijiy tillar",
    "Marketing",
]

DEFAULT_PASSWORD = "Oquvreja2026!"
PHONE_PREFIX = "+99890"


class Command(BaseCommand):
    help = "Create departments, random teacher accounts, and assign heads."

    def handle(self, *args: object, **options: object) -> None:
        turlari = list(OqituvchiTuri.objects.all())
        if not turlari:
            raise CommandError(
                "No OqituvchiTuri rows found. Create teacher types before seeding."
            )

        with transaction.atomic():
            for index, nomi in enumerate(DEPARTMENT_NAMES):
                self._seed_department(nomi, index, turlari)

        self.stdout.write(self.style.SUCCESS("Done."))
        self.stdout.write(
            f"Default password for all seeded teachers: {DEFAULT_PASSWORD}"
        )

    def _seed_department(
        self, nomi: str, index: int, turlari: list[OqituvchiTuri]
    ) -> None:
        department, created = Department.objects.get_or_create(nomi=nomi)
        if not created:
            self.stdout.write(f"Skipped (exists): {nomi}")
            return

        head_profil = self._create_teacher_profil(index * 100, department, turlari)
        head_profil.foydalanuvchi.rol = Rol.DEPARTMENT_ADMIN
        head_profil.foydalanuvchi.save(update_fields=["rol"])
        department.mudir = head_profil
        department.save(update_fields=["mudir"])

        for offset in range(1, 4):
            self._create_teacher_profil(index * 100 + offset, department, turlari)

        self.stdout.write(self.style.SUCCESS(f"Created: {nomi} (head: {head_profil})"))

    def _create_teacher_profil(
        self, seed: int, department: Department, turlari: list[OqituvchiTuri]
    ) -> OqituvchiProfil:
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        telefon = f"{PHONE_PREFIX}{seed:07d}"
        user = Foydalanuvchi.objects.create_user(
            telefon=telefon,
            password=DEFAULT_PASSWORD,
            first_name=first_name,
            last_name=last_name,
            rol=Rol.TEACHER,
        )
        return OqituvchiProfil.objects.create(
            foydalanuvchi=user, kafedra=department, turi=random.choice(turlari)
        )
