from datetime import datetime, timedelta

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy_garden.graph import Graph, MeshLinePlot
from kivymd.uix.boxlayout import MDBoxLayout
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial

Builder.load_file("components/homepage/graph_view.kv")


class GraphView(MDBoxLayout):
    def __init__(self, **kwargs):
        super(GraphView, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, 1)

        self.firebase_controller = FirebaseController()

        self.menu = None
        self.plot = None
        self.dropdown = None
        self.dropdown_items = ["Last 24h", "Last 7 days", "Last 30 days"]

        self.end_datetime = datetime.now()
        self.start_datetime = self.end_datetime - timedelta(days=7)

        self.graph_theme = {
            'label_options': {
                'color': [1, 0, 0, 1],
                'bold': True
            },
            'tick_color': [1, 0, 0, 1],
            'border_color': [1, 0, 0, 1],
        }

        Clock.schedule_once(self.add_graph, 0.1)
        Clock.schedule_once(self.init_dropdown, 0.1)

    def add_graph(self, *args):
        self.update_plot()

    def update_plot(self):
        graph_box = self.ids.graph_box
        graph_box.clear_widgets()

        graph = Graph(
            xlabel='Time',
            ylabel='Moisture (%)',
            x_ticks_minor=1,
            x_ticks_major=1,
            y_ticks_major=1,
            y_grid_label=True,
            x_grid_label=True,
            padding=5,
            x_grid=False,
            y_grid=False,
            xmin=0,
            xmax=10,
            ymin=0,
            ymax=100,
            **self.graph_theme
        )

        moisture_info_list = self.firebase_controller.get_moisture_info_for_rasp_id(getserial(), self.start_datetime,
                                                                                    self.end_datetime)

        points = []
        for moisture_info in moisture_info_list:
            print("Moisture info value: " + str(moisture_info["measurementValuePercent"]))
            points.append((moisture_info_list.index(moisture_info), moisture_info["measurementValuePercent"]))
            # points.append((moisture_info["measurementTime"].timestamp(), moisture_info["measurementValuePercent"]))

        self.plot = MeshLinePlot(color=[1, 0, 0, 1])
        self.plot.points = points

        graph.add_plot(self.plot)
        graph_box.add_widget(graph)

    def init_dropdown(self, *args):
        self.dropdown = DropDown()

        for item in self.dropdown_items:
            btn = Button(text=item, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.select_item(self.dropdown_items.index(btn.text)))
            self.dropdown.add_widget(btn)

        mainbutton = self.ids.mainbutton
        mainbutton.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', self.dropdown_items[x]))

    def select_item(self, index):
        print(f"Selected item: {index}")
        self.dropdown.select(index)

        self.end_datetime = datetime.now()

        if index == 0:
            self.start_datetime = self.end_datetime - timedelta(days=1)
        elif index == 1:
            self.start_datetime = self.end_datetime - timedelta(days=7)
        elif index == 2:
            self.start_datetime = self.end_datetime - timedelta(days=30)

        self.update_plot()

    # def set_item(self, text_item):
    #     self.ids.drop_item.set_item(text_item)
    #     self.menu.dismiss()
