from django.test import TestCase

from mplate_decoder.models import Mplate
from mplate_decoder.test_smoke import PLATE


class DecodedModelTest(TestCase):
    """Plates store their decoded model, which the metrics page counts."""

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

    def test_metrics(self):
        self.client.post('/mplate/decode/', PLATE)
        model = Mplate.objects.get().decoded_model
        with self.assertNumQueries(3):
            response = self.client.get('/mplate/metrics/')
        self.assertEqual(response.context['modelsData'], [1])
        self.assertIn(f'({model.model}{model.configuration}{model.extras})',
                      response.context['modelsLabels'][0])
