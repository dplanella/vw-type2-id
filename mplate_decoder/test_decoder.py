from datetime import date
from unittest import expectedFailure

from django.forms import ValidationError
from django.test import SimpleTestCase, TestCase

from mplate_decoder.models import (
    Color,
    ExportDestination,
    ExteriorColor,
    InteriorColor,
    Mcode,
    McodeCollection,
    Mplate,
    MplateDecoder,
    VwType2Model,
)
from mplate_decoder.test_smoke import PLATE

FIXTURES = [
    'tst_mplate_gearbox.json',
    'tst_mplate_engine.json',
    'tst_mplate_vwtype2model',
]


def create_plate(**changes):
    """Create and return a plate based on the smoke test plate."""
    return Mplate.objects.create(**dict(PLATE, **changes))


class ModelYearTest(SimpleTestCase):
    """The model year comes from the first digits of the chassis number."""

    def test_decode_model_year(self):
        decoder = MplateDecoder()
        for chassis, year in [('8123456', 1968), ('9123833', 1969),
                              ('02057644', 1970), ('22138101', 1972),
                              ('92023025', 1979)]:
            with self.subTest(chassis=chassis):
                self.assertEqual(decoder.decode_model_year(chassis), year)

    def test_invalid_length(self):
        with self.assertRaises(ValidationError):
            MplateDecoder().decode_model_year('912345678')


class ProductionDateTest(SimpleTestCase):
    """The production date is a day and month (1968-69) or a week code."""

    def test_decode_production_date(self):
        decoder = MplateDecoder()
        for chassis, code, expected in [
                ('9123833', '072', date(1969, 2, 7)),
                ('8123456', '15O', date(1967, 10, 15)),
                ('9123833', '25D', date(1968, 12, 25)),
                ('02057644', '431', date(1969, 10, 20)),
                ('22138101', '105', date(1972, 3, 10)),
                ('92023025', '382', date(1978, 9, 19))]:
            with self.subTest(chassis=chassis, code=code):
                self.assertEqual(
                    decoder.decode_production_date(chassis, code), expected)


class DecodeModelTest(TestCase):
    """The model is looked up by model code and year, then by M-codes."""

    fixtures = FIXTURES

    def decode(self, model_code, year, m_codes):
        """Return the primary key of the decoded model, or None."""
        model = MplateDecoder().decode_model(model_code, str(year), m_codes)
        return model and model.pk

    def test_single_match(self):
        self.assertEqual(self.decode('2310', 1972, ['000']), 66)

    def test_special_sales_m_code(self):
        self.assertEqual(self.decode('2215', 1973, ['500', '736']), 102)

    @expectedFailure
    def test_m_codes_pick_among_matches(self):
        """GitHub #14: model decoded from another model code or year."""
        self.assertEqual(self.decode('2215', 1973, ['500']), 27)
        self.assertEqual(self.decode('2218', 1977, ['147']), 31)

    def test_no_match(self):
        self.assertIsNone(self.decode('2119', 1970, ['000']))

    def test_describe_unknown_model(self):
        plate = create_plate(chassis_number_short='22138101',
                             production_date_code='105', model_code='2119')
        description = plate.describe_model()
        self.assertEqual(description['model_description'], 'Unknown (2119)')
        self.assertEqual(description['extras_description'], 'Unknown')

    def test_describe_model(self):
        plate = create_plate(model_code='2310', m_codes_2='')
        model = VwType2Model.objects.get(pk=66)
        description = plate.describe_model()
        self.assertEqual(description['model_description'],
                         model.model_description)
        self.assertEqual(description['model_code_catalog'], '231')


class DecodeMcodesTest(TestCase):
    """M-codes are expanded from collections and described by year."""

    def setUp(self):
        Mcode.objects.create(m_code='Z01', description='Test option one')
        Mcode.objects.create(m_code='Z02', description='Test option 1972',
                             years='1972')
        Mcode.objects.create(m_code='Z02', description='Test option 1975',
                             years='1975')
        Mcode.objects.create(m_code='Z03', description='Test special',
                             is_special_code=True)
        McodeCollection.objects.create(m_code='Z10', collection='Z01 Z02',
                                       years='1972')

    def decode(self, m_codes, chassis='22138101'):
        """Decode M-codes for a 1972 bus unless another chassis is given."""
        return MplateDecoder().decode_mcodes(m_codes, '', chassis)

    def test_description(self):
        self.assertEqual(self.decode('Z01'), {'M Z01': 'Test option one'})

    def test_description_by_year(self):
        self.assertEqual(self.decode('Z02'), {'M Z02': 'Test option 1972'})
        self.assertEqual(self.decode('Z02', '52012345'),
                         {'M Z02': 'Test option 1975'})

    def test_special_code(self):
        self.assertEqual(self.decode('Z03'), {'S Z03': 'Test special'})

    def test_collection(self):
        self.assertEqual(self.decode('Z10'), {
            'M Z01': 'Test option one',
            'M Z02': 'Test option 1972',
        })

    def test_collection_only_in_its_years(self):
        self.assertEqual(self.decode('Z10', '52012345'),
                         {'M Z10': 'Unknown code, year 1975'})

    def test_unknown_codes(self):
        self.assertEqual(self.decode('Z99 799'), {
            'M Z99': 'Unknown code, year 1972',
            'S 799': 'Unknown code, year 1972',
        })

    def test_code_not_defined_for_year(self):
        self.assertEqual(self.decode('Z02', '62012345'),
                         {'M Z02': 'Undefined code, year 1976'})


