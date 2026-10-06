from django.test import TestCase

from mplate_decoder.models import Mplate
from mplate_decoder.test_smoke import PLATE


class DecodedModelTest(TestCase):
    """Plates store their decoded model."""

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
        'tst_mplate_vwtype2model',
    ]

    def test_save_stores_model(self):
        self.client.post('/mplate/decode/', PLATE)
        plate = Mplate.objects.get()
        self.assertIsNotNone(plate.decoded_model)
        self.assertEqual(plate.decoded_model, plate.model)
