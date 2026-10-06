from django.views import generic
from django.http import JsonResponse, HttpResponse
from .models import (
    Color,
    Mplate,
    MplateDecoder,
    Mcode,
    McodeCollection,
    ExteriorColor,
)
from .forms import MplateCreateForm, MplateUpdateForm
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.translation import gettext, ngettext
from django.utils.translation import gettext_lazy as _
from collections import Counter
import logging
from lxml import etree
from datetime import timedelta
import os
from vw_type2_id.settings import BASE_DIR


logger = logging.getLogger(__name__)


class OwnerQuerysetMixin(object):
    """
    Mixin to restrict views to object instances the logged-in user is the
    creator of. Staff members can override this check.
    The user will get a 404 error if they do not own the object.
    See https://stackoverflow.com/a/38545128
    """
    def get_queryset(self):
        queryset = super().get_queryset()

        # perhaps handle the case where user is not authenticated
        if not self.request.user.is_staff:
            queryset = queryset.filter(owner=self.request.user)

        return queryset


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


class AjaxableResponseMixin:
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if is_ajax(self.request):
            logger.info("form_invalid: ajax request")
            data = form.errors.as_json()
            response = HttpResponse(
                data,
                status=400,
                content_type='application/json')
        else:
            logger.info("form_invalid: NOT ajax request")

        # logger.info("form invalid, response: {}".format(response.content))
        return response

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        #
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if is_ajax(self.request):
            logger.debug("form_valid: ajax request")
            data = {
                'chassis_number_short': self.object.chassis_number_short,
            }
            response = JsonResponse(data)
        else:
            logger.debug("form_valid: NOT ajax request")

        return response


class MplateIndex(generic.ListView):
    queryset = Mplate.objects.order_by('-id')[:7]
    template_name = 'mplate_decoder/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mplate_count'] = Mplate.objects.count()
        return context


class MplateAbout(generic.TemplateView):
    template_name = 'mplate_decoder/mplate_about.html'


class MplateCreate(AjaxableResponseMixin, generic.edit.CreateView):
    form_class = MplateCreateForm
    template_name = 'mplate_decoder/mplate_form.html'


