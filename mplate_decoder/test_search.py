from unittest import expectedFailure

from django.test import TestCase

from mplate_decoder.models import ExportDestination, Mplate
from mplate_decoder.test_smoke import PLATE


class SearchTest(TestCase):
    """Search finds plates by M-code or by field:value terms."""

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
        'tst_mplate_vwtype2model',
    ]

    def setUp(self):
        ExportDestination.objects.create(export_code='T1', country='Testland')
        Mplate.objects.create(**PLATE)
        Mplate.objects.create(**dict(
            PLATE, chassis_number_short='22138101', m_codes_2='D03 140',
            production_date_code='105', model_code='2311',
            export_destination_code='T1'))

    def search(self, query):
        """Return the chassis numbers found for the query, sorted."""
        response = self.client.get('/mplate/search/', {'q': query})
        self.assertEqual(response.status_code, 200)
        return sorted(plate.chassis_number_short
                      for plate in response.context['mplates'])

    def test_m_code(self):
        self.assertEqual(self.search('P22'), ['92023025'])
        self.assertEqual(self.search('D03'), ['22138101', '92023025'])
        self.assertEqual(self.search('mcode:140'), ['22138101'])
        self.assertEqual(self.search('D03 -mcode:140'), ['92023025'])

    def test_year(self):
        self.assertEqual(self.search('year:1972'), ['22138101'])
        self.assertEqual(self.search('-year:1972'), ['92023025'])
        self.assertEqual(self.search('D03 year:1979'), ['92023025'])

    def test_all(self):
        self.assertEqual(self.search('*'), ['22138101', '92023025'])

    def test_empty(self):
        self.assertEqual(self.search(''), [])

    @expectedFailure
    def test_model(self):
        """model: search crashes (fixed later)."""
        self.assertEqual(self.search('model:2311'), ['22138101'])
        self.assertEqual(self.search('-model:2311'), ['92023025'])

    @expectedFailure
    def test_country(self):
        """country: search looks in the M-codes (fixed later)."""
        self.assertEqual(self.search('country:Testland'), ['22138101'])
        self.assertEqual(self.search('-country:Testland'), ['92023025'])
