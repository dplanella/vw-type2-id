from django.db.models import Model
from django.db import models
from django.urls import reverse
from django.forms import ValidationError
from datetime import date, datetime
import re
from lxml import etree
import os
from vw_type2_id.settings import BASE_DIR
import logging
logger = logging.getLogger('django')


class Mplate(Model):
    chassis_number_short = models.CharField(
        max_length=8, unique=True,
        help_text=("Chassis number shortened, with the two leading digits "
                   "removed."))
    m_codes_1 = models.CharField(
        max_length=19, blank=True,
        help_text='Row 1 of M codes (max 5)')
    m_codes_2 = models.CharField(
        max_length=19,
        help_text="Row 2 of M codes (max 4 -mod. '70-'79 or 5 -mod. '68-'69-)")
    paint_and_interior = models.CharField(
        max_length=6,
        help_text='Combined VW body/roof paint and interior codes')
    production_date = models.CharField(
        max_length=3,
        help_text='Production date')
    production_planned = models.CharField(
        max_length=4, blank=True,
        help_text='Code used for production planning')
    export_destination = models.CharField(
        max_length=3, blank=True,
        help_text='Destination code')
    # export_destination = models.ForeignKey(ExportDestination)
    model = models.CharField(
        max_length=4,
        help_text='Vehicle model')
    aggregate_code = models.CharField(
        max_length=2,
        help_text='Engine and gearbox codes')
    emden = models.CharField(
        max_length=1, blank=True,
        help_text='''Optional "E" for
            Emden''')

    def __unicode__(self):
        return self.chassis_number_short

    def get_absolute_url(self):
        return reverse(
            'mplate_decoder:mplate_retrieve',
            kwargs={'chassis_number_short': self.chassis_number_short})

    def _year_and_serial_from_chassis_no(self, chassis_number):

        MODEL_6869_CHASSIS_NR_LEN = 7
        MODEL_7079_CHASSIS_NR_LEN = 8
        MODEL_6869_YEAR_CODE_LEN = 1
        MODEL_7079_YEAR_CODE_LEN = 2

        # Validate the shortened chassis no. type
        try:
            int(chassis_number)
        except ValueError:
            raise ValidationError(
                "The shortened chassis number can only"
                " contain digits.")

        # Validate the shortened chassis no. length
        if (len(chassis_number) < MODEL_6869_CHASSIS_NR_LEN or
                len(chassis_number) > MODEL_7079_CHASSIS_NR_LEN):
            raise ValidationError(
                "The shortened chassis number should"
                " be either 7 or 8 digits."
                " You submitted {} digits".format(len(chassis_number)))

        # Extract the model year code and serial number
        splitat = -6
        model_year_code, serial_no = \
            chassis_number[:splitat], int(chassis_number[splitat:])

        # d
        if len(model_year_code) == MODEL_6869_YEAR_CODE_LEN:
            year_base = date(1960, 1, 1)
            year_delta = int(model_year_code)
            if year_delta < 8:
                raise ValidationError(
                    "Invalid model year code: {}. ".format(model_year_code) +
                    "Code must be either 8 (for 1968) or 9 (for 1969)")
        elif len(model_year_code) == MODEL_7079_YEAR_CODE_LEN:
            year_base = date(1970, 1, 1)
            year_delta = int(model_year_code[:1])
            decade_batch = int(model_year_code[1:])
            if decade_batch != 2:
                raise ValidationError(
                    "Invalid decade batch: {}. ".format(str(decade_batch)) +
                    "Second digit must be 2"
                    " for model year 1970 onwards.")
        else:
            raise ValidationError(
                "Invalid model year"
                " code length: {}".format(len(model_year_code)))

        model_year = year_base.replace(year=year_base.year + year_delta)

        return model_year, serial_no

    def get_model_year(self):
        decoder = MplateDecoder(self)
        model_year = decoder.get_model_year()

        logger.info('Model year: {}'.format(model_year))

        return model_year

    def get_serial_production_number(self):
        splitat = self._MODEL_YEAR_SERIAL_NR_SPLIT_AT
        serial_number = int(self.chassis_number[splitat:])

        logger.info('Serial number: {}'.format(serial_number))

        return serial_number

    def get_chassis_number(self):
        type_body = self.model[:2]

        return type_body + self.chassis_number_short

    def get_production_date(self):
        model_year = self.get_model_year()

        if model_year < date(1970, 1, 1):
            month_dict = {
                '1': 1,
                '2': 2,
                '3': 3,
                '4': 4,
                '5': 5,
                '6': 6,
                '7': 7,
                '8': 8,
                '9': 9,
                'O': 10,
                'N': 11,
                'D': 12
            }
            year = model_year.year - 1
            day = int(self.production_date[:2])
            month = month_dict[self.production_date[-1:]]

            production_date = datetime(year, month, day)

            production_date = production_date.strftime("%b %d, %Y")
        else:
            iso_year = model_year.year - 1
            iso_weeknumber = int(self.production_date[:2])
            iso_weekday = int(self.production_date[-1:])

            production_date = datetime.strptime(
                '{:04d} {:02d} {:d}'.format(iso_year,
                                            iso_weeknumber,
                                            iso_weekday),
                '%G %V %u').date()

        logger.info('Production date: {}'.format(production_date))

        return production_date

    def get_export_destination(self):
        export_destination = ExportDestination.objects.filter(
            export_code=self.export_destination)

        if export_destination:
            export_destination_description = \
                export_destination[0].export_destination
        else:
            export_destination_description = \
                "Unknown ({})".format(self.export_destination)

        return export_destination_description

    def get_model(self):
        model_code = self.model[:2]
        configuration_code = self.model[2]
        extras_code = self.model[3]
        model_code_catalog = self.model[:3]

        model = Type2Model.objects.filter(
            model=model_code
        )

        configuration = Type2ModelConfiguration.objects.filter(
            model=model_code, configuration=configuration_code
        )

        extras = Type2ModelExtra.objects.filter(
            model=model_code, extras=extras_code
        )

        if not model:
            model_description = "Model description unavailable"
        else:
            model_description = model[0].description

        if not configuration:
            configuration_description = "Configuration description unavailable"
        else:
            configuration_description = configuration[0].description

        if not extras:
            extras_description = "Extras description unavailable"
        else:
            extras_description = extras[0].description

        model_description = '''Volkswagen Type 2
            · {} (model {})
            · {}
            · {}'''.format(
                model_description, model_code_catalog,
                configuration_description,
                extras_description
        )

        return model_description

    def _get_exteriorcolorobjectandcode(self):

        exteriorcolor_object = None
        is_special_paint = False
        decoder = MplateDecoder(self)
        model_year = 0

        if self.paint_and_interior[0] == '5':
            exteriorcolor_code = self.paint_and_interior[-3:]
            is_special_paint = True
        else:
            exteriorcolor_code = self.paint_and_interior[:4]

        logger.info('Exterior color code: {}'.format(exteriorcolor_code))

        # Get the exterior color object from the M-plate
        # code
        exteriorcolor = ExteriorColor.objects.filter(
            plate_code=exteriorcolor_code
        )

        if not exteriorcolor:
            exteriorcolor_object = None
        elif exteriorcolor.count() > 1:
            model_year = decoder.get_model_year().year
            exteriorcolor = ExteriorColor.objects.filter(
                plate_code=exteriorcolor_code,
                years__contains=model_year,
            )
            exteriorcolor_object = exteriorcolor[0]
        else:
            exteriorcolor_object = exteriorcolor[0]

        if is_special_paint:
            exteriorcolor_code = self.paint_and_interior

        return exteriorcolor_object, exteriorcolor_code

    def get_exteriorcolor(self):
        color_name_roof = ""
        remarks = ""

        exteriorcolor, exteriorcolor_code = \
            self._get_exteriorcolorobjectandcode()
        if not exteriorcolor:
            exteriorcolor_description = \
                "{}: Unknown exterior color code".format(
                    exteriorcolor_code)
            return exteriorcolor_description

        lacquer_code_body = exteriorcolor.lacquer_code_body
        lacquer_code_roof = exteriorcolor.lacquer_code_roof

        color_body = Color.objects.filter(
            lacquer_code=exteriorcolor.lacquer_code_body
        )
        color_name_body = color_body[0].color_name

        if lacquer_code_roof:
            color_roof = Color.objects.filter(
                lacquer_code=exteriorcolor.lacquer_code_roof
            )
            color_name_roof = color_roof[0].color_name
        else:
            lacquer_code_roof = lacquer_code_body
            color_name_roof = color_name_body

        if exteriorcolor.remarks:
            remarks = '\nRemarks: {}'.format(
                exteriorcolor.remarks)

        exteriorcolor_description = '''Body: {} ({})
            Roof: {} ({}){}'''.format(
                color_name_body,
                lacquer_code_body,
                color_name_roof,
                lacquer_code_roof,
                remarks,
            )

        return exteriorcolor_description

    def _get_exteriorcolorchip(self):

        color_chip_body = ""

        # Get the exterior color object from the M-plate
        # code
        exteriorcolor, _ = self._get_exteriorcolorobjectandcode()

        if exteriorcolor:
            # Get the color attributes from the lacquer code
            color_body = Color.objects.filter(
                lacquer_code=exteriorcolor.lacquer_code_body
            )
            if color_body:
                # Get the color chip
                color_chip_body = color_body[0].chip

        return color_chip_body

    def get_interiorcolor(self):
        decoder = MplateDecoder(self)
        model_year = 0

        if not self.paint_and_interior[0] == '5':
            interiorcolor_code = self.paint_and_interior[-2:]

            interiorcolor = InteriorColor.objects.filter(
                plate_code=interiorcolor_code
            )

            if not interiorcolor:
                color_name = "({}) Unknown color".format(interiorcolor_code)
                material = "Unknown material"
            elif interiorcolor.count() > 1:
                model_year = decoder.get_model_year().year
                interiorcolor = InteriorColor.objects.filter(
                    plate_code=interiorcolor_code,
                    years__contains=model_year,
                )
                try:
                    color_name = interiorcolor[0].color_name
                    material = interiorcolor[0].material
                except IndexError:
                    color_name = (
                        "Error while fetching interior color code:"
                        " {}, year {}".format(interiorcolor_code), model_year)
                    material = ""

            else:
                color_name = interiorcolor[0].color_name
                material = interiorcolor[0].material

            interiorcolor_description = '{}, {}'.format(color_name, material)
        else:
            interiorcolor_description = ('No description available'
                                         ' for special paint jobs')

        return interiorcolor_description

    def get_engine(self):
        engine_code = self.aggregate_code[0]

        engine = Engine.objects.filter(
            engine_code=engine_code
        )

        engine_description = '{}, {}, {}'.format(
            engine[0].engine_type,
            engine[0].fuel_induction,
            engine[0].extra_specs)

        return engine_description

    def get_gearbox(self):
        gearbox_code = self.aggregate_code[1]

        gearbox = Gearbox.objects.filter(
            gearbox_code=gearbox_code
        )

        gearbox_description = '{}'.format(
            gearbox[0].gearbox_description,
        )

        return gearbox_description

    def render_plate(self):
        SVG_NAMESPACE = u"http://www.w3.org/2000/svg"
        decoder = MplateDecoder(self)
        model_year = decoder.get_model_year().year
        logger.info("Model year: {} {}".format(model_year, type(model_year)))
        if model_year in [1968, 1969]:
            svg_file = os.path.join(BASE_DIR, "mplate_decoder",
                                    "images/mplate-6869-ref.svg")
        else:
            svg_file = os.path.join(BASE_DIR, "mplate_decoder",
                                    "images/mplate-7079-ref.svg")
        MPLATE_STOP_COLOR_ID = 'stopBusColor'
        MPLATE_STOP_COLOR = '#a6a6a6'

        tree = etree.parse(svg_file)

        # Get all fields of an M-plate
        fields = [f.name for f in Mplate._meta.get_fields() if f.name != 'id']

        # Replace each field name with a matching id on the SVG file, with
        # its value
        for field in fields:
            mplate_field = tree.find(
                "//n:text[@id='{}']/n:tspan".format(field),
                namespaces={'n': SVG_NAMESPACE})
            mplate_field.text = getattr(self, field)

        color_chip_body = self._get_exteriorcolorchip()
        logger.info(color_chip_body)

        if color_chip_body:
            # Replace gradient color
            stop_color = tree.find(
                "//n:stop[@id='{}']".format(MPLATE_STOP_COLOR_ID),
                namespaces={'n': SVG_NAMESPACE}
            )

            stop_color.attrib['style'] = stop_color.attrib['style'].replace(
                MPLATE_STOP_COLOR, color_chip_body)

        plate = etree.tostring(tree).decode('utf-8')

        return plate


