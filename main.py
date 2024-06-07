from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.scrollview import MDScrollView

from utils.WateringProgramController import WateringProgramController
from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.moisture_measurement_controller import MoistureMeasurementController
from utils.notification_login_controller import NotificationLoginController
from utils.raspberry_controller import RaspberryController


class ContentNavigationDrawer(MDScrollView):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class PlantBuddyApp(MDApp):
    def build(self):
        self.root = Builder.load_file("home.kv")
        Window.fullscreen = 'auto'
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "400"


if __name__ == '__main__':
    FirebaseController().attach(RaspberryController())
    FirebaseController().attach(WateringProgramController())
    FirebaseController().attach(EventLogger())

    try:
        NotificationLoginController().try_send_login_notification()
    except Exception as e:
        print("Failed to auto login: " + str(e))

    MoistureMeasurementController().start_moisture_check_thread(12 * 60 * 60)  # 12 hours

    PlantBuddyApp().run()
