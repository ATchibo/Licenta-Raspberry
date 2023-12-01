from utils.moisture_controller import MoistureController
from utils.pump_controller import PumpController
from utils.watering_program import WateringProgram


class RaspberryController:
    def __init__(self):
        self.moisture_controller = MoistureController(channel=1)
        self.pump_controller = PumpController(pin=4, liters_per_second=0.1)
        self._watering_program = WateringProgram(name="Test", liters_needed=1, time_interval=1, min_moisture=30,
                                                 max_moisture=70)

    def set_watering_program(self, watering_program):
        self._watering_program = watering_program

    def get_moisture_percentage(self):
        return self.moisture_controller.get_moisture_percentage()

    def check_need_for_watering(self):
        if self.get_moisture_percentage() < self._watering_program.get_min_moisture():
            self.pump_controller.start_watering_for_liters(self._watering_program.get_liters_needed())