class MplateDecoder:

    _MODEL_YEAR_SERIAL_NR_SPLIT_AT = -6

    def __init__(self, mplate=None):
        self.mplate = mplate

    def get_model_year(self, chassis_number=None):

        if chassis_number:
            chassis_number = chassis_number
        elif self.mplate:
            chassis_number = self.mplate.chassis_number_short
        else:
            raise ValidationError(
                'MplateDecoder requires'
                ' an mplate or chassis_number')

        MODEL_6869_YEAR_CODE_LEN = 1
        MODEL_7079_YEAR_CODE_LEN = 2
        MODEL_YEAR_START = date(1950, 1, 1)
        model_year_decade = 0

        splitat = self._MODEL_YEAR_SERIAL_NR_SPLIT_AT
        model_year_code = chassis_number[:splitat]
        model_year_delta = int(chassis_number[0])

        if len(model_year_code) == MODEL_6869_YEAR_CODE_LEN:
            model_year_decade = 1
        elif len(model_year_code) == MODEL_7079_YEAR_CODE_LEN:
            model_year_decade = int(chassis_number[1])
        else:
            raise ValidationError(
                "Invalid model year"
                " code length: {}".format(len(model_year_code)))

        model_year = MODEL_YEAR_START.replace(
            year=MODEL_YEAR_START.year + ((10 * model_year_decade) +
                                          model_year_delta))

        return model_year

    def get_mcodes(self, m_codes_1=None, m_codes_2=None,
                   chassis_number_short=None):

        mcode_prepend = 'M '

        if m_codes_1 or m_codes_2:
            m_codes_1 = m_codes_1
            m_codes_2 = m_codes_2
        elif self.mplate:
            m_codes_1 = self.mplate.m_codes_1
            m_codes_2 = self.mplate.m_codes_2
        else:
            raise ValueError('MplateDecoder requires'
                             ' an mplate or mcodes_1/m_codes_2')

        if chassis_number_short:
            chassis_number_short = chassis_number_short
        elif self.mplate:
            chassis_number_short = self.mplate.chassis_number_short
        else:
            raise ValueError('MplateDecoder requires'
                             ' an mplate or chassis_number_short')

        model_year = self.get_model_year(chassis_number_short).year

        mcode_dict = {}
        m_codes = list(filter(None,
                       (re.split(r'\W+', m_codes_1) +
                           re.split(r'\W+', m_codes_2))))
        m_codes_expanded = []

        # First check if the M-code contains a collection of M-codes
        for m_code in m_codes:
            m_code_query_set = McodeCollection.objects.filter(
                m_code=m_code, years__contains=model_year)
            if m_code_query_set:
                m_code_collection = m_code_query_set[0].collection
                m_codes_expanded += \
                    list(filter(None,
                         (re.split(r'\W+', m_code_collection))))
            else:
                m_codes_expanded.append(m_code)

        # Retrieve the M-code description
        for m_code in m_codes_expanded:
            m_code_query_set = Mcode.objects.filter(m_code=m_code)

            if m_code_query_set:
                if m_code_query_set.count() > 1:
                    m_code_query_set = Mcode.objects.filter(
                        m_code=m_code, years__contains=model_year)
                try:
                    description = m_code_query_set[0].description
                    if m_code_query_set[0].is_special_code:
                        mcode_prepend = 'S '
                except IndexError:
                    description = (
                        "Error while fetching code:"
                        " {}, year {}".format(m_code, model_year))
            else:
                description = "Unknown code"

            mcode_dict[mcode_prepend + m_code] = description

        return mcode_dict


