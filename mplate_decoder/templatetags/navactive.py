from django.template import Library
from django.urls import reverse
register = Library()


@register.simple_tag
def navactive(request, url):
    # Check if the url and the current path are a match
    ACTIVE_CLASS = "active"
    is_active = ""

    if request.path == reverse(url):
        is_active = ACTIVE_CLASS

    return is_active
