from django.core.mail import BadHeaderError, EmailMessage
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import ContactForm
from django.conf import settings
from django.utils.translation import gettext as _


def contactView(request):
    if request.method == 'GET':
        form = ContactForm()
    else:
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data['subject']
            from_email = form.cleaned_data['from_email']
            message = form.cleaned_data['message']
            try:
                EmailMessage(subject, message,
                             to=[settings.DEFAULT_FROM_EMAIL],
                             reply_to=[from_email]).send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            return redirect('success')
    return render(request, "contact.html", {'form': form})


def successView(request):

    success_message = _('Success! Thank you for your message.')

    return render(request, "success.html",
                  {'success_message': success_message})
