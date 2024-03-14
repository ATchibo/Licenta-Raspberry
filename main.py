from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.scrollview import MDScrollView

from pages.connect_page import ConnectPage
from pages.home_page import HomePage
from pages.settings_page import SettingsPage
from utils.WateringProgramController import WateringProgramController
from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.login_controller import LoginController
from utils.moisture_measurement_controller import MoistureMeasurementController
from utils.raspberry_controller import RaspberryController


class ContentNavigationDrawer(MDScrollView):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class PlantBuddyApp(MDApp):
    def build(self):
        self.root = Builder.load_file("home.kv")
        # Window.size = (800, 480)
        Window.fullscreen = 'auto'
        self.theme_cls.primary_palette = "Green"


if __name__ == '__main__':
    try:
        if FirebaseController().anonymous_login():
            RaspberryController().start_listening_for_watering_now()
            WateringProgramController().perform_initial_setup()
            EventLogger().perform_initial_setup()
            print("Logged in")
        else:
            print("Not logged in")
    except Exception as e:
        print("Failed to auto login: " + str(e))

    #TODO: revert to try login

    # try:
    #     LoginController().try_initial_login()
    # except Exception as e:
    #     print("Failed to auto login: " + str(e))

    MoistureMeasurementController().start_moisture_check_thread(1000 * 60 * 60 * 12)

    PlantBuddyApp().run()

    # TODO: add listener and sorting for logs
