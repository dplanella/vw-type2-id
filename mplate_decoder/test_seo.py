import json
import re

from django.test import TestCase

from mplate_decoder.models import ExportDestination, Mplate
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
        self.assertTrue(summary.startswith('Built on '))
        self.assertIn(f'<meta name="description" content="{heading}, '
                      f'built on ', html)
        self.assertNotRegex(heading, r'\(\d+\)')

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


class CrawlingTest(TestCase):
    """robots.txt points to a sitemap listing pages and plates."""

    fixtures = PlatePageTest.fixtures

    def test_robots_txt(self):
        response = self.client.get('/robots.txt')
        self.assertEqual(response['Content-Type'], 'text/plain')
        self.assertEqual(response.content.decode(), 'User-agent: *\n'
                         'Disallow: /admin/\n'
                         'Sitemap: http://testserver/sitemap.xml\n')

    def test_sitemap(self):
        self.client.post('/mplate/decode/', PLATE)
        response = self.client.get('/sitemap.xml')
        for url in ['/', '/mplate/', '/mplate/decode/', '/mplate/metrics/',
                    '/mplate/about/', '/contact/',
                    f"/mplate/{PLATE['chassis_number_short']}/"]:
            self.assertContains(response, f'<loc>http://testserver{url}</loc>')
        self.assertContains(response, '<lastmod>', count=1)


class SharingTest(TestCase):
    """Pages carry Open Graph tags; the home page names the site."""

    def test_open_graph(self):
        response = self.client.get('/mplate/about/')
        self.assertContains(
            response, '<meta property="og:url" '
            'content="http://testserver/mplate/about/">')
        self.assertContains(response, '<meta property="og:title" '
                            'content="About this site">')

    def test_site_name(self):
        html = self.client.get('/').content.decode()
        data = json.loads(re.search(
            r'<script type="application/ld\+json">(.+?)</script>',
            html, re.S).group(1))
        self.assertEqual(data['@type'], 'WebSite')
        self.assertEqual(data['name'], 'VW Type 2 Identification')
        self.assertEqual(data['url'], 'http://testserver/')


class IndexPageTest(TestCase):
    """The M-plate page shows the total and only the latest plates."""

    def test_latest_plates(self):
        Mplate.objects.bulk_create([Mplate(
            chassis_number_short=f'2200000{n}',
            production_date_as_time='1971-01-01', model_year='1972')
            for n in range(10)])
        with self.assertNumQueries(2):
            response = self.client.get('/mplate/')
        self.assertEqual(
            [m.chassis_number_short for m in response.context['object_list']],
            [f'2200000{n}' for n in range(9, 2, -1)])
        self.assertEqual(response.context['mplate_count'], 10)
