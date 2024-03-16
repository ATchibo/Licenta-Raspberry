import threading
import time
from datetime import datetime

from domain.RaspberryInfo import RaspberryInfoBuilder, RaspberryInfo
from domain.logging.MessageType import MessageType
from utils.datetime_utils import get_current_datetime_tz
from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.local_storage_controller import LocalStorageController
from utils.moisture_controller import MoistureController
from utils.pump_controller import PumpController
from utils.remote_requests import RemoteRequests


class RaspberryController:
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

        self.moisture_controller = MoistureController(channel=1)
        self.pump_controller = PumpController(pin=4, liters_per_second=0.1)

        self._send_watering_updates_interval_ms = 1000
        self._max_watering_time_sec = 30
        self.watering_time = 0  # seconds
        self.liters_sent = 0  # liters
        self.watering_time_start = 0  # time
        self._send_watering_updates_thread = None
        self._send_watering_updates_event = threading.Event()
        self._while_watering_callback_function = None

        self.raspberry_id = getserial()

        self._watering_cycle_start_time = None
        self._watering_manually = False

        self._default_raspberry_info = (RaspberryInfoBuilder()
                                        .with_id(self.raspberry_id)
                                        .with_name("Raspberry" + str(hash(self.raspberry_id))[0:6])
                                        .with_location("Not set")
                                        .with_description("Not set")
                                        .with_notifiable_messages({})
                                        .build()
                                        )

        if LocalStorageController().get_raspberry_info() is None:
            LocalStorageController().save_raspberry_info(self._default_raspberry_info)

    def set_watering_program(self, watering_program):
        self._watering_program = watering_program

    def get_moisture_percentage(self):
        return self.moisture_controller.get_moisture_percentage()

    def check_need_for_watering(self):
        if self.get_moisture_percentage() < self._watering_program.get_min_moisture():
            self.pump_controller.start_watering_for_liters(self._watering_program.get_liters_needed())

    def _log_manual_watering_cycle(self):
        EventLogger().add_manual_watering_cycle_message(
            self._watering_cycle_start_time,
            self.watering_time,
            self.liters_sent
        )

    def _log_auto_watering_cycle(self):
        EventLogger().add_auto_watering_cycle_message(
            self._watering_cycle_start_time,
            self.watering_time,
            self.liters_sent
        )

    def start_watering(self) -> bool:
        if self.pump_controller.start_watering():
            self.start_sending_watering_updates()
            self._watering_manually = True
            return True
        return False

    def manual_stop_watering(self) -> bool:
        self.pump_controller.stop_watering_event.set()

        if self.pump_controller.stop_watering():
            self.stop_sending_watering_updates()
            self._send_stop_watering_message()

            if self._watering_manually:
                self._log_manual_watering_cycle()
                self._watering_manually = False

            return True
        return False

    def water_for_liters(self, liters):
        # print("Watering for", liters, "liters")
        self.start_sending_watering_updates()
        self.pump_controller.start_watering_for_liters(liters)
        self.stop_sending_watering_updates()
        self._send_stop_watering_message()

        self._log_auto_watering_cycle()

        # print("Watering finished - raspi controller")

    def start_listening_for_watering_now(self):
        RemoteRequests().add_watering_now_listener(callback=self._watering_now_callback_for_incoming_messages)

    def _watering_now_callback_for_incoming_messages(self, doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            if doc.exists:
                # Handle the updated data
                updated_data = doc.to_dict()
                # Update your UI or perform necessary actions
                # print(f"Document data: {updated_data}")

                if updated_data["command"] is not None:
                    if updated_data["command"] == "start_watering":
                        if self.pump_controller.is_watering:
                            return

                        self.pump_controller.start_watering()
                        self.start_sending_watering_updates()

                    elif updated_data["command"] == "stop_watering":
                        if not self.pump_controller.is_watering:
                            return

                        self.pump_controller.stop_watering()
                        self.stop_sending_watering_updates()

                        if self._while_watering_callback_function is not None:
                            self._while_watering_callback_function(
                                is_watering=self.pump_controller.is_watering,
                                watering_time=round(self.watering_time),
                                liters_sent=round(self.liters_sent, 2)
                            )

                        self._log_manual_watering_cycle()

            else:
                print("Current data: null")

    def stop_listening_for_watering_now(self):
        RemoteRequests().unsubscribe_watering_now_listener()

    def start_sending_watering_updates(self):
        self._watering_cycle_start_time = get_current_datetime_tz()

        self._send_watering_updates_event.set()
        self._send_watering_updates_thread = threading.Thread(target=self._send_watering_updates_worker)
        self._send_watering_updates_thread.start()

    def stop_sending_watering_updates(self):
        self.watering_time = time.time() - self.watering_time_start  # seconds
        self.liters_sent = self.watering_time * self.pump_controller.pump_capacity  # seconds * liters/second -> liters

        self._send_watering_updates_event.clear()
        if self._send_watering_updates_thread is not None and self._send_watering_updates_thread.is_alive():
            self._send_watering_updates_thread.join()

        self._update_info_for_watering_callback()

    def _send_watering_updates_worker(self):
        self.watering_time_start = time.time()
        TIMEOUT = self._send_watering_updates_interval_ms / 1000.0

        while self._send_watering_updates_event.is_set():
            self._send_watering_update_function()
            time.sleep(TIMEOUT)

    def _send_watering_update_function(self):
        self.watering_time = time.time() - self.watering_time_start  # seconds
        self.liters_sent = self.watering_time * self.pump_controller.pump_capacity  # seconds * liters/second -> liters

        if self.watering_time >= self._max_watering_time_sec:
            def _stop_watering():
                self._send_stop_watering_message()
                self._update_info_for_watering_callback()

            threading.Thread(target=_stop_watering()).start()

            return
        else:
            self._update_current_watering_info()
            self._update_info_for_watering_callback()

    def _send_stop_watering_message(self):
        RemoteRequests().update_watering_info(
            'stop_watering',
            round(self.liters_sent, 2),
            round(self.watering_time)
        )

        self.stop_sending_watering_updates()
        self.pump_controller.stop_watering()

    def _update_current_watering_info(self):
        RemoteRequests().update_watering_info(
            'start_watering',
            round(self.liters_sent, 2),
            round(self.watering_time)
        )

    def _update_info_for_watering_callback(self):
        if self._while_watering_callback_function is not None:

            # print("is_watering:", self.pump_controller.is_watering)

            self._while_watering_callback_function(
                is_watering=self.pump_controller.is_watering,
                watering_time=round(self.watering_time),
                liters_sent=round(self.liters_sent, 2)
            )

    def set_callback_for_watering_updates(self, callback):
        self._while_watering_callback_function = callback

    def get_raspberry_info(self) -> RaspberryInfo:
        _raspberry_info = RemoteRequests().get_raspberry_info()
        if _raspberry_info is not None:
            return _raspberry_info
        return self._default_raspberry_info

    def update_raspberry_notification_info(self, message_type: MessageType, value):
        self._default_raspberry_info.set_notifiable_message(message_type, value)
        RemoteRequests().update_raspberry_notifiable_message(message_type, value)
