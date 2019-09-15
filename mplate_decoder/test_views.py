from django.test import TestCase


class SimpleTest(TestCase):

    def test_home(self):
        """Home view is rendered"""

        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_mplate_index(self):
        """M-plate index view is rendered"""

        response = self.client.get('/mplate/')
        self.assertEqual(response.status_code, 200)

    def test_mplate_decoder(self):
        """M-plate decoder view is rendered"""

        response = self.client.get('/mplate/decode/')
        self.assertEqual(response.status_code, 200)

    def test_mplate_about(self):
        """M-plate about view is rendered"""

        response = self.client.get('/mplate/about/')
        self.assertEqual(response.status_code, 200)
