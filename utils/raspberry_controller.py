from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.moisture_controller import MoistureController
from utils.pump_controller import PumpController
from utils.watering_program import WateringProgram


class RaspberryController:
    _self = None

    def __new__(cls):
        if cls._self is None:
            cls._self = super().__new__(cls)
        return cls._self

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

    def start_listening_for_watering_now(self):
        FirebaseController().add_watering_now_listener(serial=getserial(), callback=self._watering_now_callback)

    def _watering_now_callback(self, doc_snapshot, changes, read_time):
        for doc in doc_snapshot:
            if doc.exists:
                # Handle the updated data
                updated_data = doc.to_dict()
                # Update your UI or perform necessary actions
                print(f"Document data: {updated_data}")

                if updated_data["command"] is not None:
                    if updated_data["command"] == "water_now":
                        self.pump_controller.start_watering()
                    elif updated_data["command"] == "stop_watering":
                        self.pump_controller.stop_watering()

            else:
                print("Current data: null")
