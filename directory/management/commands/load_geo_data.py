"""
python manage.py load_geo_data

data/ papkasidagi viloyat.geojson, Tuman.geojson, mahalla.geojson fayllarini
Region, District, Mahalla modellariga yuklaydi.

Barcha eski ma'lumotlar o'chiriladi, keyin qaytadan yuklanadi.

SOATO kodlari:
  Region.code   <- viloyat.geojson  :: parent_code
  District.code <- Tuman.geojson    :: code
  Mahalla.code  <- mahalla.geojson  :: code

Bog'lanish:
  District.region <- tuman.parent_code == region.code
  Mahalla.district <- mahalla.district_cad_id[:5] == tuman.district_cad_id
  Mahalla.region   <- mahalla.region_cad_id == tuman.region_cad_id (Region.geo_json yordamida)
"""
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from directory.models import Region, District, Mahalla

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')


def _load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, encoding='utf-8') as f:
        return json.load(f)


class Command(BaseCommand):
    help = 'GeoJSON fayllardan Region, District, Mahalla yuklaydi (eski o\'chiriladi)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--only',
            choices=['region', 'district', 'mahalla'],
            help='Faqat bitta model yuklash',
        )

    def handle(self, *args, **options):
        only = options.get('only')

        if only in (None, 'region'):
            self._load_regions()
        if only in (None, 'district'):
            self._load_districts()
        if only in (None, 'mahalla'):
            self._load_mahallas()

        self.stdout.write(self.style.SUCCESS('Yuklash yakunlandi.'))

    # ──────────────────────────────────────────────────────────────────────────

    def _load_regions(self):
        self.stdout.write('Region (viloyat): eski ma\'lumotlar o\'chirilmoqda...')
        Region.objects.all().delete()

        self.stdout.write('Region yuklanmoqda...')
        data = _load_json('viloyat.geojson')
        count = 0

        for feature in data['features']:
            props = feature['properties']
            Region.objects.create(
                code=str(props['parent_code']),
                name=props['region_name'],
                boundary_data=feature.get('geometry'),
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'  Region: {count} ta yaratildi'))

    def _load_districts(self):
        self.stdout.write('District (tuman): eski ma\'lumotlar o\'chirilmoqda...')
        District.objects.all().delete()

        self.stdout.write('District yuklanmoqda...')
        data = _load_json('Tuman.geojson')

        # region SOATO (parent_code) → Region object
        region_map = {r.code: r for r in Region.objects.all()}

        count = skipped = 0

        for feature in data['features']:
            props = feature['properties']
            region_soato = str(props['parent_code'])
            region = region_map.get(region_soato)

            if region is None:
                self.stdout.write(
                    self.style.WARNING(f"  Region topilmadi: soato={region_soato} ({props['district']})")
                )
                skipped += 1
                continue

            District.objects.create(
                code=str(props['code']),
                name=props['district'],
                region=region,
                boundary_data=feature.get('geometry'),
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  District: {count} ta yaratildi, {skipped} ta o\'tkazib yuborildi'
        ))

    def _load_mahallas(self):
        self.stdout.write('Mahalla: eski ma\'lumotlar o\'chirilmoqda...')
        Mahalla.objects.all().delete()

        self.stdout.write('Mahalla yuklanmoqda...')
        data = _load_json('mahalla.geojson')

        # region_cad_id → Region (viloyat.geojson dagi region_cad_id bilan mos)
        # viloyat.geojson da region_cad_id bor, lekin Region.code = parent_code
        # Shuning uchun Tuman.geojson orqali region_cad_id→region_soato xaritasi tuzamiz
        tuman_data = _load_json('Tuman.geojson')

        # region_cad_id → region SOATO (parent_code)
        rcad_to_soato = {}
        # district_cad_id (e.g. "11:15") → District object
        cad_to_district = {}

        for feat in tuman_data['features']:
            p = feat['properties']
            rcad_to_soato[str(p['region_cad_id'])] = str(p['parent_code'])
            cad_to_district[str(p['district_cad_id'])] = str(p['code'])

        region_map = {r.code: r for r in Region.objects.all()}
        district_map = {d.code: d for d in District.objects.all()}

        count = skipped = 0
        total = len(data['features'])

        for i, feature in enumerate(data['features'], 1):
            if i % 1000 == 0:
                self.stdout.write(f'  {i}/{total}...')

            props = feature['properties']
            name = props['mahalla_nomi']
            soato = str(props['code'])
            region_cad_id = str(props['region_cad_id'])
            # "23:17:00" → "23:17"
            dist_cad = ':'.join(str(props['district_cad_id']).split(':')[:2])

            region_soato = rcad_to_soato.get(region_cad_id)
            district_soato = cad_to_district.get(dist_cad)

            region = region_map.get(region_soato)
            district = district_map.get(district_soato)

            if district is None:
                skipped += 1
                continue

            Mahalla.objects.create(
                code=soato,
                name=name,
                region=region,
                district=district,
                boundary_data=feature.get('geometry'),
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(
            f'  Mahalla: {count} ta yaratildi, {skipped} ta o\'tkazib yuborildi'
        ))
