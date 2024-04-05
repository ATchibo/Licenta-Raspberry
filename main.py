from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.scrollview import MDScrollView

from pages.connect_page import ConnectPage
from pages.home_page import HomePage
from pages.settings_page import SettingsPage
from pages.calibration_page import CalibrationPage
from components.calibration.moisture_calibration_view import MoistureCalibrationView
from components.calibration.pump_calibration_view import PumpCalibrationView
from components.calibration.depth_calibration_view import DepthCalibrationView
from utils.WateringProgramController import WateringProgramController
from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.notification_login_controller import NotificationLoginController
from utils.moisture_measurement_controller import MoistureMeasurementController
from utils.raspberry_controller import RaspberryController
from utils.remote_requests import RemoteRequests


class ContentNavigationDrawer(MDScrollView):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class PlantBuddyApp(MDApp):
    def build(self):
        self.root = Builder.load_file("home.kv")
        # Window.size = (800, 480)
        Window.fullscreen = 'auto'
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "400"


if __name__ == '__main__':
    # try:
    #     if FirebaseController().anonymous_login():
    #         RaspberryController().start_listening_for_watering_now()
    #         WateringProgramController().perform_initial_setup()
    #         EventLogger().perform_initial_setup()
    #         print("Logged in")
    #     else:
    #         print("Not logged in")
    # except Exception as e:
    #     print("Failed to auto login: " + str(e))

    FirebaseController().attach(RaspberryController())
    FirebaseController().attach(WateringProgramController())
    FirebaseController().attach(EventLogger())

    try:
        NotificationLoginController().try_initial_login()
    except Exception as e:
        print("Failed to auto login: " + str(e))

    MoistureMeasurementController().start_moisture_check_thread(12 * 60 * 60)  # 12 hours

    PlantBuddyApp().run()
