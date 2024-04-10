import threading
import time
from datetime import datetime

from domain.RaspberryInfo import RaspberryInfoBuilder, RaspberryInfo
from domain.logging.MessageType import MessageType
from domain.observer.ObserverNotificationType import ObserverNotificationType
from domain.observer.Observer import Observer
from utils.datetime_utils import get_current_datetime_tz
from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.local_storage_controller import LocalStorageController
from utils.moisture_controller import MoistureController
from utils.pump_controller import PumpController
from utils.remote_requests import RemoteRequests
from utils.water_depth_measurement_controller import WaterDepthMeasurementController


class RaspberryController(Observer):
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

        _liter_per_second = LocalStorageController().get_pump_capacity()
        self.pump_controller = PumpController(pin=4, liters_per_second=_liter_per_second)

        self.water_depth_measurement_controller = WaterDepthMeasurementController()

        self._send_watering_updates_interval_ms = 1000
        self._max_watering_time_sec = 30
        self.watering_time = 0  # seconds
        self.liters_sent = 0  # liters
        self.watering_time_start = 0  # time
        self._send_watering_updates_thread = None
        self._send_watering_updates_event = threading.Event()
        self._while_watering_callback_function = None

        self.raspberry_id = getserial()
        self._watering_program = None

        self._watering_cycle_start_time = None
        self._watering_manually = False

        self._raspberry_info = (RaspberryInfoBuilder()
                                .with_id(self.raspberry_id)
                                .with_name("Raspberry" + str(hash(self.raspberry_id))[0:6])
                                .with_location("Not set")
                                .with_description("Not set")
                                .with_notifiable_messages({})
                                .build()
                                )

        self._load_raspberry_info_local_storage()

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

    def _log_no_water_in_tank(self):
        EventLogger().add_no_water_in_tank_message(datetime.now())

    def _log_water_level_after_watering(self):
        if self.water_depth_measurement_controller.is_water_tank_low():
            EventLogger().add_water_level_after_watering_message(
                self.water_depth_measurement_controller.get_current_water_volume(),
                datetime.now()
            )

    def start_watering(self) -> bool:
        if self.pump_controller.is_watering:
            return False

        if self.water_depth_measurement_controller.is_water_tank_empty():
            self._log_no_water_in_tank()
            self._send_stop_watering_message()
            return False

        if self.pump_controller.start_watering():
            self.start_sending_watering_updates()
            self._watering_manually = True
            return True
        return False

    def manual_stop_watering(self) -> bool:
        if not self.pump_controller.is_watering:
            return False

        if not self._watering_manually:
            self.pump_controller.stop_watering_event.set()
            return True

        if self.pump_controller.stop_watering():
            self.stop_sending_watering_updates()
            self._send_stop_watering_message()
            self._watering_manually = False
            self._log_manual_watering_cycle()
            self._log_water_level_after_watering()

            return True

        return False

    def water_for_liters(self, liters):
        if self.pump_controller.is_watering:
            return False

        if WaterDepthMeasurementController().is_water_tank_empty():
            self._log_no_water_in_tank()
            return False

        self.start_sending_watering_updates()
        self.pump_controller.start_watering_for_liters(liters)
        self.stop_sending_watering_updates()
        self._send_stop_watering_message()

        self._log_auto_watering_cycle()
        self._log_water_level_after_watering()

        return True

    def start_listening_for_watering_now(self):
        RemoteRequests().add_watering_now_listener(callback=self._watering_now_callback_for_incoming_messages)

    def _watering_now_callback_for_incoming_messages(self, doc_snapshot, changes, read_time):
        for change in changes:
            changed_doc = change.document
            updated_data = changed_doc.to_dict()

            print("Watering callback updated data: ", updated_data)

            # check for moisture request
            if "soilMoisture" in updated_data.keys():
                if "REQUEST" in str(updated_data["soilMoisture"]):
                    print("Sending moisture info")
                    self._send_moisture_info()

            if "waterTankVolume" in updated_data.keys():
                if "REQUEST" in str(updated_data["waterTankVolume"]):
                    print("Sending water volume info")
                    self._send_water_tank_volume_info()

            # check for watering now command
            if "command" in updated_data.keys():
                print("Is watering:", self.pump_controller.is_watering)
                if updated_data["command"] == "start_watering" and not self.pump_controller.is_watering:
                    RemoteRequests().update_watering_info('processing', 0.0, 0)
                    self.start_watering()

                elif updated_data["command"] == "stop_watering" and self.pump_controller.is_watering:
                    self.manual_stop_watering()
                    if self._while_watering_callback_function is not None:
                        self._while_watering_callback_function(
                            is_watering=self.pump_controller.is_watering,
                            watering_time=round(self.watering_time),
                            liters_sent=round(self.liters_sent, 2)
                        )

                    # if not self.pump_controller.is_watering:
                    #     return
                    #
                    # self.pump_controller.stop_watering()
                    # self.stop_sending_watering_updates()
                    #
                    # if self._while_watering_callback_function is not None:
                    #     self._while_watering_callback_function(
                    #         is_watering=self.pump_controller.is_watering,
                    #         watering_time=round(self.watering_time),
                    #         liters_sent=round(self.liters_sent, 2)
                    #     )
                    #
                    # self._log_manual_watering_cycle()
                else:
                    print("Current data: null")

    def stop_listening_for_watering_now(self):
        RemoteRequests().unsubscribe_watering_now_listener()

    def start_sending_watering_updates(self):
        self._watering_cycle_start_time = get_current_datetime_tz()

        self._send_watering_updates_event.clear()
        self._send_watering_updates_thread = threading.Thread(target=self._send_watering_updates_worker, daemon=True)
        self._send_watering_updates_thread.start()

    def stop_sending_watering_updates(self):
        self.watering_time = time.time() - self.watering_time_start  # seconds
        self.liters_sent = self.watering_time * self.pump_controller.pump_capacity  # seconds * liters/second -> liters

        self._send_watering_updates_event.set()
        if self._send_watering_updates_thread is not None and self._send_watering_updates_thread.is_alive():
            self._send_watering_updates_thread.join()

        self._update_info_for_watering_callback()

    def _send_watering_updates_worker(self):
        self.watering_time_start = time.time()
        TIMEOUT = self._send_watering_updates_interval_ms / 1000.0

        while not self._send_watering_updates_event.is_set():
            self._send_watering_updates_event.wait(TIMEOUT)
            if self._send_watering_updates_event.is_set():
                return
            self._send_watering_update_function()

    def _send_watering_update_function(self):
        self.watering_time = time.time() - self.watering_time_start  # seconds
        self.liters_sent = self.watering_time * self.pump_controller.pump_capacity  # seconds * liters/second -> liters

        if self.watering_time >= self._max_watering_time_sec:
            def _stop_watering():
                self.pump_controller.stop_watering_event.set()
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

        # self.stop_sending_watering_updates()
        self.pump_controller.stop_watering()

    def _update_current_watering_info(self):
        RemoteRequests().update_watering_info(
            'processing',
            round(self.liters_sent, 2),
            round(self.watering_time)
        )

    def _update_info_for_watering_callback(self):
        if self._while_watering_callback_function is not None:
            self._while_watering_callback_function(
                is_watering=self.pump_controller.is_watering,
                watering_time=round(self.watering_time),
                liters_sent=round(self.liters_sent, 2)
            )

    def _on_ping_from_phone(self,
        doc_snapshot,
        changes,
        read_time):

        for change in changes:
            changed_doc = change.document
            doc_data = changed_doc.to_dict()

            if "message" in doc_data.keys():
                if doc_data["message"] == "PING":
                    FirebaseController().answer_to_ping()

    def _set_ping_callback(self):
        FirebaseController().add_ping_listener(self._on_ping_from_phone)

    def set_callback_for_watering_updates(self, callback):
        self._while_watering_callback_function = callback

    def get_raspberry_info(self) -> RaspberryInfo:
        _raspberry_info = RemoteRequests().get_raspberry_info()
        if _raspberry_info is not None:
            return _raspberry_info
        return self._raspberry_info

    def _load_raspberry_info_local_storage(self):
        _raspberry_info = LocalStorageController().get_raspberry_info()
        if _raspberry_info is not None:
            self._raspberry_info = _raspberry_info

    def update_raspberry_notification_info(self, message_type: MessageType, value):
        self._raspberry_info.set_notifiable_message(message_type, value)
        RemoteRequests().update_raspberry_notifiable_message(message_type, value)

    def _send_moisture_info(self):
        RemoteRequests().update_moisture_info(self.get_moisture_percentage())

    def _send_water_tank_volume_info(self):
        RemoteRequests().update_water_tank_volume_info(
            self.water_depth_measurement_controller.get_current_water_volume()
        )

    def update_raspberry_info(self):
        _raspberry_info = RemoteRequests().get_raspberry_info()
        if _raspberry_info is not None:
            self._raspberry_info = _raspberry_info
            LocalStorageController().save_raspberry_info(self._raspberry_info)

    def on_notification_from_subject(self, notification_type: ObserverNotificationType):
        print(f"Subject notified raspberry controller: {notification_type}")
        if notification_type == ObserverNotificationType.FIRESTORE_CLIENT_CHANGED:
            self._set_ping_callback()
            self.start_listening_for_watering_now()
            self.update_raspberry_info()
