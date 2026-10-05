import re

from django.test import TestCase


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
