import logging

from django.db import migrations


def fill_decoded_model(apps, schema_editor):
    from mplate_decoder.models import Mplate

    StoredMplate = apps.get_model('mplate_decoder', 'Mplate')
    plates = list(StoredMplate.objects.only(
        'model_code', 'model_year', 'm_codes'))

    # Plates without a known model are expected; don't log each of them
    decoder_logger = logging.getLogger('mplate_decoder.models')
    level = decoder_logger.level
    decoder_logger.setLevel(logging.CRITICAL)
    try:
        for plate in plates:
            model = Mplate(model_code=plate.model_code,
                           model_year=plate.model_year,
                           m_codes=plate.m_codes).model
            plate.decoded_model_id = model.pk if model else None
    finally:
        decoder_logger.setLevel(level)

    StoredMplate.objects.bulk_update(plates, ['decoded_model'],
                                     batch_size=500)


class Migration(migrations.Migration):

    dependencies = [
        ('mplate_decoder', '0035_mplate_decoded_model'),
    ]

    operations = [
        migrations.RunPython(fill_decoded_model, migrations.RunPython.noop),
    ]
