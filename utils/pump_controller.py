import threading
import time

# import RPi.GPIO as GPIO


class PumpController:
    """Class for controlling the pump."""

    def __init__(self, pin, liters_per_second):
        # set the pin for the pump
        self.pin = pin
        # set the liters per second
        if liters_per_second is not None:
            self.pump_capacity = liters_per_second
        else:
            self.pump_capacity = 0.017857143  # about 1 liter per minute

        self.is_watering = False

        self.stop_watering_event = threading.Event()

        # GPIO.setwarnings(False)
        # # set the mode to BCM - refer to the pins by the GPIO number
        # GPIO.setmode(GPIO.BCM)
        # # set the pin to output
        # GPIO.setup(self.pin, GPIO.OUT)
        # # set the pin to low - not sending any power
        # GPIO.output(self.pin, GPIO.LOW)

    def start_watering_for_seconds(self, seconds):
        """Start watering for the specified amount of seconds."""

        # time_end = time.time() + seconds
        # while time.time() < time_end:
        #     if self.stop_watering_event.is_set():
        #         break
        #     self.start_watering()
        #
        # self.stop_watering()
        # self.stop_watering_event.clear()

        self.start_watering()
        self.stop_watering_event.wait(seconds)
        self.stop_watering()
        self.stop_watering_event.clear()

    def start_watering_for_liters(self, liters):
        """Start watering for the specified amount of minutes."""
        seconds = liters / self.pump_capacity
        self.start_watering_for_seconds(seconds)

    def start_watering(self) -> bool:
        if self.is_watering:
            return False

        """Start the pump."""
        # GPIO.output(self.pin, GPIO.HIGH)

        self.is_watering = True
        return True

    def stop_watering(self):
        if not self.is_watering:
            return False

        """Stop the pump."""
        # GPIO.output(self.pin, GPIO.LOW)

        self.is_watering = False
        return True
