from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.scrollview import MDScrollView

from pages.connect_page import ConnectPage
from pages.home_page import HomePage
from pages.settings_page import SettingsPage

class ContentNavigationDrawer(MDScrollView):
    screen_manager = ObjectProperty()
    nav_drawer = ObjectProperty()


class PlantBuddyApp(MDApp):
    def build(self):
        self.root = Builder.load_file("home.kv")
        Window.size = (800, 480)
        # Window.fullscreen = 'auto'

if __name__ == '__main__':
    PlantBuddyApp().run()
