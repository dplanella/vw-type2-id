"""
A simple functional headless UI test with pyvirtualdisplay and selenium
"""

from django.test import LiveServerTestCase
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class ExampleTestCase(LiveServerTestCase):
    LATE_BAY_01_CHASSIS = "92023025"
    LATE_BAY_02_CHASSIS = "22138101"
    EARLY_BAY_01_CHASSIS = "9123833"

    fixtures = [
        'tst_mplate_gearbox.json',
        'tst_mplate_engine.json',
        'tst_mplate_vwtype2model',
    ]

    def setUp(self):
        # Start the display
        # Set visible to 1 to view the actual browser
        # for visual debugging
        self.vdisplay = Display(visible=0, size=(1280, 900))
        self.vdisplay.start()

        # Start the browser
        self.selenium = webdriver.Firefox()
        self.selenium.maximize_window()
        super(ExampleTestCase, self).setUp()

    def tearDown(self):
        # Stop the browser
        self.selenium.quit()
        super(ExampleTestCase, self).tearDown()

        # Stop the display
        self.vdisplay.stop()

    def test_submit_plate(self):
        # Run tests
        self.selenium.get(
            '{}{}'.format(self.live_server_url, '/mplate/decode/')
        )

        chassis_number_short_input = self.selenium.find_element_by_name(
            "chassis_number_short")
        chassis_number_short_input.send_keys(self.EARLY_BAY_01_CHASSIS)

        m_codes_2_input = self.selenium.find_element_by_name("m_codes_2")
        m_codes_2_input.send_keys('408 095 504 507')

        paint_and_interior_input = self.selenium.find_element_by_name(
            "paint_and_interior_code")
        paint_and_interior_input.send_keys('383851')

        production_date_input = self.selenium.find_element_by_name(
            "production_date")
        production_date_input.send_keys('172')

        export_destination_input = self.selenium.find_element_by_name(
            "export_destination")
        export_destination_input.send_keys('PG')

        model_input = self.selenium.find_element_by_name("model_code")
        model_input.send_keys('2650')

        aggregate_code_input = self.selenium.find_element_by_name(
            "aggregate_code")
        aggregate_code_input.send_keys('11')

        current_url = self.selenium.current_url

        decode_button = self.selenium.find_element_by_id('btn-decode-6869')

        decode_button.location_once_scrolled_into_view
        decode_button.click()

        WebDriverWait(self.selenium, 15).until(EC.url_changes(current_url))

        production_date = WebDriverWait(
            self.selenium, 10).until(
                EC.element_to_be_clickable((By.ID, "production-date")))
        self.assertEqual(production_date.text, "Feb. 17, 1969")
