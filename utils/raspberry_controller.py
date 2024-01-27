import threading
import time

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

        self.send_watering_updates_interval_ms = 1000
        self._send_watering_updates_thread = None

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
                    if updated_data["command"] == "start_watering":
                        if self.pump_controller.is_watering:
                            return

                        self.pump_controller.start_watering()
                        self.start_sending_watering_updates()

                    elif updated_data["command"] == "stop_watering":
                        if not self.pump_controller.is_watering:
                            return

                        self.pump_controller.stop_watering()
                        self.stop_sending_watering_updates()

            else:
                print("Current data: null")

    def stop_listening_for_watering_now(self):
        FirebaseController().watering_now_listener.unsubscribe()

    def start_sending_watering_updates(self):
        self._send_watering_updates_thread = threading.Thread(target=self._send_watering_updates_worker)
        self._send_watering_updates_thread.start()

    def stop_sending_watering_updates(self):
        if self._send_watering_updates_thread is not None and self._send_watering_updates_thread.is_alive():
            self._send_watering_updates_thread.join()

    def _send_watering_updates_worker(self):
        watering_time_start = time.time()

        while True:
            self._send_watering_update_function(watering_time_start)
            time.sleep(self.send_watering_updates_interval_ms / 1000.0)

    def _send_watering_update_function(self, watering_time_start):
        watering_time = time.time() - watering_time_start  # seconds
        liters_sent = watering_time * self.pump_controller.pump_capacity  # seconds * liters/second -> liters

        FirebaseController().update_watering_info(
            getserial(),
            'start_watering',
            round(liters_sent, 2),
            round(watering_time)
        )
