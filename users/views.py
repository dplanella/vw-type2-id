# from django.shortcuts import render

from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import login
from .forms import CustomUserCreationForm


class SignUp(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('mplate_decoder:mplate_mine')
    template_name = 'signup.html'

    def form_valid(self, form):
        valid = super().form_valid(form)

        # Login the user
        login(self.request, self.object)

        return valid
