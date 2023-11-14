from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt


Builder.load_file("pages/home_page.kv")


class HomePage(MDScreen):
    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)

    def on_enter(self, *args):
        Clock.schedule_once(self.add_matplotlib_widget, 0.1)

    def add_matplotlib_widget(self, dt):
        print(self.ids)
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

