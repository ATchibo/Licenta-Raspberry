import threading
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty, Clock, NumericProperty
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
    retry_step_button_text = StringProperty("Retry step")
    _finished_step_1 = BooleanProperty(False)
    _finished_step_2 = BooleanProperty(False)

    _show_spinner = BooleanProperty(False)

    _volume_options = {
        "0.5 L": 0.5,
        "2 L": 2,
        "5 L": 5,
    }

    _selected_option = StringProperty()

    def __init__(self, **kwargs):
        super(DepthCalibrationView, self).__init__(**kwargs)

        self._min_value = None
        self._max_value = None
        self._tank_volume = None
        self._current_thread = None
        self._cancel_event = None

        self._init_setup()

    def on_enter(self, *args):
        self._init_setup()

    def on_leave(self, *args):
        self._init_setup()

    def _init_setup(self):
        self.calibrating = False
        self.step_text = "Step 1: Empty the water tank and press the button below"
        self.loading_text = ""
        self.calibrate_button_text = "Calibrate"
        self._finished_calibrating = False

        self._selected_option = "0.5 L"
        self._show_spinner = False

        self._min_value = None
        self._max_value = None
        self._tank_volume = self._volume_options[self._selected_option]

        self._current_thread = None
        self._cancel_event = threading.Event()

    def calibrate_button_function(self, *args):
        if self._max_value is None:
            self._init_setup()

            self.calibrating = True
            self.loading_text = "Measuring water depth..."

            self._current_thread = threading.Thread(
                target=self._get_max_value,
                args=(self._on_height_measurement_finished,)
            )

            self._current_thread.start()

        elif self._finished_step_1 is False:
            self._on_max_value_computing_finished()
            
        elif self._min_value is None:
            self.calibrating = True
            self.loading_text = "Measuring water depth..."

            self._current_thread = threading.Thread(
                target=self._get_min_value,
                args=(self._on_height_measurement_finished,)
            )

            self._current_thread.start()

        elif self._finished_step_2 is False:
            self._on_min_value_computing_finished()

        else:
            _ratio = RaspberryController().water_depth_measurement_controller.set_tank_volume_ratio(
                self._min_value,
                self._max_value,
                self._tank_volume
            )
            LocalStorageController().set_depth_sensor_parameters(_ratio, self._max_value)

            self._navigate_back()

    def _get_min_value(self, on_thread_finished=None):
        self._min_value = RaspberryController().water_depth_measurement_controller.measure_water_depth_cm()
        if on_thread_finished is not None:
            on_thread_finished()

    def _get_max_value(self, on_thread_finished=None):
        self._max_value = RaspberryController().water_depth_measurement_controller.measure_water_depth_cm()
        if on_thread_finished is not None:
            on_thread_finished()

    def _change_volume_option(self):
        self._selected_option = self.ids.volume_spinner.text
        self._tank_volume = self._volume_options[self._selected_option]

    def cancel(self, *args):
        self._cancel_event.set()
        if self._current_thread is not None:
            self._current_thread.join()
        self._navigate_back()

    def _navigate_back(self):
        def _aux(*args):
            App.get_running_app().root.ids.navigation_drawer.screen_manager.current = "calibrate"
        Clock.schedule_once(_aux, 0.1)

    def _on_height_measurement_finished(self):
        height = self._min_value if self._min_value is not None else self._max_value

        self.loading_text = "Measured height: " + str(height) + " cm"
        self.calibrating = False
        self.calibrate_button_text = "Next"

    def _on_max_value_computing_finished(self):
        self.step_text = ("Step 2: Select an option and fill the tank with the corresponding amount of water."
                          "After filling the tank, press Calibrate.")
        self.calibrating = False
        self.loading_text = ""
        self.calibrate_button_text = "Calibrate"
        self._finished_step_1 = True

        Clock.schedule_once(lambda dt: setattr(self, '_show_spinner', True), 0.1)

    def _on_min_value_computing_finished(self):
        self.step_text = "Calibration finished"
        self.calibrating = False
        self.loading_text = ""
        self.calibrate_button_text = "Save"
        self._finished_step_2 = True

        Clock.schedule_once(lambda dt: setattr(self, '_show_spinner', False), 0.1)

    def _retry_last_step(self):
        if self._min_value is not None:
            self._min_value = None
            self._on_max_value_computing_finished()
        else:
            self._max_value = None
            self._init_setup()
