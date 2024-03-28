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

    def measure_water_depth_cm(self):
        return self._depth_sensor_controller.measure_water_depth_cm()
