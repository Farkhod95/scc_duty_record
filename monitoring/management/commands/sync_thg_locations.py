"""
python manage.py sync_thg_locations --thg-district 1131 --organization 5

THG (IIV xarita pull API) dagi poligonlarni Location modeliga yuklaydi:
  tqm-zones      — TQM zonalari
  patrol-routes  — patrul marshrutlari
  ppx-areas      — PPX hududlari

--thg-district  THG tizimidagi tuman ID (ro'yxat: --list-districts)
--organization  Bizdagi Organization ID — Location lar shu tashkilotga biriktiriladi
--layers        Faqat ayrim qatlamlar (vergul bilan), default: hammasi
--dry-run       Bazaga yozmasdan nima bo'lishini ko'rsatadi
--no-grpc       LocationService ga (PaligonCreate) yubormaydi
"""
from django.core.management.base import BaseCommand, CommandError

from directory.models import Organization
from monitoring.services.thg_iiv_client import fetch, ThgIivError
from monitoring.services.thg_iiv_sync import LAYERS, sync_locations


class Command(BaseCommand):
    help = "THG poligonlarini (TQM zona, patrul marshruti, PPX hududi) Location ga yuklaydi"

    def add_arguments(self, parser):
        parser.add_argument('--thg-district', type=int, help="THG tizimidagi tuman ID")
        parser.add_argument('--organization', type=int, help="Bizdagi Organization ID")
        parser.add_argument('--layers', help="Qatlamlar vergul bilan: " + ', '.join(LAYERS))
        parser.add_argument('--dry-run', action='store_true', help="Bazaga yozmaydi")
        parser.add_argument('--no-grpc', action='store_true', help="LocationService ga yubormaydi")
        parser.add_argument('--list-districts', action='store_true', help="THG tumanlari ro'yxatini chiqaradi")

    def handle(self, *args, **options):
        try:
            if options['list_districts']:
                return self._list_districts()

            if not options['thg_district'] or not options['organization']:
                raise CommandError("--thg-district va --organization majburiy.")

            try:
                org = Organization.objects.get(pk=options['organization'])
            except Organization.DoesNotExist:
                raise CommandError(f"Organization id={options['organization']} topilmadi.")

            layers = None
            if options['layers']:
                layers = [x.strip() for x in options['layers'].split(',') if x.strip()]
                unknown = [x for x in layers if x not in LAYERS]
                if unknown:
                    raise CommandError(f"Noma'lum qatlam: {', '.join(unknown)}")

            stats = sync_locations(
                org, options['thg_district'],
                layers=layers,
                dry_run=options['dry_run'],
                push_grpc=not options['no_grpc'],
            )
        except ThgIivError as e:
            raise CommandError(str(e))

        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN — bazaga yozilmadi"))
        for layer, s in stats.items():
            self.stdout.write(
                f"  {layer}: olindi={s['fetched']} yaratildi={s['created']} "
                f"yangilandi={s['updated']} o'zgarmagan={s['unchanged']} o'tkazib yuborildi={s['skipped']}"
            )
        self.stdout.write(self.style.SUCCESS("Yakunlandi."))

    def _list_districts(self):
        regions = {r['id']: r['uz'] for r in fetch('regions', use_cache=False)['data']}
        for d in fetch('districts', use_cache=False)['data']:
            self.stdout.write(f"{d['id']}\t{d['uz']}\t({regions.get(d['region_id'], d['region_id'])})")
