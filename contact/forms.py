from django import forms
from django.utils.translation import gettext as _


class ContactForm(forms.Form):
    from_email = forms.EmailField(label=_('Your e-mail'), required=True)
    subject = forms.CharField(required=True)
    message = forms.CharField(widget=forms.Textarea, required=True)
