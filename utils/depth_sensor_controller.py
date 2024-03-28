import random

class DepthSensorController:

    def __init__(self, trigger_pin, echo_pin):
        self._trigger_pin = trigger_pin
        self._echo_pin = echo_pin

    def measure_water_depth_cm(self):
        return random.randint(0, 100)
