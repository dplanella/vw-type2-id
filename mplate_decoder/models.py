import re
import logging
from datetime import date, datetime
from django.db.models import Model, Q
from django.db import models
from django.urls import reverse
from django.forms import ValidationError
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from django.conf import settings
from django.utils.translation import gettext as _
from isoweek import Week
from crum import get_current_user

logger = logging.getLogger(__name__)


class Mplate(Model):
    class Meta:
        ordering = ['-id']

    _decoder = None

    chassis_number_short = models.CharField(
        _("Shortened chassis number"),
        max_length=8, unique=True,
        help_text=_("Chassis number shortened, with the two leading digits "
                    "removed."))
    m_codes_1 = models.CharField(
        _("M-codes, row 1"),
        max_length=19, blank=True,
        help_text=_("Row 1 of M codes (max 5)"))
    m_codes_2 = models.CharField(
        _("M-codes, row 2"),
        max_length=19, blank=True,
        help_text=_("Row 2 of M codes (max 4 -mod. '70-'79 or "
                    "5 -mod. '68-'69-)"))
    paint_and_interior_code = models.CharField(
        _("Paint and interior"),
        max_length=6,
        help_text='Combined VW body/roof paint and interior codes')
    production_date_code = models.CharField(
        _("Production date"),
        max_length=3,
        help_text=_('Production date code'))
    production_planned = models.CharField(
        _("Production planning"),
        max_length=4, blank=True,
        help_text=_('Production planning code'))
    export_destination_code = models.CharField(
        _("Export destination"),
        max_length=3, blank=True,
        help_text=_('Export destination code'))
    model_code = models.CharField(
        _("Vehicle model"),
        max_length=4,
        help_text=_('Vehicle model code'))
    aggregate_code = models.CharField(
        _("Aggregate"),
        max_length=2,
        help_text=_('Engine and gearbox aggregate code'))
    emden = models.CharField(
        _("Emden"),
        max_length=1, blank=True,
        help_text=_('Optional "E" for Emden'))
    created_at = models.DateTimeField(
        auto_now_add=True, blank=True,
        null=True)
    updated_at = models.DateTimeField(
        auto_now=True, blank=True,
        null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        editable=False,
        blank=True, null=True, default=None)
    editor_remarks = models.TextField(
        blank=True)

    # Computed (decoded) fields
    m_codes = models.CharField(
        max_length=38, blank=True, editable=False,
        help_text=_("Full list of M codes for this M plate"))
    production_date_as_time = models.DateField(
        blank=True, editable=False,
        help_text=_("Planned production date, in time format"))
    model_year = models.CharField(
        max_length=4, blank=True, editable=False,
        help_text=_('Model year'))
    destination_country = models.CharField(
        max_length=30, blank=True,
        help_text=_("Country of destination"))

    def __unicode__(self):
        return self.chassis_number_short

    def get_absolute_url(self):
        '''
        Return the Mplate objects canonical URL. Required for the admin's
        "View on site" feature to work:
        https://docs.djangoproject.com/en/2.2/ref/models/instances/#get-absolute-url
        '''
        return reverse(
            'mplate_decoder:mplate_retrieve',
            kwargs={'chassis_number_short': self.chassis_number_short})

    @property
    def decoder(self):
        '''
        Return the object used to decode all the various M-plate codes
        '''
        if not self._decoder:
            decoder = MplateDecoder(self)
        else:
            decoder = self._decoder

        return decoder

    @property
    def serial_production_number(self):
        '''
        Return the bus' 6-digit serial production number
        '''
        _MODEL_YEAR_SERIAL_NR_SPLIT_AT = -6
        splitat = _MODEL_YEAR_SERIAL_NR_SPLIT_AT
        serial_number = int(self.chassis_number[splitat:])

        return serial_number

    @property
    def chassis_number(self):
        '''
        Return the bus' full chassis (VIN) number
        '''
        type_body = self.model_code[:2]

        return type_body + self.chassis_number_short

    @property
    def model(self):
        '''
        Decoded vehicle model object
        '''
        return self.decoder.decode_model()

    @property
    def exteriorcolor_code(self):
        return self.decoder.get_exteriorcolor_code()

    @property
    def export_destination(self):
        return self.decoder.decode_export_destination()

    @property
    def exteriorcolor(self):
        return self.decoder.decode_exteriorcolor()

    def describe_model(self):
        return self.decoder.describe_model()

    def describe_export_destination(self):
        return self.decoder.describe_export_destination()

    def describe_export_destination_country(self, with_port=True):
        return self.decoder.describe_export_destination_country(with_port)

    def describe_exteriorcolor(self):
        return self.decoder.describe_exteriorcolor()

    def _decode_model_year(self):
        '''Used to compute property before saving'''
        return self.decoder.decode_model_year()

    def _decode_production_date(self):
        '''Used to compute property before saving'''
        return self.decoder.decode_production_date()

    def _get_exteriorcolorchip(self):

        color_chip_body = ""
        color_chip_roof = ""

        # Get the exterior color object from the M-plate
        # code
        exteriorcolor = self.exteriorcolor

        if exteriorcolor:
            try:
                # Get the color attributes from the lacquer code
                color_body = Color.objects.get(
                    lacquer_code=exteriorcolor.lacquer_code_body
                )
                # Get the color chip
                color_chip_body = color_body.chip
            except ObjectDoesNotExist:
                logger.warning('Body color chip does not exist')
                color_chip_body = ""

            try:
                # Get the color attributes from the lacquer code
                color_roof = Color.objects.get(
                    lacquer_code=exteriorcolor.lacquer_code_roof
                )
                # Get the color chip
                color_chip_roof = color_roof.chip
            except ObjectDoesNotExist:
                logger.warning('Body color chip does not exist')
                color_chip_roof = ""

        return (color_chip_body, color_chip_roof)

    def describe_interiorcolor(self):
        SPECIAL_PAINTJOB_ID = '5'
        model_year = 0

        if not self.paint_and_interior_code.startswith(SPECIAL_PAINTJOB_ID):
            interiorcolor_code = self.paint_and_interior_code[-2:]

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
            logger.error(engine_description)

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

    def save(self, *args, **kwargs):

        # Calculate the full m_codes field
        self.m_codes = f"{self.m_codes_1} {self.m_codes_2}"

        # Calculate model year
        self.model_year = self._decode_model_year()

        # Calculate production date
        self.production_date_as_time = self._decode_production_date()

        # Calculate destination country
        self.destination_country = \
            self.describe_export_destination_country(with_port=False)

        # Calculate owner
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

    def _get_value_or_mplate(self, attribute_name, value=None):
        if value:
            value = value
            logger.debug(
                f'Passed {attribute_name}: {value}')
        elif self.mplate:
            value = getattr(self.mplate, attribute_name)
            logger.debug(
                f'M-plate {attribute_name}: {value}')
        else:
            raise ValidationError(
                'MplateDecoder requires'
                f' an mplate or {attribute_name}')

        return value

    def get_exteriorcolor_code(self, paint_and_interior_code=None):
        '''
        Extracts the exterior color code from the paint and interior code.
        Depending on the model year and the special paintjob ID, the
        resulting code will be either a 3-digit or 4-digit one.

        - From 1968-71: regular codes are 4 digits. Special paint jobs
          start with '5' and are 3 digits.
        - From 1972-79: all codes are 4-digit ones. Special paint jobs
          start with '9'.
        '''

        # 1968-71 special paint job marker. It also indicates that it
        # is a 3-digit code
        SPECIAL_PAINTJOB_ID = '5'

        paint_and_interior_code = self._get_value_or_mplate(
            f'{paint_and_interior_code=}'.split('=')[0],
            paint_and_interior_code
        )

        if paint_and_interior_code.startswith(SPECIAL_PAINTJOB_ID):
            exteriorcolor_code = paint_and_interior_code[-3:]
        else:
            exteriorcolor_code = paint_and_interior_code[:4]

        return exteriorcolor_code

    def decode_model(self, model_code=None, model_year=None, m_codes=None):
        special_sales_m_codes = ['736', '723', 'D61', 'D63', 'D64', 'W51']
        # - Wild Westerner is 736, year 1973
        #   - Model 2211
        #   - Model 2215
        # - Champaigne ed. I is 723 (D09), year 1977 (seven-seater)
        #   - Model 2218
        # - Champaigne ed. II is 765 (D61, D63, D64), year 1978
        #   (seven-seater or Campmobile)
        #   - Model 2218 (D61)
        #   - Model 2319 (D63)
        # - Silverfish is 766 (W51), years 1978-1979 (nine-seater)
        #   - Model 2210
        t2_model = None

        if model_code:
            model_code = model_code
        elif self.mplate:
            model_code = self.mplate.model_code
        else:
            raise ValueError('MplateDecoder requires'
                             ' an mplate or model code')

        model = int(model_code[:2])
        configuration = int(model_code[2])
        extras = int(model_code[3])

        if model_year:
            model_year = model_year
        elif self.mplate:
            model_year = self.mplate.model_year
        else:
            raise ValueError('MplateDecoder requires'
                             ' an mplate or model year')
        if m_codes:
            m_codes = m_codes
        elif self.mplate:
            m_codes = self.mplate.m_codes.split()
        else:
            raise ValueError('MplateDecoder requires'
                             ' an mplate or M codes')

        logger.debug(
            f'Getting model {model}{configuration}{extras}, '
            f'model year {model_year}, M-codes: {m_codes}')

        model_query = Q(model=model) \
            & Q(configuration=configuration) \
            & Q(extras=extras) \
            & Q(years__icontains=model_year)

        try:
            t2_model = VwType2Model.objects.get(model_query)
            logger.debug(
                f'Model {t2_model.model}, years {t2_model.years}, '
                f'M-codes: {t2_model.m_codes}')
        except ObjectDoesNotExist:
            logger.error(
                f'Does not exist: Model {model_code}, years {model_year}, '
                f'M-codes: {m_codes}')
        except MultipleObjectsReturned:
            logger.debug(
                f'Multiple objects: Model {model_code}, years {model_year}, '
                f'M-codes: {m_codes}')

            m_codes_query = Q()

            if any(x in m_codes for x in special_sales_m_codes):
                # If the M-plate contains any special sales M-codes
                # use all special sales M-codes in the query
                logger.debug("Special sales M-code")
                for m_code in special_sales_m_codes:
                    m_codes_query |= Q(m_codes__icontains=m_code)
                model_query &= m_codes_query
            else:
                # If the M-plate does not contain any special sales M-codes
                # use all of the M-plate's M-codes in the query
                logger.debug("Not special sales M-code")
                for m_code in m_codes:
                    m_codes_query |= Q(m_codes__icontains=m_code)
                model_query |= m_codes_query

            try:
                t2_model = VwType2Model.objects.get(model_query)
                logger.debug(
                    f'Model {t2_model.model}, years {t2_model.years}, '
                    f'M-codes: {t2_model.m_codes}')
            except ObjectDoesNotExist:
                logger.error(
                    'Does not exist: '
                    f'Model {model_code}, years {model_year}, '
                    f'M-codes: {m_codes}')
            except MultipleObjectsReturned:
                logger.error(
                    'Multiple objects: '
                    f'Model {model_code}, years {model_year}, '
                    f'M-codes: {m_codes}')
                # Fall back to a model
                t2_model = VwType2Model.objects.filter(model_query)[0]

        return t2_model

    def describe_model(self):
        model_description_dict = {}

        t2_model = self.decode_model()
        model_code_catalog = \
            f'{t2_model.model}{t2_model.configuration}'

        model_description_dict['model_description'] = \
            t2_model.model_description
        model_description_dict['model_code_catalog'] = \
            model_code_catalog
        model_description_dict['configuration_description'] = \
            t2_model.configuration_description
        model_description_dict['extras_description'] = \
            t2_model.extras_description

        return model_description_dict

    def decode_model_year(self, chassis_number_short=None):

        chassis_number_short = self._get_value_or_mplate(
            f'{chassis_number_short=}'.split('=')[0],
            chassis_number_short
        )

        MODEL_6869_YEAR_CODE_LEN = 1
        MODEL_7079_YEAR_CODE_LEN = 2
        MODEL_YEAR_START = date(1950, 1, 1)
        model_year_decade = 0

        splitat = self._MODEL_YEAR_SERIAL_NR_SPLIT_AT
        model_year_code = chassis_number_short[:splitat]
        model_year_delta = int(chassis_number_short[0])

        if len(model_year_code) == MODEL_6869_YEAR_CODE_LEN:
            model_year_decade = 1
        elif len(model_year_code) == MODEL_7079_YEAR_CODE_LEN:
            model_year_decade = int(chassis_number_short[1])
        else:
            raise ValidationError(
                "Invalid model year "
                f"code length: {len(model_year_code)}, "
                f"code {model_year_code}, "
                f"chassis no. {chassis_number_short}")

        model_year = MODEL_YEAR_START.replace(
            year=MODEL_YEAR_START.year + ((10 * model_year_decade) +
                                          model_year_delta))

        return model_year.year

    def decode_production_date(
            self, chassis_number=None,
            encoded_production_date=None):

        if chassis_number and encoded_production_date:
            chassis_number = chassis_number
            encoded_production_date = encoded_production_date
        elif self.mplate:
            chassis_number = self.mplate.chassis_number_short
            encoded_production_date = self.mplate.production_date_code
        else:
            raise ValidationError(
                'MplateDecoder requires either'
                ' an m-plate or chassis_number with encoded production date')

        # Model year starts in August
        MODEL_YEAR_START_MONTH = 8
        model_year = self.decode_model_year(chassis_number)
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

    def decode_mcodes(self, m_codes_1=None, m_codes_2=None,
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

        model_year = self.decode_model_year(chassis_number_short)

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
            mcode_prepend = 'M'
            m_code_query_set = None

            try:
                # We query with get() first, as not all M-codes
                # contain their year
                m_code_query_set = Mcode.objects.get(m_code=m_code)
                if m_code_query_set.years:
                    # But we make sure that if the year is defined
                    # we check for it
                    raise MultipleObjectsReturned
            except ObjectDoesNotExist:
                # There is no such a code in the database
                error_description = f"Unknown code, year {model_year}"
            except MultipleObjectsReturned:
                m_code_query_set = Mcode.objects.filter(
                        m_code=m_code, years__contains=model_year)
                try:
                    m_code_query_set = m_code_query_set[0]
                except IndexError:
                    m_code_query_set = None
                    error_description = \
                        f"Undefined code, year {model_year}"

            if m_code_query_set:
                description = m_code_query_set.description
                if m_code_query_set.is_special_code:
                    mcode_prepend = 'S'
            else:
                # There is no m-code on the database to read
                # or there has been an error. Have a guess at
                # whether it's an S-code
                description = error_description
                if m_code.startswith('7'):
                    try:
                        if int(m_code) in range(700, 800):
                            mcode_prepend = 'S'
                    except ValueError:
                        logger.warning(
                            f'Probably an invalid M-code: '
                            f'{m_code}, M-plate {chassis_number_short}')

            mcode_dict[f"{mcode_prepend} {m_code}"] = description

        return mcode_dict

    def decode_export_destination(self, export_destination_code=None):
        '''
        Return the ExportDestination object corresponding to the M-plate's
        export code. Return None if code is not in the database.
        '''

        export_destination_code = self._get_value_or_mplate(
            f'{export_destination_code=}'.split('=')[0],
            export_destination_code
        )

        try:
            destination = ExportDestination.objects.get(
                export_code=export_destination_code)
        except ObjectDoesNotExist:
            logger.warning(
                f'Unknown export destination code: '
                f'{export_destination_code}, ')
            destination = None

        return destination

    def describe_export_destination(self, export_destination_code=None):
        '''
        Return a description of the export destination for display purposes.
        The destination may include a purpose or a location (e.g. dealer, city)
        but otherwise will not contain any other geographical information.
        '''

        export_destination_code = self._get_value_or_mplate(
            f'{export_destination_code=}'.split('=')[0],
            export_destination_code
        )

        # If the export destination code was submitted
        if export_destination_code:
            export_destination = self.decode_export_destination()

            if export_destination:
                destination_description = export_destination.destination
            else:
                # The export code is not on the database
                destination_description = \
                    f"Unknown ({export_destination_code})"
        else:
            # The export code hasn't been specified on M-plate form submission
            destination_description = "Not specified"

        logger.debug(f'Export destination desc.: {destination_description}')

        return destination_description

    def describe_export_destination_country(self, export_destination_code=None,
                                            with_port=True):
        '''
        Return a description of the export country or region for display
        purposes.
        The destination may include a country, region and port/city of entry.
        '''

        export_destination_code = self._get_value_or_mplate(
            f'{export_destination_code=}'.split('=')[0],
            export_destination_code
        )

        if export_destination_code:
            export_destination = self.decode_export_destination()

            if export_destination:
                if export_destination.country:
                    destination_country_description = \
                        export_destination.country
                elif (export_destination.region and
                      not export_destination.country):
                    destination_country_description = export_destination.region
                else:
                    destination_country_description = \
                        "Undefined country or region"

                if with_port:
                    if (export_destination.region and
                            export_destination.country):
                        destination_country_description += \
                            f", {export_destination.region}"
                    if export_destination.port:
                        destination_country_description += \
                            f" via {export_destination.port}"
                    elif export_destination.city:
                        destination_country_description += \
                            f" via {export_destination.city}"
            else:
                # The export code is not on the database
                destination_country_description = \
                    f"Unknown ({export_destination_code})"
        else:
            # The export code hasn't been specified on M-plate form submission
            destination_country_description = "Not specified"

        logger.debug(f'Export destination country desc.:'
                     f' {destination_country_description}')

        return destination_country_description

    def decode_exteriorcolor(self, model_year=None, exteriorcolor_code=None):

        SPECIAL_PAINTJOB_CODE_LEN = 3
        exteriorcolor_object = None
        model_year = 0

        exteriorcolor_code = self._get_value_or_mplate(
            f'{exteriorcolor_code=}'.split('=')[0],
            exteriorcolor_code
        )

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
            model_year = self._get_value_or_mplate(
                f'{model_year=}'.split('=')[0],
                model_year
            )
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
            exteriorcolor_code = self.paint_and_interior_code

        return exteriorcolor_object

    def describe_exteriorcolor(self, model_year=None, exteriorcolor_code=None):
        color_name_roof = ""
        remarks = ""

        exteriorcolor_code = self._get_value_or_mplate(
            f'{exteriorcolor_code=}'.split('=')[0],
            exteriorcolor_code
        )
        exteriorcolor = self.decode_exteriorcolor(model_year,
                                                  exteriorcolor_code)

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


class ExportDestination(Model):
    export_code = models.CharField(max_length=3)
    destination = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    region = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50, blank=True)
    port = models.CharField(max_length=50, blank=True)
    notes = models.CharField(max_length=50, blank=True)
    editor_remarks = models.TextField(blank=True)


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
    editor_remarks = models.TextField(blank=True)


