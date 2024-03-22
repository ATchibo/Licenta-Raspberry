import os
import pickle
import threading

from domain.RaspberryInfo import RaspberryInfo


class LocalStorageController:
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

        self._raspberry_info_file = 'raspberry_info'
        self._moisture_info_file = 'moisture_info'
        self._watering_programs_file = 'watering_programs'
        self._watering_programs_active_id_file = 'watering_programs_active_id'
        self._is_watering_programs_active_file = 'is_watering_programs_active'
        self._log_messages_file = 'log_messages'

    def clear_all(self):
        self._delete_file(self._raspberry_info_file)
        self._delete_file(self._moisture_info_file)
        self._delete_file(self._watering_programs_file)
        self._delete_file(self._watering_programs_active_id_file)
        self._delete_file(self._is_watering_programs_active_file)
        self._delete_file(self._log_messages_file)

    def _delete_file(self, file_name):
        if file_name in os.listdir():
            os.remove(file_name)

    def get_raspberry_info(self) -> RaspberryInfo | None:
        try:
            with open(self._raspberry_info_file, 'rb') as file:
                _raspberry_dict = pickle.load(file)
                if _raspberry_dict is None or len(_raspberry_dict) == 0:
                    return None

                try:
                    _rasp_info = RaspberryInfo().from_dict(_raspberry_dict)
                    return _rasp_info
                except Exception as e:
                    print(f'Error while loading RaspberryInfo from file: {e}')
                    return None
        except FileNotFoundError:
            return None

    def save_raspberry_info(self, raspberry_info: RaspberryInfo):
        try:
            with open(self._raspberry_info_file, 'wb') as file:
                pickle.dump(raspberry_info.to_dict(), file)
        except FileNotFoundError:
            print(f'File not found: {self._raspberry_info_file}')
            pass

    def get_moisture_info(self) -> list[dict]:
        try:
            with open(self._moisture_info_file, 'rb') as file:
                _moisture_info = pickle.load(file)
                return _moisture_info
        except FileNotFoundError:
            return []

    def save_moisture_info(self, moisture_info: list[dict]):
        try:
            with open(self._moisture_info_file, 'wb') as file:
                pickle.dump(moisture_info, file)
        except FileNotFoundError:
            print(f'File not found: {self._moisture_info_file}')
            pass

    def get_watering_programs(self):
        try:
            with open(self._watering_programs_file, 'rb') as file:
                _watering_programs = pickle.load(file)
                return _watering_programs
        except FileNotFoundError:
            return []

    def save_watering_programs(self, watering_programs):
        try:
            with open(self._watering_programs_file, 'wb') as file:
                pickle.dump(watering_programs, file)
        except FileNotFoundError:
            print(f'File not found: {self._watering_programs_file}')
            pass

    def get_active_watering_program_id(self):
        try:
            with open(self._watering_programs_active_id_file, 'rb') as file:
                _active_id = pickle.load(file)
                return _active_id
        except FileNotFoundError:
            return None

    def save_active_watering_program_id(self, active_id):
        try:
            with open(self._watering_programs_active_id_file, 'wb') as file:
                pickle.dump(active_id, file)
        except FileNotFoundError:
            print(f'File not found: {self._watering_programs_active_id_file}')
            pass

    def get_is_watering_programs_active(self):
        try:
            with open(self._is_watering_programs_active_file, 'rb') as file:
                _is_active = pickle.load(file)
                return _is_active
        except FileNotFoundError:
            return False

    def save_is_watering_programs_active(self, is_active):
        try:
            with open(self._is_watering_programs_active_file, 'wb') as file:
                pickle.dump(is_active, file)
        except FileNotFoundError:
            print(f'File not found: {self._is_watering_programs_active_file}')
            pass

    def get_log_messages(self) -> dict:
        try:
            with open(self._log_messages_file, 'rb') as file:
                _log_messages = pickle.load(file)
                return _log_messages
        except FileNotFoundError:
            return {}

    def save_log_messages(self, log_messages):
        try:
            with open(self._log_messages_file, 'wb') as file:
                pickle.dump(log_messages, file)
        except FileNotFoundError:
            print(f'File not found: {self._log_messages_file}')
            pass

    def add_log_message(self, log_message):
        _log_messages = self.get_log_messages()
        _log_messages.append(log_message)
        self.save_log_messages(_log_messages)

    def update_raspberry_notifiable_message(self, message_type, value):
        _raspberry_info = self.get_raspberry_info()
        if _raspberry_info is None:
            return False

        _raspberry_info.set_notifiable_message(message_type, value)
        self.save_raspberry_info(_raspberry_info)
        return True

    def save_notifiable_messages(self, notifiable_messages):
        _raspberry_info = self.get_raspberry_info()
        if _raspberry_info is None:
            return False

        _raspberry_info.notifiableMessages = notifiable_messages
        self.save_raspberry_info(_raspberry_info)
        return True

    def get_notifiable_messages(self):
        _raspberry_info = self.get_raspberry_info()
        if _raspberry_info is None:
            return {}
        return _raspberry_info.notifiableMessages

    def add_moisture_percentage_measurement(self, measurement, timestamp):
        _moisture_info = self.get_moisture_info()
        _moisture_info.append({timestamp: measurement})
        self.save_moisture_info(_moisture_info)
        return True

