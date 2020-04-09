from django.test import TestCase


class SimpleTest(TestCase):

    def _test_view(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_home(self):
        """Home view is rendered"""

        self._test_view('/')

    def test_mplate_index(self):
        """M-plate index view is rendered"""

        self._test_view('/mplate/')

    def test_mplate_decoder(self):
        """M-plate decoder view is rendered"""

        self._test_view('/mplate/decode/')

    def test_mplate_about(self):
        """M-plate about view is rendered"""

        self._test_view('/mplate/about/')

    def test_mplate_search(self):
        """M-plate search view is rendered"""

        self._test_view('/mplate/search/')

    # def test_mplate_metrics(self):
    #     """M-plate about view is rendered"""

    #     self._test_view('/mplate/metrics/')
