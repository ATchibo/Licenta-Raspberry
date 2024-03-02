from datetime import datetime

from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.scrollview import MDScrollView
from matplotlib import pyplot as plt

from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial

Builder.load_file("components/homepage/watering_history_view.kv")


class WateringHistoryView(MDBoxLayout):
    def __init__(self, **kwargs):
        super(WateringHistoryView, self).__init__(**kwargs)

        self.orientation = "vertical"
        self.size_hint_y = 1

        self._logs = {}
        self._raspberry_id = getserial()

        Clock.schedule_once(self.populate_list, 0.1)

    def populate_list(self, *args):
        ml = self.ids.watering_history_list

        self._logs, success = FirebaseController().get_log_messages(self._raspberry_id)

        if not success:
            ml.add_widget(
                OneLineListItem(
                    text="Error fetching logs"
                )
            )
            return

        if len(self._logs) == 0:
            ml.add_widget(
                OneLineListItem(
                    text="No logs found"
                )
            )
            return

        for key in self._logs:
            datetime_object = datetime.strptime(key, "%Y-%m-%d %H:%M:%S.%f")
            formatted_date_time = datetime_object.strftime("%d-%m-%Y %H:%M")
            text = f"{formatted_date_time}: {self._logs[key]}"

            # TODO: maybe convert to a recyclerview when im bored

            ml.add_widget(
                TwoLineListItem(
                    text=text
                )
            )

    def refresh_data(self, *args):
        def refresh_callback(interval):
            print("Refreshing data")
            self.populate_list()
            self.ids.refresh_layout.refresh_done()

        Clock.schedule_once(refresh_callback, 0.5)
