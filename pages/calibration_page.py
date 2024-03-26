from kivy.app import App
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

Builder.load_file("pages/calibration_page.kv")


class CalibrationPage(MDScreen):
    def __init__(self, **kwargs):
        super(CalibrationPage, self).__init__(**kwargs)

    def on_enter(self, *args):
        pass

    def on_leave(self, *args):
        pass
