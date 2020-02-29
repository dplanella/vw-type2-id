import re
import os
import logging
from datetime import date, datetime
from django.db.models import Model
from django.db import models
from django.urls import reverse
from django.forms import ValidationError
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from lxml import etree
from isoweek import Week
from vw_type2_id.settings import BASE_DIR
from users.models import CustomUser
from crum import get_current_user

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
        max_length=19, blank=True,
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
    owner = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        editable=False,
        blank=True, null=True, default=None)

    # Computed (decoded) fields
    m_codes = models.CharField(
        max_length=38, blank=True, editable=False,
        help_text="Full list of M codes for this M plate")
    production_date_as_time = models.DateField(
        blank=True, editable=False,
        help_text="Planned production date, in time format")
    model_year = models.CharField(
        max_length=4, blank=True, editable=False,
        help_text='Model year')

    def __unicode__(self):
        return self.chassis_number_short

    def get_absolute_url(self):
        return reverse(
            'mplate_decoder:mplate_retrieve',
            kwargs={'chassis_number_short': self.chassis_number_short})

    def get_model_year(self):
        decoder = MplateDecoder(self)
        model_year = decoder.get_model_year()

        return model_year

    def get_serial_production_number(self):
        splitat = self._MODEL_YEAR_SERIAL_NR_SPLIT_AT
        serial_number = int(self.chassis_number[splitat:])

        return serial_number

    def get_chassis_number(self):
        type_body = self.model[:2]

        return type_body + self.chassis_number_short

    def get_production_date(self):

        decoder = MplateDecoder(self)
        production_date = decoder.get_production_date()

        return production_date

    def get_export_destination_object(self):
        '''
        Return the ExportDestination object corresponding to the M-plate's
        export code. Return None if code is not in the database.
        '''
        try:
            destination = ExportDestination.objects.get(
                export_code=self.export_destination)
        except ObjectDoesNotExist:
            destination = None

        return destination

    def get_export_destination(self):
        '''
        Return a description of the export destination for display purposes.
        The destination may include a purpose or a location (e.g. dealer, city)
        but otherwise will not contain any other geographical information.
        '''
        export_code = self.export_destination
        export_destination = self.get_export_destination_object()

        if export_code:
            if export_destination:
                destination_description = f"{export_destination.destination}"
                # Destinations in Germany have a 3-digit export code. If it
                # is a German destination, show the city as well.
                if len(export_code) == 3 and export_destination.city:
                    destination_description += f", {export_destination.city}"
            else:
                # The export code is not on the database
                destination_description = f"Unknown ({export_code})"
        else:
            # The export code hasn't been specified on M-plate form submission
            destination_description = "Not specified"

        return destination_description

    def get_export_destination_geo(self):
        '''
        Return a description of the export country or region for display
        purposes.
        The destination may include a country, region and port/city of entry.
        '''
        export_code = self.export_destination
        export_destination = self.get_export_destination_object()

        if export_code:
            if export_destination:
                if export_destination.country:
                    destination_geo_description = \
                        f"{export_destination.country}"
                elif (export_destination.region and
                      not export_destination.country):
                    destination_geo_description = \
                        f"{export_destination.region}"
                else:
                    destination_geo_description = "Undefined country or region"
                # Destinations in Germany have a 3-digit export code. If it
                # not is a German destination, show the rest of geographical
                # info.
                if len(export_code) < 3:
                    if (export_destination.region and
                            export_destination.country):
                        destination_geo_description += \
                            f", {export_destination.region}"
                    if export_destination.port:
                        destination_geo_description += \
                            f" via {export_destination.port}"
                    elif export_destination.city:
                        destination_geo_description += \
                            f" via {export_destination.city}"
            else:
                # The export code is not on the database
                destination_geo_description = f"Unknown ({export_code})"
        else:
            # The export code hasn't been specified on M-plate form submission
            destination_geo_description = "Not specified"

        return destination_geo_description

    def get_model(self):
        model_code = self.model[:2]
        configuration_code = self.model[2]
        extras_code = self.model[3]
        model_code_catalog = self.model[:3]
        model_year = self.model_year

        try:
            model = Type2Model.objects.get(
                model=model_code
            )
            model_description = model.description
        except ObjectDoesNotExist:
            model_description = "Model description unavailable"

        try:
            configuration = Type2ModelConfiguration.objects.get(
                model=model_code, configuration=configuration_code
            )
            configuration_description = configuration.description
        except ObjectDoesNotExist:
            configuration_description = "Configuration description unavailable"

        try:
            # Most of the configurations are single objects, and
            # not all of them have a year model defined
            extras = Type2ModelExtra.objects.get(
                model=model_code, extras=extras_code,
            )
            extras_description = extras.description
        except ObjectDoesNotExist:
            extras_description = "Extras description unavailable"
        except MultipleObjectsReturned:
            extras = Type2ModelExtra.objects.filter(
                model=model_code, extras=extras_code,
                years__contains=model_year,
            )
            if extras:
                extras_description = extras.first().description
            else:
                extras_description = (
                    "No model extras found for model"
                    " {}, extras code {}, year {}".format(
                        model_code, extras_code, model_year))

        model_description = '''Volkswagen Type 2
            · {} (model {})
            · {}
            · {}'''.format(
                model_description, model_code_catalog,
                configuration_description,
                extras_description
        )

        return model_description

    def _get_exteriorcolor_code(self):
        SPECIAL_PAINTJOB_ID = '5'

        if self.paint_and_interior.startswith(SPECIAL_PAINTJOB_ID):
            exteriorcolor_code = self.paint_and_interior[-3:]
        else:
            exteriorcolor_code = self.paint_and_interior[:4]

        return exteriorcolor_code

    def _get_exteriorcolorobject(self):

        SPECIAL_PAINTJOB_CODE_LEN = 3
        exteriorcolor_object = None
        model_year = 0

        exteriorcolor_code = self._get_exteriorcolor_code()

        try:
            # Get the exterior color object from the M-plate
            # code
            exteriorcolor = ExteriorColor.objects.get(
                plate_code=exteriorcolor_code
            )
            exteriorcolor_object = exteriorcolor
        except ObjectDoesNotExist:
            exteriorcolor_object = None
        except MultipleObjectsReturned:
            model_year = self.model_year
            exteriorcolor = ExteriorColor.objects.filter(
                plate_code=exteriorcolor_code,
                years__contains=model_year,
            )
            if exteriorcolor:
                exteriorcolor_object = exteriorcolor[0]
            else:
                # If there is no match by model year,
                # simply return the first result
                exteriorcolor_object = ExteriorColor.objects.filter(
                    plate_code=exteriorcolor_code).first()

        if exteriorcolor_code == SPECIAL_PAINTJOB_CODE_LEN:
            exteriorcolor_code = self.paint_and_interior

        return exteriorcolor_object

    def get_exteriorcolor_description(self):
        color_name_roof = ""
        remarks = ""

        exteriorcolor_code = self._get_exteriorcolor_code()
        exteriorcolor = self._get_exteriorcolorobject()

        if not exteriorcolor:
            exteriorcolor_description = \
                "{}: Unknown exterior color code".format(
                    exteriorcolor_code)
            return exteriorcolor_description

        try:
            color_body = Color.objects.get(
                lacquer_code=exteriorcolor.lacquer_code_body
            )
            color_name_body = color_body.color_name
        except ObjectDoesNotExist:
            color_name_body = "Unknown color ({})".format(
                exteriorcolor.lacquer_code_body)

        lacquer_code_roof = exteriorcolor.lacquer_code_roof
        if lacquer_code_roof:
            try:
                color_roof = Color.objects.get(
                    lacquer_code=exteriorcolor.lacquer_code_roof
                )
                color_name_roof = color_roof.color_name
            except ObjectDoesNotExist:
                color_name_roof = "Unknown color ({})".format(
                    exteriorcolor.lacquer_code_roof)
        else:
            lacquer_code_roof = exteriorcolor.lacquer_code_body
            color_name_roof = color_name_body

        if exteriorcolor.remarks:
            remarks = '\nRemarks: {}'.format(
                exteriorcolor.remarks)

        exteriorcolor_description = '''Body: {} ({})
            Roof: {} ({})'''.format(
                color_name_body,
                exteriorcolor.lacquer_code_body,
                color_name_roof,
                lacquer_code_roof,
            )

        if remarks:
            exteriorcolor_description += '\n' + remarks

        return exteriorcolor_description

    def _get_exteriorcolorchip(self):

        color_chip_body = ""

        # Get the exterior color object from the M-plate
        # code
        exteriorcolor = self._get_exteriorcolorobject()

        if exteriorcolor:
            try:
                # Get the color attributes from the lacquer code
                color_body = Color.objects.get(
                    lacquer_code=exteriorcolor.lacquer_code_body
                )
                # Get the color chip
                color_chip_body = color_body.chip
            except ObjectDoesNotExist:
                color_chip_body = ""

        return color_chip_body

    def get_interiorcolor(self):
        SPECIAL_PAINTJOB_ID = '5'
        model_year = 0

        if not self.paint_and_interior.startswith(SPECIAL_PAINTJOB_ID):
            interiorcolor_code = self.paint_and_interior[-2:]

            try:
                interiorcolor = InteriorColor.objects.get(
                    plate_code=interiorcolor_code
                )
                color_name = interiorcolor.color_name
                material = interiorcolor.material
            except ObjectDoesNotExist:
                color_name = "({}) Unknown color".format(interiorcolor_code)
                material = "Unknown material"
            except MultipleObjectsReturned:
                model_year = self.model_year
                interiorcolor = InteriorColor.objects.filter(
                    plate_code=interiorcolor_code,
                    years__contains=model_year,
                )
                if interiorcolor:
                    color_name = interiorcolor.first().color_name
                    material = interiorcolor.first().material
                else:
                    color_name = (
                        "Error while fetching interior color code:"
                        " {}, year {}".format(interiorcolor_code, model_year))
                    material = ""

            interiorcolor_description = '{}, {}'.format(color_name, material)
        else:
            interiorcolor_description = ('No description available'
                                         ' for special paint jobs')

        return interiorcolor_description

    def get_engine(self):
        engine_code = self.aggregate_code[0]

        try:
            engine = Engine.objects.get(
                engine_code=engine_code
            )
            engine_description = '{}, {}'.format(
                engine.engine_type,
                engine.fuel_induction,
            )
            if engine.extra_specs:
                engine_description += ", " + engine.extra_specs

        except ObjectDoesNotExist:
            engine_description = "Unavailable engine description"

        return engine_description

    def get_gearbox(self):
        gearbox_code = self.aggregate_code[1]

        try:
            gearbox = Gearbox.objects.get(
                gearbox_code=gearbox_code
            )
            gearbox_description = '{}'.format(
                gearbox.gearbox_description,
            )
        except ObjectDoesNotExist:
            gearbox_description = "Unavailable transmission description"

        return gearbox_description

    def render_plate(self):
        SVG_NAMESPACE = u"http://www.w3.org/2000/svg"
        model_year = self.model_year
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
        fields = [f.name for f in Mplate._meta.get_fields()
                  if (f.name != 'id' and f.editable)]

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

    def save(self, *args, **kwargs):

        # Calculate the full m_codes field
        self.m_codes = \
            f"{self.m_codes_1} {self.m_codes_2}"

        # Calculate model year
        self.model_year = \
            self.get_model_year()

        # Calculate production date
        date = self.get_production_date()
        self.production_date_as_time = date

        # Get currently logged in user
        user = get_current_user()
        if user and not user.pk:
            user = None

        # Save the user as the owner only if
        # the M-plate is being created (added),
        # but NOT when it's being updated
        is_new = self._state.adding
        if is_new:
            self.owner = user

        super().save(*args, **kwargs)


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

        return model_year.year

    def get_production_date(
            self, chassis_number=None,
            encoded_production_date=None):

        if chassis_number and encoded_production_date:
            chassis_number = chassis_number
            encoded_production_date = encoded_production_date
        elif self.mplate:
            chassis_number = self.mplate.chassis_number_short
            encoded_production_date = self.mplate.production_date
        else:
            raise ValidationError(
                'MplateDecoder requires either'
                ' an m-plate or chassis_number with encoded production date')

        # Model year starts in August
        MODEL_YEAR_START_MONTH = 8
        model_year = self.get_model_year(chassis_number)
        production_date = None

        # Model year is 68-69
        if model_year < 1970:
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

            year = model_year
            try:
                day = encoded_production_date[:2]
                day = int(day)
            except ValueError as e:
                logger.error(
                    f'Could not decode production day {day}'
                    f' for chassis number {chassis_number}: {e}')
                return datetime.now()

            try:
                month = encoded_production_date[-1:]
                month = month_dict[month]
            except KeyError as e:
                logger.error(
                    f'Could not decode production month {month}'
                    f' for chassis number {chassis_number}: {e}')
                return datetime.now()

            if month >= MODEL_YEAR_START_MONTH:
                year = model_year - 1

            try:
                production_date = datetime(year, month, day).date()
            except ValueError as e:
                logger.error(
                    f'Could not decode production'
                    f' date {encoded_production_date}'
                    f' for chassis number {chassis_number}: {e}')
                return datetime.now()
        else:
            iso_year = model_year
            iso_weeknumber = int(encoded_production_date[:2])
            iso_weekday = int(encoded_production_date[-1:])

            first_model_year_weeks = {
                1969: "1969W12",
                1970: "1970W29",
                1971: "1970W32",
                1972: "1971W34",
                1973: "1972W34",
                1974: "1973W33",
                1975: "1974W33",
                1976: "1975W28",
                1977: "1976W28",
                1978: "1977W30",
                1979: "1978W28",
            }

            first_model_year_week = Week.fromstring(
                first_model_year_weeks[iso_year])

            if iso_weeknumber >= first_model_year_week.week:
                week_offset = iso_weeknumber - first_model_year_week.week
            else:
                week_offset = ((52 + iso_weeknumber)
                               - first_model_year_week.week)

            production_week = first_model_year_week + week_offset
            production_date = production_week.day(iso_weekday - 1)

        return production_date

    def get_mcodes(self, m_codes_1=None, m_codes_2=None,
                   chassis_number_short=None):

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

        model_year = self.get_model_year(chassis_number_short)

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
            mcode_prepend = 'M '

            try:
                # We query with get() first, as not all M-codes
                # contain their year
                m_code_query_set = Mcode.objects.get(m_code=m_code)
                description = m_code_query_set.description
            except ObjectDoesNotExist:
                description = f"Unknown code, year {model_year}"
            except MultipleObjectsReturned:
                m_code_query_set = Mcode.objects.filter(
                        m_code=m_code, years__contains=model_year)
                try:
                    description = m_code_query_set[0].description
                    if m_code_query_set[0].is_special_code:
                        mcode_prepend = 'S '
                except IndexError:
                    description = \
                        f"Undefined code for year {model_year}"

            mcode_dict[mcode_prepend + m_code] = description

        return mcode_dict


class ExportDestination(Model):
    export_code = models.CharField(max_length=3)
    destination = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    region = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    port = models.CharField(max_length=50, blank=True)
    notes = models.CharField(max_length=50, blank=True)


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
    source = models.TextField(blank=True)
    editor_remarks = models.TextField(blank=True)


class McodeCollection(Model):
    m_code = models.CharField(
        max_length=3)
    collection = models.TextField()
    years = models.CharField(
        max_length=65,
        blank=True)
    remarks = models.TextField(blank=True)
    source = models.TextField(blank=True)
    editor_remarks = models.TextField(blank=True)
