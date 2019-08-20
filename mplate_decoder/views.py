from django.views import generic
from django.http import JsonResponse, HttpResponse
from .models import Mplate, MplateDecoder
from .forms import MplateForm
from django.urls import reverse_lazy
import logging

logger = logging.getLogger('django')


class AjaxableResponseMixin:
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """
    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            logger.info("request is ajax, form invalid")
            data = form.errors.as_json()
            response = HttpResponse(
                data,
                status=400,
                content_type='application/json')
        else:
            logger.info("request is not ajax, form invalid")

        # logger.info("form invalid, response: {}".format(response.content))
        return response

    def form_valid(self, form):
        # We make sure to call the parent's form_valid() method because
        # it might do some processing (in the case of CreateView, it will
        # call form.save() for example).
        response = super().form_valid(form)
        if self.request.is_ajax():
            logger.info("request is ajax, form valid")
            data = {
                'chassis_number_short': self.object.chassis_number_short,
            }
            response = JsonResponse(data)
        else:
            logger.info("request is not ajax, form valid")

        # logger.info("form valid, response: {}".format(response.content))
        return response


class MplateIndex(generic.ListView):
    model = Mplate
    template_name = 'mplate_decoder/index.html'


class MplateCreate(AjaxableResponseMixin, generic.edit.CreateView):
    form_class = MplateForm
    template_name = 'mplate_decoder/mplate_form.html'


class MplateRetrieve(generic.DetailView):
    model = Mplate
    template_name = 'mplate_decoder/detail.html'
    slug_field = 'chassis_number_short'
    slug_url_kwarg = 'chassis_number_short'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mplate = super().get_object()
        decoder = MplateDecoder(mplate)

        context['chassis_number'] = mplate.get_chassis_number()
        context['model_year'] = decoder.get_model_year().year
        context['production_date'] = mplate.get_production_date()
        context['export_destination'] = mplate.get_export_destination()
        context['plate'] = mplate.render_plate()
        context['model_description'] = mplate.get_model()
        context['interiorcolor_description'] = mplate.get_interiorcolor()
        context['exteriorcolor_description'] = mplate.get_exteriorcolor()
        context['engine_description'] = mplate.get_engine()
        context['gearbox_description'] = mplate.get_gearbox()
        context['m_codes'] = decoder.get_mcodes()

        return context


class MplateUpdate(generic.edit.UpdateView):
    model = Mplate
    fields = '__all__'
    slug_field = 'chassis_number_short'
    slug_url_kwarg = 'chassis_number_short'


class MplateDelete(generic.edit.DeleteView):
    model = Mplate
    slug_field = 'chassis_number_short'
    slug_url_kwarg = 'chassis_number_short'
    success_url = reverse_lazy('mplate_decoder:mplate_index')
