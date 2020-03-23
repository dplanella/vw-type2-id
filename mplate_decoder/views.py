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
import logging

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
            logger.info("form_valid: ajax request")
            data = {
                'chassis_number_short': self.object.chassis_number_short,
            }
            response = JsonResponse(data)
        else:
            logger.info("form_valid: NOT ajax request")

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

    def get_schematic(self, model_code, model_year, m_codes):

        schematic = None
        model = int(model_code[:2])
        configuration = int(model_code[2])
        extras = int(model_code[3])
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
            schematic = t2_model.schematic_bitmap
        except ObjectDoesNotExist:
            logger.error(
                f'Does not exist: Model {model_code}, years {model_year}, '
                f'M-codes: {m_codes}')
        except MultipleObjectsReturned:
            logger.debug(
                f'Multiple objects: Model {model_code}, years {model_year}, '
                f'M-codes: {m_codes}')

            m_codes_query = Q()
            for m_code in special_sales_m_codes:
                m_codes_query |= Q(m_codes__icontains=m_code)

            model_query &= m_codes_query

            try:
                t2_model = VwType2Model.objects.get(model_query)
                logger.debug(
                    f'Model {t2_model.model}, years {t2_model.years}, '
                    f'M-codes: {t2_model.m_codes}')
                schematic = t2_model.schematic_bitmap
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

        schematic = t2_model.schematic_bitmap

        return schematic

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mplate = super().get_object()
        decoder = MplateDecoder(mplate)

        context['plate'] = mplate.render_plate()
        context['schematic'] = self.get_schematic(
            mplate.model,
            mplate.model_year,
            mplate.m_codes)
        context['chassis_number'] = mplate.get_chassis_number()
        context['model_year'] = mplate.model_year
        context['production_date'] = mplate.production_date_as_time
        context['export_destination'] = mplate.get_export_destination()
        context['export_destination_geo'] = mplate.get_export_destination_geo()
        context['model_description'] = mplate.get_model()
        context['interiorcolor_description'] = mplate.get_interiorcolor()
        context['exteriorcolor_description'] = \
            mplate.get_exteriorcolor_description()
        context['engine_description'] = mplate.get_engine()
        context['gearbox_description'] = mplate.get_gearbox()
        context['m_codes'] = decoder.get_mcodes()
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
            if query != '*':
                results = Mplate.objects.order_by('-id').filter(
                    Q(m_codes__icontains=query)
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
