from django.conf import settings
from django.db import migrations
from django.utils.translation import override


def store_in_english(apps, schema_editor):
    """Recompute each plate's destination country in English."""
    from mplate_decoder.models import Mplate

    StoredMplate = apps.get_model('mplate_decoder', 'Mplate')
    changed = []
    with override(settings.LANGUAGE_CODE):
        for plate in StoredMplate.objects.only(
                'export_destination_code', 'destination_country'):
            country = str(Mplate(
                export_destination_code=plate.export_destination_code,
            ).describe_export_destination_country(with_port=False))
            if country != plate.destination_country:
                plate.destination_country = country
                changed.append(plate)

    StoredMplate.objects.bulk_update(changed, ['destination_country'],
                                     batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('mplate_decoder', '0036_fill_mplate_decoded_model'),
    ]

    operations = [
        migrations.RunPython(store_in_english, migrations.RunPython.noop),
    ]
