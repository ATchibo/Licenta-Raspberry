from math import sin

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy_garden.graph import Graph, MeshLinePlot
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from matplotlib import pyplot as plt


Builder.load_file("components/homepage/graph_view.kv")


class GraphView(MDBoxLayout):
    def __init__(self, **kwargs):
        super(GraphView, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, 1)

        self.menu = None

        Clock.schedule_once(self.add_graph, 0.1)
        Clock.schedule_once(self.init_dropdown, 0.1)

    def add_graph(self, *args):
        graph_box = self.ids.graph_box
        graph_box.clear_widgets()

        graph_theme = {
            'label_options': {
                'color': [1, 0, 0, 1],  # color of tick labels and titles
                'bold': True},
            'tick_color': [1, 0, 0, 1],  # ticks and grid
            'border_color': [1, 0, 0, 1]
        }  # border drawn around each graph

        graph = Graph(xlabel='X axis', ylabel='Y axis', x_ticks_minor=5,
                      x_ticks_major=25, y_ticks_major=1,
                      y_grid_label=True, x_grid_label=True, padding=5,
                      x_grid=True, y_grid=True, xmin=-0, xmax=100, ymin=-1, ymax=1,
                      **graph_theme)
        plot = MeshLinePlot(color=[1, 0, 0, 1])
        plot.points = [(x, sin(x / 10.)) for x in range(0, 101)]
        graph.add_plot(plot)

        graph_box.add_widget(graph)

    def get_graph(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 12, 6, 9, 15]

        plt.plot(x, y)
        plt.ylabel("This is MY Y Axis")
        plt.xlabel("X Axis")

        plt.tight_layout(pad=5)

        return plt.gcf()

    def init_dropdown(self, *args):
        dropdown = DropDown()
        for index in range(10):
            btn = Button(text='Value %d' % index, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)

        mainbutton = self.ids.mainbutton
        mainbutton.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', x))

    def set_item(self, text_item):
        self.ids.drop_item.set_item(text_item)
        self.menu.dismiss()

