from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from components.homepage.graph_view import GraphView
from components.homepage.watering_history_view import WateringHistoryView
from components.homepage.watering_options_view import WateringOptionsView

Builder.load_file("pages/home_page.kv")


class HomePage(MDScreen):
    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)
