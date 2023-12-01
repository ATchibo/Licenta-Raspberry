import time

# import RPi.GPIO as GPIO


class PumpController:
    """Class for controlling the pump."""

    def __init__(self, pin, liters_per_second):
        # set the pin for the pump
        self.pin = pin
        # set the liters per second
        self.pump_capacity = liters_per_second
    #
    #     GPIO.setwarnings(False)
    #     # set the mode to BCM - refer to the pins by the GPIO number
    #     GPIO.setmode(GPIO.BCM)
    #     # set the pin to output
    #     GPIO.setup(self.pin, GPIO.OUT)
    #     # set the pin to low - not sending any power
    #     GPIO.output(self.pin, GPIO.LOW)
    #
    # def start_watering_for_seconds(self, seconds):
    #     """Start watering for the specified amount of seconds."""
    #
    #     time_end = time.time() + seconds
    #     while time.time() < time_end:
    #         self._start()
    #     self._stop()
    #
    # def start_watering_for_liters(self, liters):
    #     """Start watering for the specified amount of minutes."""
    #     seconds = liters / self.pump_capacity
    #     self.start_watering_for_seconds(seconds)
    #
    # def _start(self):
    #     """Start the pump."""
    #     GPIO.output(self.pin, GPIO.HIGH)
    #
    # def _stop(self):
    #     """Stop the pump."""
    #     GPIO.output(self.pin, GPIO.LOW)