class MplateRetrieve(generic.DetailView):
    model = Mplate
    template_name = 'mplate_decoder/detail.html'
    slug_field = 'chassis_number_short'
    slug_url_kwarg = 'chassis_number_short'

    def render_plate(self, mplate):
        SVG_NAMESPACE = u"http://www.w3.org/2000/svg"
        model_year = int(mplate.model_year)
        if model_year in [1968, 1969]:
            svg_file = os.path.join(BASE_DIR, "mplate_decoder",
                                    "images/mplate-6869-ref.svg")
        else:
            svg_file = os.path.join(BASE_DIR, "mplate_decoder",
                                    "images/mplate-7079-ref.svg")
        MPLATE_STOP_COLOR_ID = 'stopBusColor'
        MPLATE_STOP_COLOR = '#a6a6a6'
        fields = (
            'chassis_number_short',
            'm_codes_1',
            'm_codes_2',
            'paint_and_interior_code',
            'production_date_code',
            'production_planned',
            'export_destination_code',
            'model_code',
            'aggregate_code',
            'emden',
        )

        tree = etree.parse(svg_file)

        # Replace each field name with a matching id on the SVG file, with
        # its value
        for field in fields:
            mplate_field = tree.find(
                ".//n:text[@id='{}']/n:tspan".format(field),
                namespaces={'n': SVG_NAMESPACE})
            mplate_field.text = getattr(mplate, field)

        color_chip_body, _ = mplate._get_exteriorcolorchip()

        if color_chip_body:
            # Replace gradient color
            stop_color = tree.find(
                ".//n:stop[@id='{}']".format(MPLATE_STOP_COLOR_ID),
                namespaces={'n': SVG_NAMESPACE}
            )

            stop_color.attrib['style'] = stop_color.attrib['style'].replace(
                MPLATE_STOP_COLOR, color_chip_body)

        plate = etree.tostring(tree).decode('utf-8')

        return plate

    def render_schematic(self, mplate):

        schematic = None
        t2_model = None
        SVG_NAMESPACE = u"http://www.w3.org/2000/svg"
        BUS_ROOF_COLOR_ID = 'roof-color'
        BUS_BODY_COLOR_ID = 'body-color'
        BUS_ROOF_COLOR_DEFAULT = '#ffffff'
        BUS_BODY_COLOR_DEFAULT = '#ffffff'

        t2_model = mplate.model

        if t2_model:
            schematic = t2_model.schematic_vector

        if schematic:
            tree = etree.fromstring(schematic)

            color_chip_body, color_chip_roof = mplate._get_exteriorcolorchip()
            logger.debug(f'Body color chip code: {color_chip_body}')
            logger.debug(f'Roof color chip code: {color_chip_roof}')

            if color_chip_body:
                # Replace body color
                body_color = tree.find(
                    f".//n:path[@id='{BUS_BODY_COLOR_ID}']",
                    namespaces={'n': SVG_NAMESPACE}
                )

                if body_color is not None:
                    logger.debug(f'Body color: {body_color}')
                    logger.debug(
                        f"Body color style: {body_color.attrib['style']}")
                    body_color.attrib['style'] = \
                        body_color.attrib['style'].replace(
                            f'fill:{BUS_BODY_COLOR_DEFAULT}',
                            f'fill:{color_chip_body}')
                    logger.debug(
                        f"Body color style: {body_color.attrib['style']}")

            roof_color = None
            if color_chip_roof:
                # Replace roof color
                roof_color = tree.find(
                    f".//n:path[@id='{BUS_ROOF_COLOR_ID}']",
                    namespaces={'n': SVG_NAMESPACE}
                )

                if roof_color is not None:
                    logger.debug(f'Roof color: {roof_color}')
                    logger.debug(
                        f"Roof color style: {body_color.attrib['style']}")
                    roof_color.attrib['style'] = \
                        roof_color.attrib['style'].replace(
                            f'fill:{BUS_ROOF_COLOR_DEFAULT}',
                            f'fill:{color_chip_roof}')
                    logger.debug(
                        f"Roof color style: {roof_color.attrib['style']}")

            schematic = etree.tostring(tree).decode('utf-8')

        return schematic

    def describe_bus(self, mplate):
        """Return a short name for the bus, e.g. 1971 VW Microbus (221)."""
        t2_model = mplate.model
        if t2_model is None:
            return gettext('%(year)s VW Type 2') % {'year': mplate.model_year}
        return gettext('%(year)s VW %(model)s (%(code)s)') % {
            'year': mplate.model_year,
            'model': t2_model.model_description,
            'code': f'{t2_model.model}{t2_model.configuration}',
        }

    def body_color_name(self, mplate):
        exteriorcolor = mplate.exteriorcolor
        if not exteriorcolor:
            return ''
        color = Color.objects.filter(
            lacquer_code=exteriorcolor.lacquer_code_body).first()
        return color.color_name if color else ''

    def summarize(self, mplate, bus, m_codes):
        """Return a one-paragraph summary of the decoded plate."""
        destination = mplate.export_destination
        country = destination and (destination.country or destination.region)
        values = {
            'bus': bus,
            'date': date_format(mplate.production_date_as_time),
            'country': country,
            'count': len(m_codes),
        }
        if country:
            summary = gettext(
                'This %(bus)s was built on %(date)s for %(country)s.')
        else:
            summary = gettext('This %(bus)s was built on %(date)s.')
        if m_codes:
            summary += ' ' + ngettext(
                'Its M-plate lists %(count)d optional extra.',
                'Its M-plate lists %(count)d optional extras.',
                len(m_codes))
        return summary % values

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mplate = super().get_object()
        decoder = MplateDecoder(mplate)
        m_codes = decoder.decode_mcodes()
        bus = self.describe_bus(mplate)
        color = self.body_color_name(mplate)

        context['plate'] = self.render_plate(mplate)
        context['schematic'] = self.render_schematic(mplate)
        context['chassis_number'] = mplate.chassis_number
        context['model_year'] = mplate.model_year
        context['production_date'] = mplate.production_date_as_time
        context['export_destination'] = mplate.describe_export_destination()
        context['export_destination_country'] = \
            mplate.describe_export_destination_country()
        context['model_description'] = mplate.describe_model()
        context['interiorcolor_description'] = mplate.describe_interiorcolor()
        context['exteriorcolor_description'] = \
            mplate.describe_exteriorcolor()
        context['engine_description'] = mplate.get_engine()
        context['gearbox_description'] = mplate.get_gearbox()
        context['m_codes'] = m_codes
        context['emden'] = mplate.emden
        if color:
            context['heading'] = gettext('%(bus)s, %(color)s') % {
                'bus': bus, 'color': color}
        else:
            context['heading'] = bus
        context['summary'] = self.summarize(mplate, bus, m_codes)

        return context


