import threading

from utils.depth_sensor_controller import DepthSensorController


class WaterDepthMeasurementController:
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

        self._depth_sensor_controller = DepthSensorController(trigger_pin=23, echo_pin=24)

        self._tank_volume_ratio = None  # liters per cm in height

        self._load_parameters()

    def _load_parameters(self):
        pass

    def measure_water_depth_cm(self):
        return self._depth_sensor_controller.measure_water_depth_cm()

    def set_tank_volume_ratio(self, min_value, max_value, tank_volume):
        self._tank_volume_ratio = tank_volume / (max_value - min_value)
        return self._tank_volume_ratio
