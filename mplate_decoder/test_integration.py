"""
A simple functional headless UI test with pyvirtualdisplay and selenium
"""

from django.test import LiveServerTestCase
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


class ExampleTestCase(LiveServerTestCase):
    LATE_BAY_01_CHASSIS = "92023025"
    LATE_BAY_02_CHASSIS = "22138101"
    EARLY_BAY_01_CHASSIS = "9123833"

    fixtures = [
        'mplate_gearbox.json',
        'mplate_engine.json',
        'mplate_type2model',
        'mplate_type2modelconfiguration',
        'mplate_type2modelextra',
    ]

    def setUp(self):

        # Start the display
        self.vdisplay = Display(visible=1, size=(1280, 900))
        self.vdisplay.start()

        # Start the browser
        self.selenium = webdriver.Firefox()
        #self.selenium.set_window_position(0, 0)
        #self.selenium.set_window_size(2560, 1440)
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
            "paint_and_interior")
        paint_and_interior_input.send_keys('383851')

        production_date_input = self.selenium.find_element_by_name(
            "production_date")
        production_date_input.send_keys('072')

        export_destination_input = self.selenium.find_element_by_name(
            "export_destination")
        export_destination_input.send_keys('PG')

        model_input = self.selenium.find_element_by_name("model")
        model_input.send_keys('2650')

        aggregate_code_input = self.selenium.find_element_by_name(
            "aggregate_code")
        aggregate_code_input.send_keys('11')

        current_url = self.selenium.current_url

        #self.selenium.set_window_size(2000, 950)
        decode_button = self.selenium.find_element_by_id('btn-decode-6869')
        #decode_button = WebDriverWait(
        #    self.selenium, 10).until(
        #        EC.element_to_be_clickable((By.ID, "btn-decode-6869")))

        #actions = ActionChains(self.selenium)
        #actions.move_to_element(decode_button).perform()

        decode_button.location_once_scrolled_into_view
        decode_button.click()

        WebDriverWait(self.selenium, 15).until(EC.url_changes(current_url))
        new_url = self.selenium.current_url
        print(new_url)

        #production_date = self.selenium.find_element_by_name("production-date")
        production_date = WebDriverWait(
            self.selenium, 10).until(
                EC.element_to_be_clickable((By.ID, "production-date")))
        self.assertEqual(production_date.text, "Feb 07, 1968")
