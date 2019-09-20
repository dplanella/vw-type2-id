"""
A simple functional headless UI test with pyvirtualdisplay and selenium
"""

from django.test import LiveServerTestCase
from pyvirtualdisplay import Display
from selenium import webdriver


class ExampleTestCase(LiveServerTestCase):
    LATE_BAY_01_CHASSIS = "92023025"
    LATE_BAY_02_CHASSIS = "22138101"
    EARLY_BAY_01_CHASSIS = "9123833"

    def setUp(self):
        # Start the display
        self.vdisplay = Display(visible=0, size=(1024, 768))
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
        decode_button = self.selenium.find_element_by_id('btn-decode')
        chassis_number_short_input = self.selenium.find_element_by_name("id_chassis_number_short")
        chassis_number_short_input.send_keys(self.EARLY_BAY_01_CHASSIS)

        m_codes_2_input = self.selenium.find_element_by_name("m_codes_2")
        m_codes_2_input.send_keys('408 095 504 507')

        paint_and_interior_input = self.selenium.find_element_by_name("paint_and_interior")
        paint_and_interior_input.send_keys('383851')

        production_date_input = self.selenium.find_element_by_name("production_date")
        production_date_input.send_keys('072')

        export_destination_input = self.selenium.find_element_by_name("export_destination")
        export_destination_input.send_keys('PG')

        model_input = self.selenium.find_element_by_name("model")
        model_input.send_keys('2650')

        aggregate_code_input = self.selenium.find_element_by_name("aggregate_code")
        aggregate_code_input.send_keys('11')

        decode_button.click()

        production_date = self.selenium.find_element_by_name("production_date")
        self.assertEqual(production_date.text, "Feb 07, 1968")
