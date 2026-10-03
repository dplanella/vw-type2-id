from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import translation

from mplate_decoder.models import ExportDestination, Mplate


PLATE = {
    'chassis_number_short': '92023025',
    'm_codes_1': '',
    'm_codes_2': 'D03 P22 005 227',
    'paint_and_interior_code': '9451EB',
    'production_date_code': '382',
    'production_planned': '7494',
    'export_destination_code': 'UT',
    'model_code': '2319',
    'aggregate_code': '61',
    'emden': '',
}


class SmokeTest(TestCase):
    """Main pages render and the main forms work."""

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
        'tst_mplate_vwtype2model',
    ]

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user('owner', password='pw')
        self.admin = User.objects.create_superuser(
            'admin', 'admin@example.com', 'pw')

    def create_plate(self, user=None):
        if user:
            self.client.force_login(user)
        response = self.client.post('/mplate/decode/', PLATE)
        self.assertEqual(response.status_code, 302)
        return Mplate.objects.get(
            chassis_number_short=PLATE['chassis_number_short'])

    def assert_ok(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response

    def test_public_pages(self):
        for url in ['/', '/mplate/', '/mplate/decode/', '/mplate/about/',
                    '/mplate/search/?q=920', '/contact/', '/success/',
                    '/users/signup/', '/users/login/']:
            self.assert_ok(url)

    def test_translated_pages(self):
        for lang in ['ca', 'de', 'es', 'fr', 'nl']:
            response = self.client.get(
                '/mplate/', HTTP_ACCEPT_LANGUAGE=lang)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Language'], lang)

    def test_translated_model_fields(self):
        ExportDestination.objects.create(export_code='XX', country='Germany')
        with translation.override('de'):
            self.assertEqual(ExportDestination.objects.get().country,
                             'Deutschland')

    def test_create_sets_owner(self):
        plate = self.create_plate(self.user)
        self.assertEqual(plate.owner, self.user)

    def test_create_anonymous(self):
        plate = self.create_plate()
        self.assertIsNone(plate.owner)

    def test_create_ajax(self):
        response = self.client.post('/mplate/decode/', PLATE,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.json(), {
            'chassis_number_short': PLATE['chassis_number_short']})

    def test_create_ajax_invalid(self):
        response = self.client.post('/mplate/decode/', {},
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertIn('chassis_number_short', response.json())

    def test_plate_pages(self):
        self.create_plate(self.user)
        url = f"/mplate/{PLATE['chassis_number_short']}/"
        for lang in ['en', 'de']:
            response = self.client.get(url, HTTP_ACCEPT_LANGUAGE=lang)
            self.assertEqual(response.status_code, 200)
        self.assert_ok(url + 'update/')
        self.assert_ok(url + 'delete/')
        self.assert_ok('/mplate/mine/')
        self.assert_ok('/mplate/metrics/')

    def test_owner_only(self):
        self.create_plate(self.user)
        User = get_user_model()
        other = User.objects.create_user('other', password='pw')
        self.client.force_login(other)
        response = self.client.get(
            f"/mplate/{PLATE['chassis_number_short']}/update/")
        self.assertEqual(response.status_code, 404)

    def test_admin(self):
        self.create_plate(self.user)
        self.client.force_login(self.admin)
        plate = Mplate.objects.get()
        for url in ['/admin/', '/admin/mplate_decoder/mplate/',
                    f'/admin/mplate_decoder/mplate/{plate.pk}/change/',
                    '/admin/mplate_decoder/mcode/',
                    '/admin/mplate_decoder/color/',
                    '/admin/users/customuser/']:
            self.assert_ok(url)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_contact(self):
        response = self.client.post('/contact/', {
            'from_email': 'visitor@example.com',
            'subject': 'Hello',
            'message': 'Hi there',
        })
        self.assertRedirects(response, '/success/')
        self.assertEqual(len(mail.outbox), 1)