class Color(Model):
    lacquer_code = models.CharField(
            max_length=30)
    color_name = models.CharField(
            max_length=75)
    ral_code = models.CharField(
            max_length=30, blank=True)
    chip = models.CharField(
            max_length=36, blank=True)
    editor_remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.lacquer_code}, {self.color_name}"


class ExteriorColor(Model):
    plate_code = models.CharField(
            max_length=4)
    lacquer_code_body = models.CharField(
            max_length=20)
    lacquer_code_roof = models.CharField(
            max_length=20, blank=True)
    lacquer_code_body_link = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        related_name='lacquer_code_body',
        null=True,
    )
    lacquer_code_roof_link = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        related_name='lacquer_code_roof',
        blank=True,
        null=True,
    )
    years = models.CharField(
            max_length=65, blank=True)
    sonderlackierung = models.BooleanField()
    remarks = models.TextField(blank=True)
    editor_remarks = models.TextField(blank=True)


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
    editor_remarks = models.TextField(blank=True)


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
    collection = models.TextField(blank=True)
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


class VwType2Model(Model):
    model = models.PositiveSmallIntegerField()
    configuration = models.PositiveSmallIntegerField()
    extras = models.PositiveSmallIntegerField()
    model_description = models.CharField(
        max_length=35,
        help_text=("Model description"))
    configuration_description = models.TextField()
    extras_description = models.TextField()
    m_codes = models.CharField(
        max_length=100,
        help_text=("List of M-codes for the corresponding extras"),
        blank=True)
    chassis_plate = models.CharField(
        max_length=20,
        help_text=("Model description as it appears on the chassis plate"),
        blank=True)
    years = models.CharField(
            max_length=65, blank=True)
    schematic_vector = models.TextField(blank=True)
    editor_remarks = models.TextField(blank=True)
