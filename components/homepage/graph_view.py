from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from matplotlib import pyplot as plt


Builder.load_file("components/homepage/graph_view.kv")


class GraphView(MDBoxLayout):
    def __init__(self, **kwargs):
        super(GraphView, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = 1
        Clock.schedule_once(self.add_matplotlib_widget, 0.1)

    def add_matplotlib_widget(self, *args):
        print("rahat")
        graph_box = self.ids.graph_box
        graph_box.clear_widgets()  # Clear any existing widgets

        # Create a Matplotlib figure and add it to the graph_box
        figure = self.get_graph()
        canvas = FigureCanvasKivyAgg(figure=figure)
        print(canvas)
        graph_box.add_widget(canvas)

    def get_graph(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 12, 6, 9, 15]

        plt.plot(x, y)
        plt.ylabel("This is MY Y Axis")
        plt.xlabel("X Axis")

        plt.tight_layout(pad=5)

        return plt.gcf()

