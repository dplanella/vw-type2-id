from django.test import TestCase
from mplate_decoder.models import Mplate
from datetime import date


class MplateDecodeTestCase(TestCase):

    LATE_BAY_01_CHASSIS = "92023025"
    LATE_BAY_02_CHASSIS = "22138101"
    EARLY_BAY_01_CHASSIS = "9123833"

    def setUp(self):
        Mplate.objects.create(
            chassis_number_short=self.LATE_BAY_01_CHASSIS,
            m_codes_1='',
            m_codes_2='D03 P22 005 227',
            paint_and_interior='9451EB',
            production_date='382',
            production_planned='7494',
            export_destination='UT',
            model='2319',
            aggregate_code='61',
            emden='',
        )

        Mplate.objects.create(
            chassis_number_short=self.LATE_BAY_02_CHASSIS,
            m_codes_1='A89 089 100 119',
            m_codes_2='',
            paint_and_interior='918551',
            production_date='105',
            production_planned='7490',
            export_destination='056',
            model='2319',
            aggregate_code='31',
            emden='',
        )

        Mplate.objects.create(
            chassis_number_short=self.EARLY_BAY_01_CHASSIS,
            m_codes_1='',
            m_codes_2='408 095 504 507',
            paint_and_interior='383851',
            production_date='072',
            production_planned='',
            export_destination='PG',
            model='2650',
            aggregate_code='11',
            emden='',
        )

    def test_decode_model_year(self):
        """Mplate model year is correctly decoded"""

        late_bay_01 = Mplate.objects.get(
            chassis_number_short=self.LATE_BAY_01_CHASSIS)

        late_bay_02 = Mplate.objects.get(
            chassis_number_short=self.LATE_BAY_02_CHASSIS)

        early_bay_01 = Mplate.objects.get(
            chassis_number_short=self.EARLY_BAY_01_CHASSIS)

        self.assertEqual(late_bay_01.model_year, 1979)
        self.assertEqual(late_bay_02.model_year, 1972)
        self.assertEqual(early_bay_01.model_year, 1969)

    def test_decode_production_date(self):
        """Mplate production date is correctly decoded"""

        late_bay_01 = Mplate.objects.get(
            chassis_number_short=self.LATE_BAY_01_CHASSIS)

        late_bay_02 = Mplate.objects.get(
            chassis_number_short=self.LATE_BAY_02_CHASSIS)

        early_bay_01 = Mplate.objects.get(
            chassis_number_short=self.EARLY_BAY_01_CHASSIS)

        self.assertEqual(late_bay_01.get_production_date(as_string=False),
                         date(1978, 9, 19))
        self.assertEqual(late_bay_02.get_production_date(as_string=False),
                         date(1972, 3, 10))
        self.assertEqual(early_bay_01.get_production_date(as_string=False),
                         date(1969, 2, 7))
