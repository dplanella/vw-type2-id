import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.test import TestCase

from mplate_decoder.management.commands import export_db_strings


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
