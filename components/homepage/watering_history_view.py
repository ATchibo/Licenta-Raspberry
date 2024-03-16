from datetime import datetime

from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import MDList, OneLineListItem, TwoLineListItem
from kivymd.uix.scrollview import MDScrollView
from matplotlib import pyplot as plt

from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial

Builder.load_file("components/homepage/watering_history_view.kv")


class WateringHistoryView(MDBoxLayout):

    def __init__(self, **kwargs):
        super(WateringHistoryView, self).__init__(**kwargs)

        self.orientation = "vertical"
        self.size_hint_y = 1

        self._raspberry_id = getserial()
        self.refreshing = False

        Clock.schedule_once(self._init_setup, 0.1)

    def _init_setup(self, *args):
        self._populate_list()
        EventLogger().set_gui_log_update_callback(self._populate_list_callback)

    def _populate_list(self):
        rv = self.ids.rv

        _logs, success = EventLogger().load_log_messages()

        if not success:
            rv.data = [{"text": "Error fetching logs"}]
            return

        if len(_logs) == 0:
            rv.data = [{"text": "No logs available"}]
            return

        self._add_logs_to_recyclerview(_logs)

    def _populate_list_callback(self, logs):
        rv = self.ids.rv

        if logs is None or len(logs) == 0:
            rv.data = [{"text": "No logs available"}]
            return

        self._add_logs_to_recyclerview(logs)

    def _add_logs_to_recyclerview(self, logs):
        rv = self.ids.rv

        _data = []

        for log in logs:
            date = log.get_timestamp()
            message = log.get_message()

            formatted_date_time = date.strftime("%d-%m-%Y %H:%M")
            text = f"{formatted_date_time}: {message}"
            _data.append({"text": text})

        rv.data = _data

    def refresh_data(self, *args):
        def refresh_callback(interval):
            self.refreshing = True
            self._populate_list()
            self.refreshing = False

        Clock.schedule_once(refresh_callback, 0.5)
