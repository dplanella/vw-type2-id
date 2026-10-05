from django import template
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def svg(name):
    """Inline the static file svg/<name>.svg."""
    with open(finders.find(f'svg/{name}.svg')) as svg_file:
        return mark_safe(svg_file.read())