class MplateUpdate(AjaxableResponseMixin, LoginRequiredMixin,
                   OwnerQuerysetMixin, generic.edit.UpdateView):
    model = Mplate
    # fields = '__all__'
    form_class = MplateUpdateForm
    template_name = 'mplate_decoder/mplate_form.html'
    slug_field = 'chassis_number_short'
    slug_url_kwarg = 'chassis_number_short'


class MplateDelete(LoginRequiredMixin, OwnerQuerysetMixin,
                   generic.edit.DeleteView):
    model = Mplate
    slug_field = 'chassis_number_short'
    slug_url_kwarg = 'chassis_number_short'
    success_url = reverse_lazy('mplate_decoder:mplate_index')


class SearchResultsView(generic.ListView):
    model = Mplate
    template_name = 'mplate_decoder/search_results.html'
    paginate_by = 25
    context_object_name = 'mplates'

    def get_queryset(self):

        results = []
        query = self.request.GET.get('q')

        if query:
            advanced_search_query = Q()
            query_strings = query.split()

            for q_string in query_strings:
                exclude = False
                try:
                    key, value = q_string.split(':')
                except ValueError:
                    key, value = ('mcode', q_string)

                if key.startswith('-'):
                    key = key[1:]
                    exclude = True

                if key == 'year':
                    if not exclude:
                        advanced_search_query &= Q(model_year__exact=value)
                    else:
                        advanced_search_query &= ~Q(model_year__exact=value)
                elif key == 'model':
                    if not exclude:
                        advanced_search_query &= Q(model__exact=value)
                    else:
                        advanced_search_query &= ~Q(model__exact=value)
                elif key == 'mcode':
                    if not exclude:
                        advanced_search_query &= Q(m_codes__icontains=value)
                    else:
                        advanced_search_query &= ~Q(m_codes__icontains=value)
                elif key == 'country':
                    if not exclude:
                        advanced_search_query &= Q(m_codes__iexact=value)
                    else:
                        advanced_search_query &= ~Q(m_codes__iexact=value)
                else:
                    if not exclude:
                        advanced_search_query &= Q(m_codes__icontains=value)
                    else:
                        advanced_search_query &= ~Q(m_codes__icontains=value)

            if query != '*':
                results = Mplate.objects.order_by('-id').filter(
                    advanced_search_query
                )
            else:
                results = Mplate.objects.all()

        return results

    def get_context_data(self, **kwargs):
        '''
        Add additional context data
        '''
        query = self.request.GET.get('q')
        context = super().get_context_data(**kwargs)

        m_code_query_set = Mcode.objects.filter(
                m_code__iexact=query)

        if not m_code_query_set:
            m_code_query_set = McodeCollection.objects.filter(
                m_code__iexact=query)

        context['m_code_query_set'] = m_code_query_set

        return context


