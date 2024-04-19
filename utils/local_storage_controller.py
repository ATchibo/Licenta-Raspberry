import datetime
import os
import pickle
import threading

from tzlocal import get_localzone

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

        self._moisture_sensor_file = 'moisture_sensor'
        self._pump_capacity_file = 'pump_capacity'
        self._depth_sensor_file = 'depth_sensor'

        self._last_watering_time_file = 'last_watering_time'

    def clear_all(self):
        self._delete_file(self._raspberry_info_file)
        self._delete_file(self._moisture_info_file)
        self._delete_file(self._watering_programs_file)
        self._delete_file(self._watering_programs_active_id_file)
        self._delete_file(self._is_watering_programs_active_file)
        self._delete_file(self._log_messages_file)
        self._delete_file(self._last_watering_time_file)

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
        except Exception as e:
            print(f'Error while loading RaspberryInfo from file: {e}')
            return None

    def save_raspberry_info(self, raspberry_info: RaspberryInfo):
        try:
            with open(self._raspberry_info_file, 'wb') as file:
                pickle.dump(raspberry_info.to_dict(), file)
        except FileNotFoundError:
            print(f'File not found: {self._raspberry_info_file}')
            pass
        except Exception as e:
            print(f'Error while saving RaspberryInfo to file: {e}')
            pass

    def get_moisture_info(self, start_date=None, end_date=None) -> list[dict]:
        try:
            with open(self._moisture_info_file, 'rb') as file:
                _moisture_info = pickle.load(file)

                if start_date is None:
                    start_date = datetime.datetime.min
                if end_date is None:
                    end_date = datetime.datetime.now()

                start_date = start_date.astimezone(get_localzone())
                end_date = end_date.astimezone(get_localzone())

                _moisture_info_filtered = [measurement for measurement in _moisture_info
                                  if start_date <= measurement["measurementTime"] <= end_date]

                return _moisture_info_filtered
        except FileNotFoundError as e:
            print(f'File not found: {self._moisture_info_file} and error is {e}')
            return []

    def save_moisture_info(self, moisture_info: list[dict]):
        try:
            with open(self._moisture_info_file, 'wb') as file:
                pickle.dump(moisture_info, file)
        except FileNotFoundError:
            print(f'File not found: {self._moisture_info_file}')
            pass

    def update_moisture_info_list(self, moisture_info: list[dict]):
        try:
            _current_moisture_info = self.get_moisture_info()
            _current_moisture_info.extend(moisture_info)
            _current_moisture_info = sorted(_current_moisture_info, key=lambda x: x["measurementTime"], reverse=True)
            _current_moisture_info = _current_moisture_info[:100]
            self.save_moisture_info(_current_moisture_info)
        except Exception as e:
            print(f'Error while updating moisture info: {e}')
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
        _log_messages[log_message.get_timestamp()] = log_message.get_message()
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
            return {}, False
        return _raspberry_info.notifiableMessages, True

    def add_moisture_percentage_measurement(self, measurement):
        _moisture_info = self.get_moisture_info()
        _moisture_info.append(measurement)
        self.update_moisture_info_list(_moisture_info)
        return True

    def set_moisture_sensor_absolute_values(self, absolute_dry, absolute_wet) -> bool:
        try:
            with (open(self._moisture_sensor_file, 'wb') as file):
                _moisture_absolute_values = {
                    "absolute_dry": absolute_dry,
                    "absolute_wet": absolute_wet
                }
                pickle.dump(_moisture_absolute_values, file)

                return True
        except FileNotFoundError:
            print(f'File not found: {self._log_messages_file}')
            return False

    def get_moisture_sensor_absolute_values(self):
        try:
            with (open(self._moisture_sensor_file, 'rb') as file):
                _moisture_absolute_values = pickle.load(file)
                if (_moisture_absolute_values is None
                        or "absolute_dry" not in _moisture_absolute_values
                        or "absolute_wet" not in _moisture_absolute_values):
                    return None, None

                return _moisture_absolute_values["absolute_dry"], _moisture_absolute_values["absolute_wet"]
        except FileNotFoundError:
            return None, None
        except Exception as e:
            print(f'Error while loading moisture sensor absolute values: {e}')
            return None, None

    def set_pump_capacity(self, _pump_capacity):
        try:
            with (open(self._pump_capacity_file, 'wb') as file):
                pickle.dump(_pump_capacity, file)
                return True
        except FileNotFoundError:
            print(f'File not found: {self._log_messages_file}')
            return False

    def get_pump_capacity(self):
        try:
            with (open(self._pump_capacity_file, 'rb') as file):
                _pump_capacity = pickle.load(file)
                if not isinstance(_pump_capacity, float) or _pump_capacity < 0:
                    return None
                return _pump_capacity
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f'Error while loading pump capacity: {e}')
            return None

    def set_last_watering_time(self, timestamp, program_id):
        try:
            with open(self._last_watering_time_file, 'rb') as file:
                data = {
                    "program_id": program_id,
                    "timestamp": timestamp
                }
                pickle.dump(data, file)
                return True
        except FileNotFoundError:
            return False
        except Exception as e:
            print(f'Error while loading last watering times: {e}')
            return False

    def get_last_watering_time(self):
        try:
            with open(self._last_watering_time_file, 'rb') as file:
                data = pickle.load(file)
                if data is None or "program_id" not in data or "timestamp" not in data:
                    return None, None
                return data["program_id"], data["timestamp"]
        except FileNotFoundError:
            return None, None
        except Exception as e:
            print(f'Error while loading last watering times: {e}')
            return None, None

    def set_depth_sensor_parameters(self, tank_volume_ratio, max_height):
        try:
            with (open(self._depth_sensor_file, 'wb') as file):
                _depth_sensor_parameters = {
                    "tank_volume_ratio": tank_volume_ratio,
                    "max_height": max_height
                }
                pickle.dump(_depth_sensor_parameters, file)

                return True
        except FileNotFoundError:
            print(f'File not found: {self._log_messages_file}')
            return False
        except Exception as e:
            print(f'Error while saving depth sensor parameters: {e}')
            return False

    def get_depth_sensor_parameters(self):
        try:
            with (open(self._depth_sensor_file, 'rb') as file):
                _depth_sensor_parameters = pickle.load(file)
                if (_depth_sensor_parameters is None
                        or "tank_volume_ratio" not in _depth_sensor_parameters
                        or "max_height" not in _depth_sensor_parameters):
                    return None, None

                return _depth_sensor_parameters["tank_volume_ratio"], _depth_sensor_parameters["max_height"]
        except FileNotFoundError:
            return None, None
        except Exception as e:
            print(f'Error while loading depth sensor parameters: {e}')
            return None, None
