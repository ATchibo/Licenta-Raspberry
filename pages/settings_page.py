from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

Builder.load_file("pages/settings_page.kv")


class SettingsPage(MDScreen):
    def __init__(self, **kwargs):
        super(SettingsPage, self).__init__(**kwargs)
