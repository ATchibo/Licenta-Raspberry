from datetime import timedelta

import matplotlib.pyplot as plt
from kivy.clock import Clock
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.boxlayout import MDBoxLayout
from tzlocal import get_localzone

from utils.datetime_utils import get_current_datetime_tz
from utils.remote_requests import RemoteRequests

Builder.load_file("components/homepage/graph_view.kv")


class GraphView(MDBoxLayout):
    def __init__(self, **kwargs):
        super(GraphView, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, 1)

        self.menu = None
        self.dropdown = None
        self.dropdown_items = ["Last 24h", "Last 7 days", "Last 30 days"]

        self.end_datetime = get_current_datetime_tz()
        self.start_datetime = self.end_datetime - timedelta(days=1)

        Clock.schedule_once(self.update_plot, 0.1)
        Clock.schedule_once(self.init_dropdown, 0.1)

    def on_enter(self, *args):
        print("GraphView on_enter")
        self.update_plot()

    def update_plot(self, *args):
        graph_box = self.ids.graph_box
        graph_box.clear_widgets()

        fig, ax = plt.subplots()

        moisture_info_list = RemoteRequests().get_moisture_info(self.start_datetime, self.end_datetime)

        if moisture_info_list is None or len(moisture_info_list) == 0:
            ax.plot(["No data"], [0])
            ax.grid()
            ax.set_xlabel('Time')
            ax.set_ylabel('Moisture (%)')
            plt.tight_layout(pad=3.0)
            graph_box.add_widget(FigureCanvasKivyAgg(plt.gcf()))
            return

        moisture_info_list = sorted(moisture_info_list, key=lambda x: x["measurementTime"])
        timestamps = [moisture_info["measurementTime"].astimezone(get_localzone()) for moisture_info in
                      moisture_info_list]
        values = [int(moisture_info["measurementValuePercent"]) for moisture_info in moisture_info_list]

        ax.grid()
        ax.set_ylabel('Moisture (%)')

        ax.set_ylim(0, 100)

        if len(timestamps) > 20:
            _rotation = 50
            _fontsize = 8
            _format = "%d.%m %H:%M"
        elif len(timestamps) > 10:
            _rotation = 30
            _fontsize = 9
            _format = "%d.%m %H:%M"
        else:
            _rotation = 0
            _fontsize = 10
            _format = "%d %b\n%H:%M"

        x_labels = [timestamp.strftime(_format) for timestamp in timestamps]
        y_values = values
        x_positions = range(len(x_labels))
        x_ticks = range(0, len(x_labels))

        ax.plot(x_positions, y_values, color='red', marker='o')
        ax.set_xticks(x_ticks)
        ax.set_xticklabels(x_labels, rotation=_rotation, ha="right", fontsize=_fontsize)
        for zip_obj in zip(x_positions, y_values):
            ax.text(zip_obj[0], zip_obj[1], str(zip_obj[1]), ha='center', va='bottom')

        plt.tight_layout(pad=2.9, w_pad=-2.5)

        graph_box.add_widget(FigureCanvasKivyAgg(plt.gcf()))

    def init_dropdown(self, *args):
        self.dropdown = DropDown()

        for item in self.dropdown_items:
            btn = Button(text=item, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: self.select_item(self.dropdown_items.index(btn.text)))
            btn.padding = (10, 0)
            self.dropdown.add_widget(btn)

        mainbutton = self.ids.mainbutton
        mainbutton.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', self.dropdown_items[x]))

    def select_item(self, index):
        self.dropdown.select(index)

        self.end_datetime = get_current_datetime_tz()

        if index == 0:
            self.start_datetime = self.end_datetime - timedelta(days=1)
        elif index == 1:
            self.start_datetime = self.end_datetime - timedelta(days=7)
        elif index == 2:
            self.start_datetime = self.end_datetime - timedelta(days=30)

        self.update_plot()

    def refresh_data(self, *args):
        Clock.schedule_once(self.update_plot, 0.1)
