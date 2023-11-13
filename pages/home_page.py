from kivy.lang import Builder
from kivymd.uix.screen import MDScreen


Builder.load_file("pages/home_page.kv")


class HomePage(MDScreen):
    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)

