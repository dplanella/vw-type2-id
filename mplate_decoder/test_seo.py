import re

from django.test import TestCase

from mplate_decoder.models import ExportDestination
from mplate_decoder.test_smoke import PLATE


class SeoTest(TestCase):
    """Pages carry the tags search engines read."""

    PAGES = ['/', '/mplate/', '/mplate/decode/', '/mplate/metrics/',
             '/mplate/about/', '/contact/']

    def get_html(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response.content.decode()

    def test_titles_and_descriptions(self):
        titles = set()
        descriptions = set()
        for url in self.PAGES:
            html = self.get_html(url)
            titles.add(re.search(r'<title>(.+?)</title>', html).group(1))
            descriptions.add(re.search(
                r'<meta name="description" content="(.+?)">',
                html).group(1))
        self.assertEqual(len(titles), len(self.PAGES))
        self.assertEqual(len(descriptions), len(self.PAGES))


class PlatePageTest(TestCase):
    """Plate pages describe the bus in their title, heading and summary."""

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
        'tst_mplate_vwtype2model',
    ]

    def test_plate_page(self):
        self.client.post('/mplate/decode/', PLATE)
        html = self.client.get(
            f"/mplate/{PLATE['chassis_number_short']}/").content.decode()
        heading = re.search(r'<h1[^>]*>(.+?)</h1>', html).group(1)
        self.assertRegex(heading, r'^19\d\d VW ')
        self.assertIn(
            f"<title>{heading}: M-plate {PLATE['chassis_number_short']} "
            "decoded | ", html)
        summary = re.search(r'<p class="lead">(.+?)</p>', html).group(1)
        self.assertIn(f'This {heading} was built on ', summary)
        self.assertIn(f'<meta name="description" content="{summary}">', html)

    def test_plate_page_destination(self):
        ExportDestination.objects.create(
            export_code=PLATE['export_destination_code'], country='Germany')
        self.client.post('/mplate/decode/', PLATE)
        response = self.client.get(
            f"/mplate/{PLATE['chassis_number_short']}/")
        self.assertContains(response, ' for Germany. ')


class IndexingTest(TestCase):
    """Indexable pages have a canonical link, others are noindex."""

    def test_canonical(self):
        response = self.client.get('/mplate/?utm_source=x')
        self.assertContains(response, '<link rel="canonical" '
                                      'href="http://testserver/mplate/">')
        self.assertNotContains(response, 'noindex')

    def test_noindex(self):
        for url in ['/mplate/search/?q=500', '/users/login/',
                    '/users/signup/', '/users/password_reset/',
                    '/success/', '/missing/']:
            response = self.client.get(url)
            self.assertContains(
                response, '<meta name="robots" content="noindex, follow">',
                status_code=response.status_code)
            self.assertNotContains(response, 'rel="canonical"',
                                   status_code=response.status_code)
