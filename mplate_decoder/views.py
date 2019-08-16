from django.views import generic
from django.http import JsonResponse, HttpResponse
from .models import Mplate, MplateDecoder
from .forms import (
    MplateForm,
    # MplateForm7079,
)
from django.urls import (
    # reverse,
    reverse_lazy,
)
import logging

logger = logging.getLogger('django')

# from django.shortcuts import render
# from django.views.generic.edit import CreateView, UpdateView, DeleteView
# from .forms import year_and_serial_from_chassis_no, is_60s_bus
# from django.views.generic.base import TemplateView
# from django.http import HttpResponse

# def index(request):
#    # template_name = 'mplate_decoder/index.html'
#    return HttpResponse("Hello, world. You're at the M-plate decoder index.")


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
    # greeting = "Hello, world. You're at the M-plate decoder index."

    # def get(self, request):
    #    return HttpResponse(self.greeting)


# class MplateCreate(generic.FormView):
#     form_class = MplateForm7079
#     template_name = 'mplate_decoder/mplate_form.html'
#     chassis_number_short = ''

#     def form_valid(self, form):
#         mplate = form.save()
#         self.chassis_number_short = mplate.chassis_number_short
#         # self.chassis_number_short = form.instance.chassis_number_short
#         response = super().form_valid(form)

#         return response

#     def get_success_url(self):
#         success_url = reverse(
#             'mplate_retrieve',
#             kwargs={'chassis_number_short': self.chassis_number_short})

#         return success_url


class MplateCreate(AjaxableResponseMixin, generic.edit.CreateView):
    form_class = MplateForm
    template_name = 'mplate_decoder/mplate_form.html'

#    model = Mplate
#    fields = [
#            'chassis_number_short',
#            'm_codes_1',
#            'm_codes_2',
#            'paint_and_interior',
#            'production_date',
#            'production_planned',
#            'export_destination',
#            'model',
#            'aggregate_code',
#            ]
    # initial = {'date_of_death': '05/01/2018'}

    # def get_success_url(self):
    #    return reverse('mplate_retrieve', args=(self.object.pk,))

    # def form_valid(self, form):
    #    form.instance.chassis_number
    #    pass
    #    # This method is called when valid form data has been POSTed.
    #    # It should return an HttpResponse.
    #    form.send_email()
    #    return super().form_valid(form)


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
        context['model_year'] = decoder.get_model_year().year  # mplate.get_model_year().year # noqa
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
    success_url = reverse_lazy('mplate_index')
