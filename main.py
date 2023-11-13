from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from pages.connect_page import ConnectPage
from pages.home_page import HomePage


class WindowManager(MDScreenManager):
    pass


# kv = Builder.load_file("home.kv")


class PlantBuddyApp(MDApp):
    def build(self):
        self.root = Builder.load_file("home.kv")
        Window.size = (480, 320)
        # return kv


if __name__ == '__main__':
    PlantBuddyApp().run()
