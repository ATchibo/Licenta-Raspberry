from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineIconListItem, OneLineListItem
from kivymd.uix.menu import MDDropdownMenu
from matplotlib import pyplot as plt


Builder.load_file("components/homepage/graph_view.kv")


class GraphView(MDBoxLayout):
    def __init__(self, **kwargs):
        super(GraphView, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, 1)

        self.menu = None

        Clock.schedule_once(self.add_matplotlib_widget, 0.1)
        Clock.schedule_once(self.init_dropdown, 0.1)

    def add_matplotlib_widget(self, *args):
        graph_box = self.ids.graph_box
        graph_box.clear_widgets()  # Clear any existing widgets

        # Create a Matplotlib figure and add it to the graph_box
        figure = self.get_graph()
        canvas = FigureCanvasKivyAgg(figure=figure)
        graph_box.add_widget(canvas)

    def get_graph(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 12, 6, 9, 15]

        plt.plot(x, y)
        plt.ylabel("This is MY Y Axis")
        plt.xlabel("X Axis")

        plt.tight_layout(pad=5)

        return plt.gcf()

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
        self.menu.dismiss()