class ExportDestinationTest(TestCase):
    """The export destination code gives a destination and a country."""

    fixtures = FIXTURES

    def setUp(self):
        ExportDestination.objects.create(
            export_code='T1', destination='Test dealer', country='Testland',
            region='North', port='Testport')
        ExportDestination.objects.create(
            export_code='T2', region='Test region', city='Testcity')

    def country(self, code, with_port=True):
        """Describe the country of a plate with the given export code."""
        plate = Mplate(**dict(PLATE, export_destination_code=code))
        return MplateDecoder(plate).describe_export_destination_country(
            with_port=with_port)

    def test_country(self):
        self.assertEqual(self.country('T1'), 'Testland, North via Testport')
        self.assertEqual(self.country('T2'), 'Test region via Testcity')

    def test_country_without_port(self):
        self.assertEqual(self.country('T1', with_port=False), 'Testland')
        self.assertEqual(self.country('T2', with_port=False), 'Test region')

    def test_unknown_country(self):
        self.assertEqual(self.country('Q9'), 'Unknown (Q9)')

    def test_destination(self):
        plate = create_plate(export_destination_code='T1')
        self.assertEqual(plate.describe_export_destination(), 'Test dealer')

    def test_unknown_destination(self):
        plate = create_plate(export_destination_code='Q9')
        self.assertEqual(plate.describe_export_destination(), 'Unknown (Q9)')

    def test_destination_not_specified(self):
        plate = create_plate(export_destination_code='')
        self.assertEqual(plate.describe_export_destination(), 'Not specified')

    @expectedFailure
    def test_plate_country(self):
        """GitHub #15: plate pages show "Unknown (True)"."""
        for code, expected in [('Q9', 'Unknown (Q9)'), ('', 'Not specified')]:
            plate = Mplate(**dict(PLATE, export_destination_code=code))
            self.assertEqual(plate.describe_export_destination_country(),
                             expected)

    @expectedFailure
    def test_stored_country(self):
        """GitHub #15: the port is stored with the country."""
        plate = create_plate(export_destination_code='T1')
        self.assertEqual(plate.destination_country, 'Testland')


class ColorTest(TestCase):
    """Paint and interior codes give the body, roof and interior colours."""

    fixtures = FIXTURES

    def setUp(self):
        white = Color.objects.create(lacquer_code='L111',
                                     color_name='Test White', chip='#ffffff')
        red = Color.objects.create(lacquer_code='L222',
                                   color_name='Test Red', chip='#ff0000')
        ExteriorColor.objects.create(
            plate_code='1234', lacquer_code_body='L222',
            lacquer_code_roof='L111', lacquer_code_body_link=red,
            lacquer_code_roof_link=white, sonderlackierung=False)
        ExteriorColor.objects.create(
            plate_code='4321', lacquer_code_body='L111',
            lacquer_code_body_link=white, sonderlackierung=False)
        InteriorColor.objects.create(plate_code='51', color_name='Test Grey',
                                     material='Test vinyl')

    def test_exterior_color(self):
        plate = create_plate(paint_and_interior_code='123451')
        self.assertEqual(plate.exteriorcolor_code, '1234')
        description = plate.describe_exteriorcolor()
        self.assertIn('Body: Test Red (L222)', description)
        self.assertIn('Roof: Test White (L111)', description)
        self.assertEqual(plate._get_exteriorcolorchip(),
                         ('#ff0000', '#ffffff'))

    def test_roof_same_as_body(self):
        plate = create_plate(paint_and_interior_code='432151')
        self.assertIn('Roof: Test White (L111)',
                      plate.describe_exteriorcolor())

    def test_unknown_exterior_color(self):
        plate = create_plate(paint_and_interior_code='999951')
        self.assertEqual(plate.describe_exteriorcolor(),
                         'Unknown exterior color code (9999)')
        self.assertEqual(plate._get_exteriorcolorchip(), ('', ''))

    def test_interior_color(self):
        plate = create_plate(paint_and_interior_code='123451')
        self.assertEqual(plate.describe_interiorcolor(),
                         'Test Grey, Test vinyl')

    def test_unknown_interior_color(self):
        plate = create_plate(paint_and_interior_code='123499')
        self.assertEqual(plate.describe_interiorcolor(),
                         '(99) Unknown color, Unknown material')


class AggregateTest(TestCase):
    """The aggregate code gives the engine and the gearbox."""

    fixtures = FIXTURES

    def test_engine_and_gearbox(self):
        plate = create_plate(aggregate_code='43')
        self.assertEqual(plate.get_engine(), 'Type 4, Dual carburetor, '
                                             'Exhaust emission control')
        self.assertEqual(plate.get_gearbox(),
                         'Automatic transmission, 3-speed')

    def test_unknown(self):
        plate = create_plate(aggregate_code='99')
        self.assertEqual(plate.get_engine(), 'Unavailable engine description')
        self.assertEqual(plate.get_gearbox(),
                         'Unavailable transmission description')
