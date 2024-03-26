import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.properties import BooleanProperty, StringProperty, Clock
from kivymd.uix.screen import MDScreen

from utils.local_storage_controller import LocalStorageController
from utils.raspberry_controller import RaspberryController

Builder.load_file("components/calibration/pump_calibration_view.kv")


class PumpCalibrationView(MDScreen):
    calibrating = BooleanProperty(False)
    step_text = StringProperty("Place the pump hose in 0.5L bottle full of water"
                               " and press the button below. When it ends pumping all the"
                               " water, press the button again.")
    loading_text = StringProperty("")
    calibrate_button_text = StringProperty("Start")

    def __init__(self, **kwargs):
        super(PumpCalibrationView, self).__init__(**kwargs)

        self._WATER_QTY = 0.5

        self._time_delta = 0

        self._current_thread = None
        self._cancel_event = threading.Event()

    def on_enter(self, *args):
        self.calibrating = False
        self.step_text = ("Place the pump hose in 0.5L bottle full of water"
                          " and press the button below. When it ends pumping all the"
                          " water, press the button again.")
        self.loading_text = ""
        self.calibrate_button_text = "Start"

        self._time_delta = 0

        self._current_thread = None
        self._cancel_event.clear()

    def on_leave(self, *args):
        RaspberryController().pump_controller.stop_watering()
        self.on_enter(args)

    def calibrate_button_function(self, *args):
        if self._time_delta == 0:
            self.calibrating = True
            self._current_thread = threading.Thread(
                target=self._compute_time_delta,
                args=(self._on_calibration_thread_finished,)
            )

            self._current_thread.start()

            self.calibrate_button_text = "Stop"

        elif self.calibrating:
            self.calibrating = False
            self._cancel_event.set()
            if self._current_thread is not None:
                self._current_thread.join()

        else:
            _pump_capacity = 60 / self._time_delta * self._WATER_QTY  # 60 seconds in a minute
            LocalStorageController().set_pump_capacity(_pump_capacity)
            RaspberryController().pump_controller.pump_capacity = _pump_capacity

            self._navigate_back()

    def _compute_time_delta(self, on_thread_finished=None):
        RaspberryController().pump_controller.start_watering()

        while not self._cancel_event.is_set():
            self.loading_text = f"Time elapsed: {self._time_delta} seconds"
            self._time_delta += 1

            self._cancel_event.wait(1)
            if self._cancel_event.is_set():
                break

        RaspberryController().pump_controller.stop_watering()

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

    def _on_calibration_thread_finished(self):
        self.step_text = "Calibration finished"
        self.calibrating = False
        self.loading_text = ""
        self.calibrate_button_text = "Save"
