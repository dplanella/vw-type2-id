import logging
from django import template
from django.template.defaultfilters import stringfilter
register = template.Library()

logger = logging.getLogger('django')


@register.filter
@stringfilter
def summarizemodelyears(value):
    """
    Converts a list of model years to a summary: e.g.
    1970 1971 1972 => 1970-72
    """
    if value:
        years_list = value.split()
    else:
        # If no years list available, assume and return all years
        years_list = [str(year) for year in list(range(1968, 1979))]

    if len(years_list) > 1:
        summarizedmodelyears = f"{years_list[0]}-{years_list[-1][-2:]}"
    else:
        summarizedmodelyears = years_list[0]

    return summarizedmodelyears
