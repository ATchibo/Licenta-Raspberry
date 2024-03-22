import threading
from datetime import datetime

from domain.RaspberryInfo import RaspberryInfo
from domain.WateringProgram import WateringProgram
from domain.logging.MessageType import MessageType
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.local_storage_controller import LocalStorageController


class RemoteRequests:
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

        self._firebase_controller = FirebaseController()
        self._local_storage_controller = LocalStorageController()

    # def try_initial_login(self) -> bool:
    #     return self._login_controller.try_initial_login()

    def attempt_login(self, auth_token: str) -> bool:
        return self._firebase_controller.login_with_custom_token(auth_token)

    def register_raspberry(self, raspberry_info: RaspberryInfo) -> bool:
        try:
            return self._firebase_controller.register_raspberry(raspberry_info)
        except Exception as e:
            return False

    def get_raspberry_info(self) -> RaspberryInfo | None:
        try:
            _result = self._firebase_controller.get_raspberry_info(self._raspberry_id)
            if _result is None:
                _result = self._local_storage_controller.get_raspberry_info()
            else:
                self._local_storage_controller.save_raspberry_info(_result)
            return _result
        except Exception as e:
            return self._local_storage_controller.get_raspberry_info()

    def add_watering_now_listener(self, callback):
        self._firebase_controller.add_watering_now_listener(self._raspberry_id, callback)

    def get_moisture_info(self, start_date: datetime, end_date: datetime) -> list[dict]:
        try:
            _result = self._firebase_controller.get_moisture_info_for_rasp_id(self._raspberry_id, start_date, end_date)
            self._local_storage_controller.save_moisture_info(_result)
            return _result
        except Exception as e:
            return self._local_storage_controller.get_moisture_info()

    def update_watering_info(self, command: str, liters_sent: float, watering_time: int) -> bool:
        try:
            return self._firebase_controller.update_watering_info(self._raspberry_id, command, liters_sent, watering_time)
        except Exception as e:
            return False

    def get_watering_programs(self) -> list[WateringProgram]:
        try:
            _result = self._firebase_controller.get_watering_programs(self._raspberry_id)
            self._local_storage_controller.save_watering_programs(_result)
            return _result
        except Exception as e:
            return self._local_storage_controller.get_watering_programs()

    def get_active_watering_program_id(self) -> str | None:
        try:
            _result = self._firebase_controller.get_active_watering_program_id(self._raspberry_id)
            self._local_storage_controller.save_active_watering_program_id(_result)
            return _result
        except Exception as e:
            return self._local_storage_controller.get_active_watering_program_id()

    def set_active_watering_program_id(self, program_id: str):
        try:
            _result = self._firebase_controller.set_active_watering_program_id(self._raspberry_id, program_id)
        except Exception as e:
            pass

        self._local_storage_controller.save_active_watering_program_id(program_id)

    def get_is_watering_programs_active(self) -> bool:
        try:
            _result = self._firebase_controller.get_is_watering_programs_active(self._raspberry_id)
            self._local_storage_controller.save_is_watering_programs_active(_result)
            return _result
        except Exception as e:
            return self._local_storage_controller.get_is_watering_programs_active()

    def set_is_watering_programs_active(self, is_active: bool):
        try:
            _result = self._firebase_controller.set_is_watering_programs_active(self._raspberry_id, is_active)
        except Exception as e:
            pass

        self._local_storage_controller.save_is_watering_programs_active(is_active)

    def add_listener_for_watering_programs_changes(self, callback) -> bool:
        try:
            self._firebase_controller.add_listener_for_watering_programs_changes(self._raspberry_id, callback)
            return True
        except Exception as e:
            return False

    def add_listener_for_log_messages_changes(self, callback) -> bool:
        try:
            self._firebase_controller.add_listener_for_log_messages_changes(self._raspberry_id, callback)
            return True
        except Exception as e:
            return False

    def unregister_raspberry(self) -> bool:
        try:
            return self._firebase_controller.unregister_raspberry(self._raspberry_id)
        except Exception as e:
            return False

    def register_raspberry_to_device(self, device_id: str) -> bool:
        try:
            return self._firebase_controller.link_raspberry_to_device(self._raspberry_id, device_id)
        except Exception as e:
            return False

    def get_log_messages(self) -> dict:
        try:
            _result = self._firebase_controller.get_log_messages(self._raspberry_id)
            self._local_storage_controller.save_log_messages(_result)
            return _result
        except Exception as e:
            return self._local_storage_controller.get_log_messages()

    def add_log_message(self, log_message: str) -> bool:
        try:
            _result = self._firebase_controller.add_log_message(self._raspberry_id, log_message)
            self._local_storage_controller.add_log_message(log_message)
        except Exception as e:
            return False

    def update_raspberry_notifiable_message(self, message_type: MessageType, value: bool) -> bool:
        try:
            _result = self._firebase_controller.update_raspberry_notifiable_message(self._raspberry_id, message_type, value)
            self._local_storage_controller.update_raspberry_notifiable_message(message_type, value)
            return _result
        except Exception as e:
            return False

    def get_notifiable_messages(self) -> dict:
        try:
            _result = self._firebase_controller.get_notifiable_messages(self._raspberry_id)
            self._local_storage_controller.save_notifiable_messages(_result)
            return _result
        except Exception as e:
            return self._local_storage_controller.get_notifiable_messages()

    def add_moisture_percentage_measurement(self, percentage: float, timestamp: datetime) -> bool:
        try:
            _result = self._firebase_controller.add_moisture_percentage_measurement(self._raspberry_id, percentage, timestamp)
            self._local_storage_controller.add_moisture_percentage_measurement(percentage, timestamp)
            return _result
        except Exception as e:
            return False

    def unsubscribe_watering_now_listener(self):
        self._firebase_controller.unsubscribe_watering_now_listener()

    def update_moisture_info(self, param) -> bool:
        try:
            return self._firebase_controller.update_moisture_info(self._raspberry_id, param)
        except Exception as e:
            return False

