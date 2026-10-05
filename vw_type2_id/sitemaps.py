from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from mplate_decoder.models import Mplate


class StaticSitemap(Sitemap):
    def items(self):
        return ['home', 'mplate_decoder:mplate_index',
                'mplate_decoder:mplate_create',
                'mplate_decoder:mplate_metrics',
                'mplate_decoder:mplate_about', 'contact']

    def location(self, item):
        return reverse(item)


class MplateSitemap(Sitemap):
    def items(self):
        return Mplate.objects.order_by('id').only(
            'chassis_number_short', 'updated_at')

    def lastmod(self, mplate):
        return mplate.updated_at


sitemaps = {'static': StaticSitemap, 'mplates': MplateSitemap}