class ExportDestination(Model):
    export_code = models.CharField(max_length=3)
    export_destination = models.CharField(max_length=50)


class Type2Model(Model):
    model = models.PositiveSmallIntegerField()
    description = models.CharField(
        max_length=35,
        help_text=("Model description"))
    schematic = models.TextField(blank=True)


class Type2ModelConfiguration(Model):
    model = models.PositiveSmallIntegerField()
    configuration = models.PositiveSmallIntegerField()
    description = models.TextField()


class Type2ModelExtra(Model):
    model = models.PositiveSmallIntegerField()
    extras = models.PositiveSmallIntegerField()
    description = models.TextField()
    m_codes = models.CharField(
        max_length=50,
        help_text=("List of M-codes for the corresponding extras"),
        blank=True)
    chassis_plate = models.CharField(
        max_length=20,
        help_text=("Model description as it appears on the chassis plate"),
        blank=True)
    years = models.CharField(
            max_length=65, blank=True)


class InteriorColor(Model):
    plate_code = models.CharField(
            max_length=2)
    color_name = models.CharField(
            max_length=50)
    material = models.CharField(
            max_length=20)
    years = models.CharField(
            max_length=65, blank=True)
    remarks = models.TextField(blank=True)
    image = models.ImageField(blank=True)


class ExteriorColor(Model):
    plate_code = models.CharField(
            max_length=4)
    lacquer_code_body = models.CharField(
            max_length=20)
    lacquer_code_roof = models.CharField(
            max_length=20, blank=True)
    years = models.CharField(
            max_length=65, blank=True)
    sonderlackierung = models.BooleanField()
    remarks = models.TextField(blank=True)