class MplatesByUserListView(LoginRequiredMixin, generic.ListView):
    """
    Generic class-based view listing M-plates created by the current user.
    """
    model = Mplate
    template_name = 'mplate_decoder/mplate_created_by_user.html'
    paginate_by = 10

    def get_queryset(self):
        qs = Mplate.objects.filter(owner=self.request.user)
        return qs


class MetricsView(generic.TemplateView):
    model = Mplate
    template_name = 'mplate_decoder/metrics.html'
    # context_object_name = 'mplates'

    def get_context_data(self, **kwargs):
        '''
        Add additional context data
        '''
        models_labels = []
        models_data = []
        years_labels = []
        years_data = []
        colors_labels = []
        colors_data = []
        colors_backgroundcolor = []
        countries_labels = []
        countries_data = []
        submissions_labels = []
        submissions_data = []

        context = super().get_context_data(**kwargs)

        mplates_all = Mplate.objects.select_related('decoded_model').only(
            'model_year', 'paint_and_interior_code', 'destination_country',
            'decoded_model',
            'decoded_model__model', 'decoded_model__configuration',
            'decoded_model__extras', 'decoded_model__model_description',
            'decoded_model__extras_description')

        # Collect model data
        models = [mplate.decoded_model for mplate in mplates_all]
        models_most_common = Counter(models).most_common(10)

        for model in models_most_common:
            logger.debug(model[0])
            if model[0] is None:
                continue
            models_labels.append(
                f'{model[0].model_description} '
                f'{model[0].extras_description} '
                f'({model[0].model}{model[0].configuration}{model[0].extras})'
                )
            models_data.append(model[1])

        # Collect years data
        years = [mplate.model_year for mplate in mplates_all]
        years_most_common = Counter(years).most_common()
        for year in years_most_common:
            years_labels.append(year[0])
            years_data.append(year[1])

        # Collect colors data
        colors = [mplate.paint_and_interior_code for mplate in mplates_all]
        colors_exterior = []
        color_description = ''
        color_code = ''
        exteriorcolor_object = None
        for color in colors:
            if color.startswith('5'):
                color_code = color[3:]
            else:
                color_code = color[:4]
            colors_exterior.append(color_code)
        colors_most_common = Counter(colors_exterior).most_common(15)
        logger.info(colors_most_common)
        for color in colors_most_common:
            try:
                exteriorcolor_object = \
                    ExteriorColor.objects.filter(
                        plate_code=color[0])[0]
                color_description = \
                    exteriorcolor_object.lacquer_code_body_link.color_name
                color_chip = \
                    exteriorcolor_object.lacquer_code_body_link.chip
            except IndexError:
                continue
            colors_labels.append(f'{color_description} ({color[0]})')
            colors_data.append(color[1])
            colors_backgroundcolor.append(color_chip)

        # Collect countries data
        countries = [mplate.destination_country for mplate in mplates_all]
        countries_most_common = Counter(countries).most_common(10)
        for country in countries_most_common:
            if country[0]:
                countries_labels.append(country[0])
            else:
                countries_labels.append(_('Unknown'))
            countries_data.append(country[1])

        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        # Collect submissions data
        monthly_submissions = Mplate.objects.filter(
            created_at__range=(start_date, end_date))
        days = [mplate.created_at.date().isoformat()
                for mplate in monthly_submissions]
        days_submissions = sorted(Counter(days).items())

        for day in days_submissions:
            submissions_labels.append(day[0])
            submissions_data.append(day[1])

        context['modelsLabels'] = models_labels
        context['modelsData'] = models_data
        context['yearsLabels'] = years_labels
        context['yearsData'] = years_data
        context['colorsLabels'] = colors_labels
        context['colorsData'] = colors_data
        context['colorsBackgroundColor'] = colors_backgroundcolor
        context['countriesLabels'] = countries_labels
        context['countriesData'] = countries_data
        context['submissionsLabels'] = submissions_labels
        context['submissionsData'] = submissions_data

        return context
