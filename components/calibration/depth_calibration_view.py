import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty, Clock
from kivymd.uix.screen import MDScreen

from utils.local_storage_controller import LocalStorageController
from utils.raspberry_controller import RaspberryController
from utils.water_depth_measurement_controller import WaterDepthMeasurementController

Builder.load_file("components/calibration/depth_calibration_view.kv")


class DepthCalibrationView(MDScreen):
    calibrating = BooleanProperty(False)
    step_text = StringProperty("Step 1: Empty the water tank and press the button below")
    loading_text = StringProperty("")
    calibrate_button_text = StringProperty("Calibrate")

    def __init__(self, **kwargs):
        super(DepthCalibrationView, self).__init__(**kwargs)

        self._min_value = None
        self._max_value = None
        self._tank_volume = None

        self._current_thread = None
        self._cancel_event = threading.Event()

    def on_enter(self, *args):
        self.calibrating = False
        self.step_text = "Step 1: Empty the water tank and press the button below"
        self.loading_text = ""
        self.calibrate_button_text = "Calibrate"

        self._min_value = None
        self._max_value = None
        self._tank_volume = None

        self._current_thread = None
        self._cancel_event.clear()

    def on_leave(self, *args):
        self.on_enter(args)

    def calibrate_button_function(self, *args):
        if self._max_value is None:
            self.calibrating = True
            self._current_thread = threading.Thread(
                target=self._get_max_value,
                args=(self._on_max_value_thread_finished,)
            )

            self._current_thread.start()

        elif self._min_value is None:
            self.calibrating = True
            self._current_thread = threading.Thread(
                target=self._get_min_value,
                args=(self._on_min_value_thread_finished,)
            )

            self._current_thread.start()
        else:
            # self._tank_volume = RaspberryController().moisture_controller.get_moisture()
            # RaspberryController().moisture_controller.tank_volume = self._tank_volume
            #
            # LocalStorageController().set_moisture_sensor_absolute_values(
            #     self._min_value,
            #     self._max_value
            # )
            #
            # RaspberryController().moisture_controller.absolute_dry = self._max_value
            # RaspberryController().moisture_controller.absolute_wet = self._min_value

            self._navigate_back()

    def _get_min_value(self, on_thread_finished=None):
        self._min_value = WaterDepthMeasurementController().measure_water_depth_cm()
        if on_thread_finished is not None:
            on_thread_finished()

    def _get_max_value(self, on_thread_finished=None):
        self._max_value = WaterDepthMeasurementController().measure_water_depth_cm()
        if on_thread_finished is not None:
            on_thread_finished()

    def cancel(self, *args):
        self._cancel_event.set()
        if self._current_thread is not None:
            self._current_thread.join()
        self._navigate_back()

    def _navigate_back(self):
        def _aux(*args):
            App.get_running_app().root.ids.navigation_drawer.screen_manager.current = "calibrate"
        Clock.schedule_once(_aux, 0.1)

    def _on_min_value_thread_finished(self):
        self.step_text = "Step 3: Specify the tank volume in L and press Save\n"
        self.calibrating = False
        self.loading_text = ""
        self.calibrate_button_text = "Save"

    def _on_max_value_thread_finished(self):
        self.step_text = "Step 2: Fill the water tank and press the button below"
        self.calibrating = False
        self.loading_text = ""
