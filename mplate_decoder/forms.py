from django.forms import ModelForm, ValidationError
from django.urls import reverse
import re
from django.utils.text import slugify
from .models import (
    Mplate, Type2Model, Engine, Gearbox, MplateDecoder,
)

import logging
logger = logging.getLogger(__name__)


class MplateCreateForm(ModelForm):

    class Meta:
        model = Mplate
        fields = (
            'chassis_number_short',
            'm_codes_1',
            'm_codes_2',
            'paint_and_interior',
            'production_date',
            'production_planned',
            'export_destination',
            'model',
            'aggregate_code',
            'emden',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.saved_data = {}

    # For each field in the form (in the order they are declared in the form
    # definition),
    # 1. the Field.clean() method (or its override) is run,
    # 2. then clean_<fieldname>().
    # 3. Finally, once those two methods are run for every field, the
    #    Form.clean() method, or its override, is executed whether or not the
    #    previous methods have raised errors.

    # Validate each one of the fields:
    # https://docs.djangoproject.com/en/dev/ref/forms/validation/#django.forms.Form.clean
    # https://docs.djangoproject.com/en/dev/topics/forms/modelforms/#validation-on-a-modelform

    def clean_chassis_number_short(self):
        MODEL_6869_YEAR_CHASSIS_NR_LEN = 7
        MODEL_7079_YEAR_CHASSIS_NR_LEN = 8
        data = self.cleaned_data['chassis_number_short']
        decoder = MplateDecoder()

        # 1. Check for correct length
        if len(data) < MODEL_6869_YEAR_CHASSIS_NR_LEN:
            raise ValidationError(
                "Minimum digits: "
                "{} (mod. 68-68) or {} digits (mod. 70-79)".format(
                    MODEL_6869_YEAR_CHASSIS_NR_LEN,
                    MODEL_7079_YEAR_CHASSIS_NR_LEN
                ))

        # 2. Check for correct format
        if not re.match("^[0-9]{7,8}$", data):
            raise ValidationError(
                "Only digits allowed, without spaces. "
                "The second digit is always a 2."
            )

        # 3. Check for correctly decoded model year
        # Raises ValidationError if no valid chassis number
        # is provided, or if the length is invalid
        try:
            model_year = decoder.get_model_year(data)
        except ValidationError:
            raise ValidationError(
                "Invalid shortened chassis number. "
                "Check first digit."
            )

        logger.info(
            "Model year validation: {} ({})".format(
                model_year, type(model_year)))

        # 4. Check for correct range
        if model_year not in range(1968, 1980):
            raise ValidationError(
                "Invalid shortened chassis number. "
                "Check first and second digits."
            )

        # 5. Convert string to URL slug
        data = slugify(data)

        # There are two paths here:
        # 1. When creating a new M-Plate (Mplate instance does not exist)
        # 2. When updating an existing M-plate (Mplate instance exists)

        qs = Mplate.objects.filter(chassis_number_short=data)

        # If it already exists in the database
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
            logger.info(f"Data after exclude: {data}")

        if qs.exists():
            mplate_url = reverse('mplate_decoder:mplate_retrieve', args=[data])
            mplate_link = f'<a href="{mplate_url}">M-plate {data}</a>'
            self.saved_data['chassis_number_short'] = data
            raise ValidationError(
                f'M-Plate already exists. View {mplate_link}.')

        return data

    def clean_emden(self):
        data = self.cleaned_data['emden']

        data = data.upper()

        if data and (data != 'E'):
            raise ValidationError("Only the letter 'E' is allowed")

        return data

    def clean_m_codes(self, data):
        MCODE_LEN = 3
        mcodes_list = []

        if data:
            data = data.upper()
            if not re.match("^[A-Z0-9 ]+$", data):
                raise ValidationError(
                    "Only digits, letters and spaces allowed")

            if len(data) >= MCODE_LEN:
                if ' ' in data:
                    mcodes_list = data.split(' ')
                else:
                    mcodes_list = [data[i:i+MCODE_LEN]
                                   for i in range(0, len(data), MCODE_LEN)]

                for mcode in mcodes_list:
                    if len(mcode) != MCODE_LEN:
                        raise ValidationError(
                            "Code: {}. M-code length should be "
                            "{} digits or letters".format(mcode, MCODE_LEN)
                        )
                data = ' '.join(mcodes_list)
            else:
                raise ValidationError(
                            "Minimum M-code length: "
                            "{} digits or letters".format(MCODE_LEN)
                        )

        return data

    def clean_m_codes_1(self):
        data = self.clean_m_codes(self.cleaned_data['m_codes_1'])

        return data

    def clean_m_codes_2(self):
        data = self.clean_m_codes(self.cleaned_data['m_codes_2'])

        return data

    def clean_paint_and_interior(self):
        PAINT_AND_INTERIOR_LEN = 6
        data = self.cleaned_data['paint_and_interior']

        data = data.upper()

        if not re.match("^[A-Z0-9]+$", data):
            raise ValidationError("Only digits and letters allowed")

        if len(data) < PAINT_AND_INTERIOR_LEN:
            raise ValidationError(
                "Minimum paint and interior code length: "
                "{} digits or letters".format(
                    PAINT_AND_INTERIOR_LEN)
            )

        return data

    def clean_production_date(self):
        data = self.cleaned_data['production_date']
        decoder = MplateDecoder()

        # Get the model year to check the date format
        try:
            chassis_number_short = self.cleaned_data['chassis_number_short']
        except KeyError:
            # This happens when chassis_number_short is not valid (i.e. the
            # M-plate was already on the database)
            logger.warning("Chassis no. short not available from cleaned_data."
                           " Trying from saved data...")
            try:
                chassis_number_short = self.saved_data['chassis_number_short']
                logger.warning(f"Chassis no. short: {chassis_number_short}")
            except KeyError:
                logger.warning(
                    "Chassis no. short not available from saved_data.")
                raise ValidationError(
                    "Cannot validate production date format "
                    "without a valid chassis number.")
        model_year = decoder.get_model_year(chassis_number_short)

        # Model year is 68-69, check if valid production date
        if model_year < 1970:
            data = data.upper()
            if not re.match("^[1-3][0-9][1-9OND]$", data):
                raise ValidationError(
                    "Invalid production date format. Please double check.")

            try:
                production_data_decoded = decoder.get_production_date(
                    chassis_number=chassis_number_short,
                    encoded_production_date=data)
                if not production_data_decoded:
                    raise ValidationError(
                        f"Invalid production date. Please double check.")
            except ValueError as exc:
                raise ValidationError(
                    f"Invalid production date ({exc}). Please double check.")
        # Model year is 70-79, check if valid production date
        else:
            if not re.match("^([0][1-9]|[1-4][0-9]|5[0-2])[1-6]$", data):
                raise ValidationError(
                    "Invalid production date format. Please double check.")

            iso_week = int(data[2:])
            if iso_week > 52:
                raise ValidationError(
                    "Invalid production week date. Please double check"
                    " the two first digits.")

        return data

    def clean_production_planned(self):
        data = self.cleaned_data['production_planned']

        return data

    def clean_export_destination(self):
        EXPORT_DESTINATION_LEN = 2
        data = self.cleaned_data['export_destination']

        if data:
            data = data.upper()
            if not re.match("^[A-Z0-9]+$", data):
                raise ValidationError("Only digits and letters allowed")

            if len(data) < EXPORT_DESTINATION_LEN:
                raise ValidationError(
                    "Minimum destination country length:"
                    " {} letters or digits".format(
                        EXPORT_DESTINATION_LEN)
                )

        return data

    def clean_model(self):
        MODEL_LEN = 4
        data = self.cleaned_data['model']

        if len(data.strip()) < MODEL_LEN:
            raise ValidationError(
                "Minimum model code length: {} digits".format(
                    MODEL_LEN)
            )

        VALID_MODELS = Type2Model.objects.values_list('model', flat=True)
        VALID_MODELS = list(map(int, VALID_MODELS))

        logger.info('Valid models: {}'.format(VALID_MODELS))

        if not re.match("^2[1-467][14568][0-9]$", data):
            raise ValidationError(
                "Invalid model. Please double check.")

        try:
            model_int = int(data[:2])
        except ValueError:
            raise ValidationError("Only digits allowed in model code")

        logger.info('Model code: {}'.format(model_int))

        if model_int not in VALID_MODELS:
            raise ValidationError("Invalid model code")

        return data

    def clean_aggregate_code(self):
        AGGREGATE_CODE_LEN = 2
        data = self.cleaned_data['aggregate_code']

        if len(data) < AGGREGATE_CODE_LEN:
            raise ValidationError(
                "Minimum aggregate code length: {} digits".format(
                    AGGREGATE_CODE_LEN)
            )

        valid_aggregates = []

        try:
            aggregate_int = int(data)
        except ValueError:
            raise ValidationError("Only digits allowed in aggregate code")

        for engine in Engine.objects.all():
            for gearbox in Gearbox.objects.all():
                if gearbox.gearbox_description.startswith('Automatic'):
                    if engine.engine_type == 'Type 4':
                        valid_aggregates.append(
                            (engine.engine_code * 10) + gearbox.gearbox_code)
                else:
                    valid_aggregates.append(
                        (engine.engine_code * 10) + gearbox.gearbox_code)

        if aggregate_int not in valid_aggregates:
            raise ValidationError("Invalid aggregate code")

        return data


class MplateUpdateForm(MplateCreateForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
