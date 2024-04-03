import threading
from datetime import datetime

from utils.datetime_utils import get_current_datetime_tz
from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.moisture_controller import MoistureController
from utils.remote_requests import RemoteRequests


class MoistureMeasurementController:
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

        self._raspberry_id = getserial()
        self._moisture_check_interval_sec = None

        self._moisture_controller = MoistureController(channel=1)

        self._moisture_check_thread = None
        self._moisture_check_thread_finished = threading.Event()

    def get_current_moisture_percentage(self):
        return self._moisture_controller.get_moisture_percentage()

    def get_moisture_check_interval_sec(self):
        return self._moisture_check_interval_sec

    def start_moisture_check_thread(self, interval_sec=1000*10):
        self._stop_moisture_check_thread()

        self._moisture_check_interval_sec = interval_sec

        self._moisture_check_thread = threading.Thread(
            target=self._moisture_check_thread_function,
            daemon=True
        )

        self._moisture_check_thread.start()

    def _stop_moisture_check_thread(self):
        self._moisture_check_thread_finished.set()
        if self._moisture_check_thread is not None:
            self._moisture_check_thread.join()
        self._moisture_check_thread_finished.clear()

    def _moisture_check_thread_function(self):
        while not self._moisture_check_thread_finished.is_set():
            self._moisture_check_thread_finished.wait(self._moisture_check_interval_sec)
            if self._moisture_check_thread_finished.is_set():
                return

            _moisture_perc = self._moisture_controller.get_moisture_percentage()
            _measurement_time = get_current_datetime_tz()

            RemoteRequests().add_moisture_percentage_measurement(_moisture_perc, _measurement_time)
            EventLogger().add_moisture_measurement_message(_moisture_perc, _measurement_time)
