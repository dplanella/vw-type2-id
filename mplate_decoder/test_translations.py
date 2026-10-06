import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.forms import ValidationError
from django.test import TestCase
from django.utils.translation import override

from mplate_decoder.forms import MplateCreateForm
from mplate_decoder.management.commands import export_db_strings
from mplate_decoder.models import ExportDestination, Mplate


class ExportDbStringsTest(TestCase):
    """The reference data strings are exported for makemessages."""

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
    ]

    def test_export_db_strings(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'db_strings.py'
            with mock.patch.object(export_db_strings, 'OUTPUT', output):
                call_command('export_db_strings', stdout=StringIO())
            lines = output.read_text().splitlines()

        strings = [line for line in lines if line.startswith('gettext_noop(')]
        self.assertIn("gettext_noop('Automatic transmission, 3-speed')",
                      strings)
        self.assertIn("gettext_noop('Type 4')", strings)
        self.assertEqual(strings, sorted(set(strings)))


class ReferenceDataTranslationTest(TestCase):
    """Reference data is stored in English and translated for display."""

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
        'tst_mplate_vwtype2model',
    ]

    def create_mplate(self):
        """Create a plate with a German destination and automatic gearbox."""
        ExportDestination.objects.create(export_code='XX', country='Germany')
        return Mplate.objects.create(
            chassis_number_short='92023025',
            m_codes_1='',
            m_codes_2='',
            paint_and_interior_code='9451EB',
            production_date_code='382',
            production_planned='7494',
            export_destination_code='XX',
            model_code='2319',
            aggregate_code='43',
            emden='',
        )

    def test_description_is_translated(self):
        mplate = self.create_mplate()
        with override('de'):
            self.assertEqual(mplate.get_gearbox(),
                             'Automatikgetriebe, 3-Gang')
            self.assertEqual(mplate.describe_export_destination_country(),
                             'Deutschland')

    def test_destination_country_is_stored_in_english(self):
        with override('de'):
            mplate = self.create_mplate()
        self.assertEqual(mplate.destination_country, 'Germany')

    def test_aggregate_validation_ignores_language(self):
        form = MplateCreateForm()
        for language in ('en', 'de'):
            with self.subTest(language=language), override(language):
                form.cleaned_data = {'aggregate_code': '43'}
                self.assertEqual(form.clean_aggregate_code(), '43')
                form.cleaned_data = {'aggregate_code': '13'}
                with self.assertRaises(ValidationError):
                    form.clean_aggregate_code()


class StoreDestinationCountryMigrationTest(TestCase):
    """The migration rewrites countries saved in another language."""

    def test_migration(self):
        from importlib import import_module

        from django.apps import apps

        migration = import_module('mplate_decoder.migrations.'
                                  '0037_store_destination_country_in_english')
        ExportDestination.objects.create(export_code='XX', country='Germany')
        plate = Mplate.objects.create(
            chassis_number_short='92023025', m_codes_1='', m_codes_2='',
            paint_and_interior_code='9451EB', production_date_code='382',
            production_planned='7494', export_destination_code='XX',
            model_code='2319', aggregate_code='43', emden='')
        Mplate.objects.filter(pk=plate.pk).update(
            destination_country='Deutschland')
        updated_at = Mplate.objects.get().updated_at

        migration.store_in_english(apps, None)

        plate = Mplate.objects.get()
        self.assertEqual(plate.destination_country, 'Germany')
        self.assertEqual(plate.updated_at, updated_at)
