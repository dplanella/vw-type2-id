from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from lxml import html

from mplate_decoder.models import Mplate


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
                    '/users/signup/', '/users/login/', '/health/']:
            self.assert_ok(url)

    @override_settings(GIT_COMMIT='0123456789abcdef0123456789abcdef01234567')
    def test_commit_shown(self):
        self.assertEqual(self.client.get('/health/').content,
                         b'ok 0123456789abcdef0123456789abcdef01234567')
        self.assertContains(self.client.get('/'), '>0123456<')

    def test_inline_svg(self):
        self.assertContains(self.client.get('/mplate/decode/'), '<svg')

    def test_translated_pages(self):
        for lang in ['ca', 'de', 'es', 'fr', 'nl']:
            response = self.client.get(
                '/mplate/', HTTP_ACCEPT_LANGUAGE=lang)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Language'], lang)

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

    def test_logout(self):
        self.client.force_login(self.user)
        response = self.client.get('/mplate/')
        self.assertContains(response, 'action="/users/logout/"')
        response = self.client.post('/users/logout/')
        self.assertRedirects(response, '/mplate/')
        self.assertNotIn('_auth_user_id', self.client.session)

    def admin_save(self, url, **changes):
        page = html.fromstring(self.client.get(url).content)
        form = page.get_element_by_id(changes.pop('form_id'))
        data = dict(form.form_values())
        data.update(changes, _save='Save')
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, url)

    def test_admin_save(self):
        self.create_plate(self.user)
        self.client.force_login(self.admin)
        plate = Mplate.objects.get()
        self.admin_save(f'/admin/mplate_decoder/mplate/{plate.pk}/change/',
                        form_id='mplate_form', production_planned='7495')
        self.assertEqual(Mplate.objects.get().production_planned, '7495')
        self.admin_save(f'/admin/users/customuser/{self.user.pk}/change/',
                        form_id='customuser_form', first_name='Owner')
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Owner')

    def test_admin_logout(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post('/admin/logout/').status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_signup(self):
        response = self.client.post('/users/signup/', {
            'username': 'newbie',
            'email': 'newbie@example.com',
            'password1': 'a-Long-pass-1234',
            'password2': 'a-Long-pass-1234',
        })
        self.assertRedirects(response, '/mplate/mine/')
        self.assertEqual(self.client.session['_auth_user_id'],
                         str(get_user_model().objects.get(
                             username='newbie').pk))

    def test_password_change(self):
        self.client.force_login(self.user)
        response = self.client.post('/users/password_change/', {
            'old_password': 'pw',
            'new_password1': 'a-New-pass-1234',
            'new_password2': 'a-New-pass-1234',
        })
        self.assertRedirects(response, '/users/password_change/done/')
        self.client.post('/users/logout/')
        response = self.client.post('/users/login/', {
            'username': 'owner', 'password': 'a-New-pass-1234'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('_auth_user_id', self.client.session)

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_reset(self):
        self.user.email = 'owner@example.com'
        self.user.save()
        response = self.client.post('/users/password_reset/',
                                    {'email': 'owner@example.com'})
        self.assertRedirects(response, '/users/password_reset/done/')
        self.assertEqual(len(mail.outbox), 1)
        link = next(word for word in mail.outbox[0].body.split()
                    if '/users/reset/' in word)
        response = self.client.get(link, follow=True)
        url = response.redirect_chain[-1][0]
        response = self.client.post(url, {
            'new_password1': 'a-New-pass-1234',
            'new_password2': 'a-New-pass-1234',
        })
        self.assertRedirects(response, '/users/reset/done/')
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('a-New-pass-1234'))

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
        self.assertEqual(mail.outbox[0].from_email,
                         'VW Type 2 ID <no-reply@vw-type2-id.xyz>')
        self.assertEqual(mail.outbox[0].to, ['contact@vw-type2-id.xyz'])
        self.assertEqual(mail.outbox[0].reply_to, ['visitor@example.com'])
