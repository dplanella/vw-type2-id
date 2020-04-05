from django.views import generic
from django.http import JsonResponse, HttpResponse
from .models import (
    Mplate,
    MplateDecoder,
    Mcode,
    McodeCollection,
    VwType2Model,
)
from .forms import MplateCreateForm, MplateUpdateForm
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import (
    ObjectDoesNotExist,
    MultipleObjectsReturned,
)
from collections import Counter
import logging
from lxml import etree


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


class AjaxableResponseMixin:
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
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
        if self.request.is_ajax():
            logger.debug("form_valid: ajax request")
            data = {
                'chassis_number_short': self.object.chassis_number_short,
            }
            response = JsonResponse(data)
        else:
            logger.debug("form_valid: NOT ajax request")

        return response


class MplateIndex(generic.ListView):
    model = Mplate
    template_name = 'mplate_decoder/index.html'


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

    def get_schematic(self, mplate):

        schematic = None
        model = int(mplate.model[:2])
        configuration = int(mplate.model[2])
        extras = int(mplate.model[3])
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
        model_code = mplate.model
        model_year = mplate.model_year
        m_codes = mplate.m_codes.split()
        t2_model = None
        SVG_NAMESPACE = u"http://www.w3.org/2000/svg"
        BUS_ROOF_COLOR_ID = 'roof-color'
        BUS_BODY_COLOR_ID = 'body-color'
        BUS_ROOF_COLOR_DEFAULT = '#ffffff'
        BUS_BODY_COLOR_DEFAULT = '#ffffff'

        logger.debug(
            f'Getting schematic for model {model}{configuration}{extras}, '
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
            schematic = t2_model.schematic_vector
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
                model_query &= m_codes_query

            try:
                t2_model = VwType2Model.objects.get(model_query)
                logger.debug(
                    f'Model {t2_model.model}, years {t2_model.years}, '
                    f'M-codes: {t2_model.m_codes}')
                schematic = t2_model.schematic_vector
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mplate = super().get_object()
        decoder = MplateDecoder(mplate)

        context['plate'] = mplate.render_plate()
        context['schematic'] = self.get_schematic(mplate)
        context['chassis_number'] = mplate.chassis_number
        context['model_year'] = mplate.model_year
        context['production_date'] = mplate.production_date_as_time
        context['export_destination'] = mplate._get_export_destination()
        context['export_destination_country'] = \
            mplate._get_export_destination_country()
        context['model_description'] = mplate.get_model()
        context['interiorcolor_description'] = mplate.get_interiorcolor()
        context['exteriorcolor_description'] = \
            mplate.get_exteriorcolor_description()
        context['engine_description'] = mplate.get_engine()
        context['gearbox_description'] = mplate.get_gearbox()
        context['m_codes'] = decoder.decode_mcodes()
        context['emden'] = mplate.emden

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

        # Enrich the mplate data with the model descriptions dictionary
        for mplate in results:
            try:
                mplate.model = mplate.get_model()
            except ValueError:
                logger.error(
                    'Could not get model descriptions for M-plate '
                    f'{mplate.chassis_number_short}')

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
        countries_labels = []
        countries_data = []

        context = super().get_context_data(**kwargs)

        mplates_all = Mplate.objects.all()

        models = [mplate.model for mplate in mplates_all]
        models_most_common = Counter(models).most_common(10)

        for model in models_most_common:
            models_labels.append(model[0])
            models_data.append(model[1])

        years = [mplate.model_year for mplate in mplates_all]
        years_most_common = Counter(years).most_common()
        for year in years_most_common:
            years_labels.append(year[0])
            years_data.append(year[1])

        colors = [mplate.paint_and_interior for mplate in mplates_all]
        colors_exterior = []
        for color in colors:
            if color.startswith('5'):
                colors_exterior.append(color[3:])
            else:
                colors_exterior.append(color[:4])
        colors_most_common = Counter(colors_exterior).most_common(10)
        for color in colors_most_common:
            colors_labels.append(color[0])
            colors_data.append(color[1])

        countries = [mplate.destination_country for mplate in mplates_all]
        countries_most_common = Counter(countries).most_common(10)
        for country in countries_most_common:
            if country[0]:
                countries_labels.append(country[0])
            else:
                countries_labels.append('Unknown')
            countries_data.append(country[1])

        context['modelsLabels'] = models_labels
        context['modelsData'] = models_data
        context['yearsLabels'] = years_labels
        context['yearsData'] = years_data
        context['colorsLabels'] = colors_labels
        context['colorsData'] = colors_data
        context['countriesLabels'] = countries_labels
        context['countriesData'] = countries_data

        return context
