import threading

from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from matplotlib import pyplot as plt

from utils.WateringProgramController import WateringProgramController
from utils.raspberry_controller import RaspberryController

Builder.load_file("components/homepage/watering_options_view.kv")


# TODO: replace local variables with variables from watering program controller when necessary and if applicable
class WateringOptionsView(MDBoxLayout):
    watering_label_variable = StringProperty()

    def __init__(self, **kwargs):
        super(WateringOptionsView, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = 1

        self.raspberry_controller = RaspberryController()
        self._watering_program_controller = WateringProgramController()
        self.watering_label_variable = f"Water amount: 0L\nTime running: 0s"
        self.pushed_water_now = False

        self.programs = {}
        self.current_program_name = ""
        self.selected_program_id = None
        self.are_programs_active = True

        self.bind_raspberry_controller_properties()
        self.load_programs()

        Clock.schedule_once(self.init, 0.1)

    def init(self, *args):
        if len(self.current_program_name) > 0:
            self.ids.watering_program_spinner.text = self.current_program_name

        self._watering_program_controller.set_on_receive_from_network_callback(self._update_values_on_receive_from_network)

    def change_program(self):
        self.current_program_name = self.ids.watering_program_spinner.text
        self._watering_program_controller.set_active_watering_program_id(self.programs[self.current_program_name].id)

    def load_programs(self):
        _programs = self._watering_program_controller.get_watering_programs()
        self.are_programs_active = self._watering_program_controller.get_is_watering_programs_active()
        self.selected_program_id = self._watering_program_controller.get_active_watering_program_id()

        if self.selected_program_id is not None:
            for program in _programs:
                if program.id == self.selected_program_id:
                    self.current_program_name = program.name
                    break

        self.programs = {program.name: program for program in _programs}

    def set_item(self, text_item):
        self.ids.drop_item.set_item(text_item)
        self.menu.dismiss()

    def toggle_water_now(self):
        if self.pushed_water_now:
            self.stop_watering()
        else:
            self.water_now()

    def water_now(self):
        print("Watering now")

        if self.raspberry_controller.water_now():
            # moisture_percentage = self.raspberry_controller.get_moisture_percentage()
            self.ids.water_now_button.text = "Stop watering"
            self.pushed_water_now = True
        else:
            self.ids.water_now_label.text = "Could not start watering"

    def stop_watering(self):
        res = self.raspberry_controller.stop_watering()

        if res:
            self.ids.water_now_button.text = "Water now"
            self.pushed_water_now = False
        else:
            self.ids.water_now_label.text = "Could not stop watering"

    def bind_raspberry_controller_properties(self):
        self.raspberry_controller.set_callback_for_watering_updates(callback=self._update_watering_now_info)

    def _update_watering_now_info(self, is_watering, watering_time, liters_sent):
        if self.pushed_water_now is not is_watering:
            if is_watering:
                self.ids.water_now_button.text = "Stop watering"
            else:
                self.ids.water_now_button.text = "Water now"

        self.pushed_water_now = is_watering
        self.watering_label_variable = f"Water amount: {liters_sent}L\nTime running: {watering_time}s"

    def toggle_watering_program(self):
        self.are_programs_active = not self.are_programs_active
        self._watering_program_controller.set_is_watering_programs_active(self.are_programs_active)

    def refresh_callback(self, *args):
        def refresh_callback(interval):
            self.load_programs()
            self.ids.watering_program_spinner.values = list(self.programs.keys())
            self.ids.watering_program_spinner.text = self.current_program_name
            self.are_programs_active = self._watering_program_controller.get_is_watering_programs_active()
            self.ids.watering_program_switch.active = self.are_programs_active

            self.ids.refresh_layout.refresh_done()

        Clock.schedule_once(refresh_callback, 0.5)

    def _update_values_on_receive_from_network(
            self,
            new_programs={},
            new_active_program_id=None,
            new_is_watering_programs_active=None
    ):
        if new_is_watering_programs_active is not None:
            self.are_programs_active = new_is_watering_programs_active
            self.ids.watering_program_switch.active = self.are_programs_active

        if new_active_program_id is not None:
            self.selected_program_id = new_active_program_id

        if len(new_programs.keys()) > 0:
            if self.selected_program_id is None:
                self.selected_program_id = self._watering_program_controller.get_active_watering_program_id()

            self.current_program_name = new_programs[self.selected_program_id].name

            self.programs.clear()
            for program in new_programs.values():
                self.programs[program.name] = program

            def refresh_callback(interval):
                self.ids.watering_program_spinner.values = list(self.programs.keys())
                self.ids.watering_program_spinner.text = self.current_program_name
            Clock.schedule_once(refresh_callback, 0.5)
