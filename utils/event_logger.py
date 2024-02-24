import threading

from domain.logging.ManualWateringCycleMessage import ManualWateringCycleMessage
from domain.logging.MoistureMeasurementMessage import MoistureMeasurementMessage
from utils.firebase_controller import FirebaseController
from domain.logging.AutoWateringCycleMessage import AutoWateringCycleMessage


class EventLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self._log_messages = []
        self._notifiable_messages = {}

    def load_log_messages(self):
        self._log_messages = FirebaseController().get_log_messages()

    def load_notifiable_messages(self):
        self._notifiable_messages = FirebaseController().get_notifiable_messages()

    def load_initial_data(self):
        self.load_log_messages()
        self.load_notifiable_messages()

    def _add_log_message(self, log_message):
        if FirebaseController().add_log_message(log_message):
            self._log_messages.append(log_message)

            if self._notifiable_messages.get(log_message.get_level()) is True:
                FirebaseController().send_notification(log_message.get_message())

    def add_auto_watering_cycle_message(self, start_time, end_time, water_amount):
        self._add_log_message(AutoWateringCycleMessage(start_time, end_time, water_amount))

    def add_manual_watering_cycle_message(self, start_time, end_time, water_amount):
        self._add_log_message(ManualWateringCycleMessage(start_time, end_time, water_amount))

    def add_moisture_measurement_message(self, moisture_level, date_time):
        self._add_log_message(MoistureMeasurementMessage(moisture_level, date_time))
