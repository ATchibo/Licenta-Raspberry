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

        self._send_watering_updates_interval_ms = 1000
        self._max_watering_time_sec = 30
        self.watering_time = 0  # seconds
        self.liters_sent = 0  # liters
        self._send_watering_updates_thread = None
        self._send_watering_updates = False
        self._watering_callback_function = None

    def set_watering_program(self, watering_program):
        self._watering_program = watering_program

    def get_moisture_percentage(self):
        return self.moisture_controller.get_moisture_percentage()

    def check_need_for_watering(self):
        if self.get_moisture_percentage() < self._watering_program.get_min_moisture():
            self.pump_controller.start_watering_for_liters(self._watering_program.get_liters_needed())

    def water_now(self) -> bool:
        if self.pump_controller.start_watering():
            self.start_sending_watering_updates()
            return True
        return False

    def stop_watering(self) -> bool:
        if self.pump_controller.stop_watering():
            self.stop_sending_watering_updates()
            return True
        return False

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

                        if self._watering_callback_function is not None:
                            self._watering_callback_function(
                                is_watering=self.pump_controller.is_watering,
                                watering_time=round(self.watering_time),
                                liters_sent=round(self.liters_sent, 2)
                            )

            else:
                print("Current data: null")

    def stop_listening_for_watering_now(self):
        FirebaseController().watering_now_listener.unsubscribe()

    def start_sending_watering_updates(self):
        self._send_watering_updates = True
        self._send_watering_updates_thread = threading.Thread(target=self._send_watering_updates_worker)
        self._send_watering_updates_thread.start()

    def stop_sending_watering_updates(self):
        self._send_watering_updates = False

        if self._send_watering_updates_thread is not None and self._send_watering_updates_thread.is_alive():
            self._send_watering_updates_thread.join()

    def _send_watering_updates_worker(self):
        watering_time_start = time.time()

        while self._send_watering_updates:
            self._send_watering_update_function(watering_time_start)
            time.sleep(self._send_watering_updates_interval_ms / 1000.0)

    def _send_watering_update_function(self, watering_time_start):
        self.watering_time = time.time() - watering_time_start  # seconds
        self.liters_sent = self.watering_time * self.pump_controller.pump_capacity  # seconds * liters/second -> liters

        if self.watering_time >= self._max_watering_time_sec:
            FirebaseController().update_watering_info(
                getserial(),
                'stop_watering',
                round(self.liters_sent, 2),
                round(self.watering_time)
            )

            self.stop_sending_watering_updates()
            self.pump_controller.stop_watering()

            if self._watering_callback_function is not None:
                self._watering_callback_function(
                    is_watering=self.pump_controller.is_watering,
                    watering_time=round(self.watering_time),
                    liters_sent=round(self.liters_sent, 2)
                )

        else:
            FirebaseController().update_watering_info(
                getserial(),
                '',
                round(self.liters_sent, 2),
                round(self.watering_time)
            )

            if self._watering_callback_function is not None:
                self._watering_callback_function(
                    is_watering=self.pump_controller.is_watering,
                    watering_time=round(self.watering_time),
                    liters_sent=round(self.liters_sent, 2)
                )

    def set_callback_for_watering_updates(self, callback):
        self._watering_callback_function = callback
