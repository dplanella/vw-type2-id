from django.test import TestCase

from mplate_decoder.forms import MplateCreateForm
from mplate_decoder.models import Mplate
from mplate_decoder.test_smoke import PLATE

EARLY_PLATE = dict(PLATE, chassis_number_short='9123833',
                   production_date_code='152', model_code='2650',
                   aggregate_code='11')


class MplateCreateFormTest(TestCase):
    """The M-plate form validates and normalises each code."""

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
        'tst_mplate_vwtype2model',
    ]

    def form(self, plate=PLATE, **changes):
        """Return a bound form for the plate with the changed fields."""
        return MplateCreateForm(data=dict(plate, **changes))

    def assert_valid(self, field, value, cleaned=None, plate=PLATE):
        """Assert the field accepts the value and cleans it as expected."""
        form = self.form(plate, **{field: value})
        self.assertTrue(form.is_valid(), form.errors)
        expected = value if cleaned is None else cleaned
        self.assertEqual(form.cleaned_data[field], expected)

    def assert_invalid(self, field, *values, plate=PLATE):
        """Assert the field rejects each value."""
        for value in values:
            with self.subTest(field=field, value=value):
                form = self.form(plate, **{field: value})
                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_valid_plates(self):
        for plate in (PLATE, EARLY_PLATE):
            with self.subTest(chassis=plate['chassis_number_short']):
                form = self.form(plate)
                self.assertTrue(form.is_valid(), form.errors)

    def test_chassis_number(self):
        self.assert_invalid('chassis_number_short',
                            '912383', '9212345a', '912 3833', '123456789',
                            '83023025')

    def test_chassis_number_already_exists(self):
        self.form().save()
        form = self.form()
        self.assertFalse(form.is_valid())
        self.assertIn('/mplate/92023025/',
                      form.errors['chassis_number_short'][0])

    def test_chassis_number_unchanged_on_update(self):
        plate = self.form().save()
        form = MplateCreateForm(data=PLATE, instance=plate)
        self.assertTrue(form.is_valid(), form.errors)

    def test_m_codes(self):
        self.assert_valid('m_codes_1', 'd03p22', 'D03 P22')
        self.assert_valid('m_codes_2', 'D03 P22 005', 'D03 P22 005')
        self.assert_valid('m_codes_1', '', '')
        self.assert_invalid('m_codes_1', 'D03-P22', 'D0', 'D03 P2', 'D03P2')

    def test_paint_and_interior_code(self):
        self.assert_valid('paint_and_interior_code', '9451eb', '9451EB')
        self.assert_invalid('paint_and_interior_code', '9451E', '9451-E')

    def test_production_date_late_bay(self):
        self.assert_valid('production_date_code', '015')
        self.assert_invalid('production_date_code',
                            '002', '532', '387', '38', 'A82')

    def test_production_date_early_bay(self):
        self.assert_valid('production_date_code', '15o', '15O',
                          plate=EARLY_PLATE)
        self.assert_invalid('production_date_code', '070', '07X', '402',
                            plate=EARLY_PLATE)

    def test_export_destination_code(self):
        self.assert_valid('export_destination_code', 'ut', 'UT')
        self.assert_valid('export_destination_code', '', '')
        self.assert_invalid('export_destination_code', 'U', 'U-')

    def test_model_code(self):
        self.assert_valid('model_code', '2310')
        self.assert_invalid('model_code', '231', '2510', '2999', '23a9')

    def test_aggregate_code(self):
        self.assert_valid('aggregate_code', '43')
        self.assert_invalid('aggregate_code', '4', 'ab', '13', '71')

    def test_emden(self):
        self.assert_valid('emden', 'e', 'E')
        self.assert_valid('emden', '', '')
        self.assert_invalid('emden', 'X')

    def test_save_derives_fields(self):
        plate = self.form(m_codes_1='D03', m_codes_2='P22').save()
        plate = Mplate.objects.get(pk=plate.pk)
        self.assertEqual(plate.m_codes, 'D03 P22')
        self.assertEqual(plate.model_year, '1979')
