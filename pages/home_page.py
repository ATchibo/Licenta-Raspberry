from kivy.lang import Builder
from kivymd.uix.screen import MDScreen
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
import matplotlib.pyplot as plt


Builder.load_file("pages/home_page.kv")


class HomePage(MDScreen):
    def __init__(self, **kwargs):
        super(HomePage, self).__init__(**kwargs)

        print("HomePage init")
        print(self.ids)

        # graph_box = self.ids.graph_box
        # graph_box.add_widget(FigureCanvasKivyAgg(figure=self.get_graph()))

    def get_graph(self):
        x = [1, 2, 3, 4, 5]
        y = [5, 12, 6, 9, 15]

        plt.plot(x, y)
        plt.ylabel("This is MY Y Axis")
        plt.xlabel("X Axis")

        return plt.gcf()

