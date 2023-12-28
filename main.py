from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.scrollview import MDScrollView

from pages.connect_page import ConnectPage
from pages.home_page import HomePage
from pages.settings_page import SettingsPage
from utils.firebase_controller import FirebaseController


class ContentNavigationDrawer(MDScrollView):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class PlantBuddyApp(MDApp):
    def build(self):
        self.root = Builder.load_file("home.kv")
        # Window.size = (1200, 720)
        Window.fullscreen = 'auto'
        self.theme_cls.primary_palette = "Green"


if __name__ == '__main__':
    FirebaseController()
    PlantBuddyApp().run()
