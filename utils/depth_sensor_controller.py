import RPi.GPIO as GPIO
import time

class DepthSensorController:

    def __init__(self, trigger_pin, echo_pin):
        self._trigger_pin = trigger_pin
        self._echo_pin = echo_pin

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self._trigger_pin, GPIO.OUT)
        GPIO.setup(self._echo_pin, GPIO.IN)

        GPIO.output(self._trigger_pin, GPIO.LOW)

    def measure_water_depth_cm(self):
        GPIO.output(self._trigger_pin, GPIO.HIGH)
        time.sleep(0.00001)
        GPIO.output(self._trigger_pin, GPIO.LOW)

        while GPIO.input(self._echo_pin) == 0:
            pulse_start_time = time.time()
        while GPIO.input(self._echo_pin) == 1:
            pulse_end_time = time.time()

        pulse_duration = pulse_end_time - pulse_start_time

        # if we consider the speed of sound to be 343 m/s we get 34300 cm/s
        # and we divide by 2 because the sound goes to the object and comes back
        # then, by applying the formula distance = time * speed (which is time * 34300 / 2)
        # we get the distance in cm
        distance = pulse_duration * 17150
        return round(distance, 2)
