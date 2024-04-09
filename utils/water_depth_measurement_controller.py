import threading
import time

from utils.depth_sensor_controller import DepthSensorController
from utils.local_storage_controller import LocalStorageController


class WaterDepthMeasurementController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 tank_volume_ratio=0.08,
                 empty_tank_threshold=0.03,
                 low_tank_threshold=0.25,
                 trigger_pin=23,
                 echo_pin=24
                 ):

        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self._depth_sensor_controller = DepthSensorController(trigger_pin=trigger_pin, echo_pin=echo_pin)

        self._tank_volume_ratio = tank_volume_ratio  # liters per cm in height
        self._max_height = None
        self._empty_tank_threshold = empty_tank_threshold
        self._low_tank_threshold = low_tank_threshold

        self._load_parameters()

    def _load_parameters(self):
        _tank_volume_ratio, _max_height = LocalStorageController().get_depth_sensor_parameters()
        if _tank_volume_ratio is not None and _max_height is not None:
            self._tank_volume_ratio = _tank_volume_ratio
            self._max_height = _max_height
        else:
            LocalStorageController().set_depth_sensor_parameters(self._tank_volume_ratio, self._max_height)

    def measure_water_depth_cm(self):
        return self._depth_sensor_controller.measure_water_depth_cm()

    def set_tank_volume_ratio(self, min_value, max_value, tank_volume):
        self._tank_volume_ratio = tank_volume / (max_value - min_value)
        self._max_height = max_value
        LocalStorageController().set_depth_sensor_parameters(self._tank_volume_ratio, max_value)
        return self._tank_volume_ratio

    def get_current_water_volume(self):
        if self._max_height is None:
            return 0

        _max_tries = 5
        _water_height_1 = self.measure_water_depth_cm()
        print("Water height 1: ", _water_height_1)
        time.sleep(0.5)
        _water_height_2 = self.measure_water_depth_cm()
        print("Water height 2: ", _water_height_2)
        while abs(_water_height_1 - _water_height_2) > 0.1 and _max_tries > 0:
            _water_height_1 = _water_height_2
            time.sleep(0.5)
            _water_height_2 = self.measure_water_depth_cm()
            print("Water height 2: ", _water_height_2)
            _max_tries -= 1

        _volume = self._tank_volume_ratio * (self._max_height - _water_height_2)
        print("Volume: ", _volume)
        return round(max(0.0, _volume), 2)

    def is_water_tank_empty(self) -> bool:
        return self.get_current_water_volume() < self._empty_tank_threshold

    def is_water_tank_low(self) -> bool:
        return self.get_current_water_volume() < self._low_tank_threshold
