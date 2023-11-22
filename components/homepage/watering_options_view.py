from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from matplotlib import pyplot as plt


Builder.load_file("components/homepage/watering_options_view.kv")


class WateringOptionsView(MDBoxLayout):
    def __init__(self, **kwargs):
        super(WateringOptionsView, self).__init__(**kwargs)
        self.menu = None
        self.orientation = "vertical"
        self.size_hint_y = 1
        Clock.schedule_once(self.init, 0.1)

    def init(self, *args):
        self.init_dropdown(*args)

    def init_dropdown(self, *args):

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"Item {i}",
                "on_release": lambda x=f"Item {i}": self.set_item(x),
            } for i in range(5)
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.drop_item,
            items=menu_items,
            position="center",
            width_mult=2,
        )

        self.menu.bind()

    def set_item(self, text_item):
        self.ids.drop_item.set_item(text_item)
        # self.menu.dismiss()



