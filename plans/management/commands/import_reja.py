from argparse import ArgumentParser
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from plans.importer import ImportNatija, ImportXato, import_reja, parse_xlsx


class Command(BaseCommand):
    help = "O'quv reja .xlsx fayllarini bazaga import qiladi."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("files", nargs="+", type=Path)
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Mavjud rejani qayta yuklaydi (yuklamalar bo'lmasa).",
        )
        parser.add_argument(
            "--yil",
            type=int,
            default=None,
            help="Boshlanish yili; varaqda o'quv yili bo'lmasa majburiy.",
        )

    def handle(self, *args: object, **options: object) -> None:
        xatolar = 0
        for path in options["files"]:
            try:
                natija = self._bitta_fayl(path, options)
                self._chiqarish(path, natija)
            except ImportXato as xato:
                self.stderr.write(self.style.ERROR(f"{path.name}: {xato}"))
                xatolar += 1
        if xatolar:
            raise CommandError(f"{xatolar} ta fayl import qilinmadi")

    def _bitta_fayl(self, path: Path, options: dict[str, object]) -> ImportNatija:
        if not path.exists():
            raise ImportXato("fayl topilmadi")
        return import_reja(
            parse_xlsx(path, boshlanish_yili=options["yil"]),
            replace=options["replace"],
        )

    def _chiqarish(self, path: Path, natija: ImportNatija) -> None:
        holat = "yaratildi" if natija.yaratildi else "yangilandi"
        self.stdout.write(
            f"{path.name} -> {natija.reja} "
            f"({natija.fan_soni} fan, {natija.variant_soni} variant) {holat}"
        )
        for ogohlantirish in natija.ogohlantirishlar:
            self.stdout.write(self.style.WARNING(f"  OGOHLANTIRISH: {ogohlantirish}"))