class Color(Model):
    lacquer_code = models.CharField(
            max_length=30)
    color_name = models.CharField(
            max_length=75)
    ral_code = models.CharField(
            max_length=30, blank=True)
    chip = models.CharField(
            max_length=36, blank=True)


class Engine(Model):
    engine_code = models.PositiveSmallIntegerField()
    engine_type = models.CharField(
        max_length=6)
    fuel_induction = models.CharField(
        max_length=30)
    extra_specs = models.CharField(
        max_length=50, blank=True)
    m_codes = models.CharField(
        max_length=50,
        help_text=("List of M-codes for the corresponding extras"),
        blank=True)
    years = models.CharField(
        max_length=65,
        blank=True)


class Gearbox(Model):
    gearbox_code = models.PositiveSmallIntegerField()
    gearbox_description = models.CharField(
        max_length=35)
    m_codes = models.CharField(
        max_length=50,
        help_text=("List of M-codes for the corresponding extras"),
        blank=True)
    years = models.CharField(
        max_length=65,
        blank=True)


class Mcode(Model):
    m_code = models.CharField(
        max_length=3)
    description = models.TextField()
    model_type = models.CharField(max_length=30,
                                  blank=True)
    is_special_code = models.BooleanField(default=False)
    years = models.CharField(
        max_length=65,
        blank=True)
    remarks = models.TextField(blank=True)


class McodeCollection(Model):
    m_code = models.CharField(
        max_length=3)
    collection = models.TextField()
    years = models.CharField(
        max_length=65,
        blank=True)
    remarks = models.TextField(blank=True)
