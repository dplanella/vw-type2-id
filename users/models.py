from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(
        'E-mail address',
        help_text='Optional. Password recovery can only be done '
            'with a valid e-mail address.',
        blank=True,
        unique=True),
    dont_contact = models.BooleanField(
        'Do not contact me',
        default=False,
        help_text='I do not want to be contacted by the admin '
             'for questions about my M-plates.')
