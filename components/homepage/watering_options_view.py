from kivy.clock import Clock
from kivy.garden.matplotlib import FigureCanvasKivyAgg
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.menu import MDDropdownMenu
from matplotlib import pyplot as plt

from utils.raspberry_controller import RaspberryController

Builder.load_file("components/homepage/watering_options_view.kv")


class WateringOptionsView(MDBoxLayout):
    watering_label_variable = StringProperty()

    def __init__(self, **kwargs):
        super(WateringOptionsView, self).__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = 1

        self.raspberry_controller = RaspberryController()
        self.watering_label_variable = f"Water amount: 0L\nTime running: 0s"
        self.water_now_disabled_variable = False

        self.programs = {}
        self.current_program_name = ""
        self.are_programs_active = True

        self.bind_raspberry_controller_properties()
        self.load_programs()

        Clock.schedule_once(self.init, 0.1)

    def init(self, *args):
        if len(self.current_program_name) > 0:
            self.ids.watering_program_spinner.text = self.current_program_name

    def change_program(self):
        self.current_program_name = self.ids.watering_program_spinner.text
        self.raspberry_controller.set_active_watering_program_id(self.programs[self.current_program_name].id)

    def load_programs(self):
        _programs = self.raspberry_controller.get_watering_programs()
        self.are_programs_active = self.raspberry_controller.get_is_watering_programs_active()
        selected_program_id = self.raspberry_controller.get_active_watering_program_id()

        if selected_program_id is not None:
            for program in _programs:
                if program.id == selected_program_id:
                    self.current_program_name = program.name
                    break

        self.programs = {program.name: program for program in _programs}

    def set_item(self, text_item):
        self.ids.drop_item.set_item(text_item)
        self.menu.dismiss()

    def toggle_water_now(self):
        if self.water_now_disabled_variable:
            self.stop_watering()
        else:
            self.water_now()

    def water_now(self):
        print("Watering now")

        if self.raspberry_controller.water_now():
            # moisture_percentage = self.raspberry_controller.get_moisture_percentage()
            self.ids.water_now_button.text = "Stop watering"
            self.water_now_disabled_variable = True
        else:
            self.ids.water_now_label.text = "Could not start watering"

    def stop_watering(self):
        print("Stopping watering")

        self.raspberry_controller.stop_watering()
        self.ids.water_now_button.text = "Water now"
        self.water_now_disabled_variable = False

    def bind_raspberry_controller_properties(self):
        self.raspberry_controller.set_callback_for_watering_updates(callback=self._update_watering_now_info)

    def _update_watering_now_info(self, is_watering, watering_time, liters_sent):
        if self.water_now_disabled_variable is not is_watering:
            if is_watering:
                self.ids.water_now_button.text = "Stop watering"
            else:
                self.ids.water_now_button.text = "Water now"

        self.water_now_disabled_variable = is_watering
        self.watering_label_variable = f"Water amount: {liters_sent}L\nTime running: {watering_time}s"

    def toggle_watering_program(self):
        self.are_programs_active = not self.are_programs_active
        self.raspberry_controller.set_is_watering_programs_active(self.are_programs_active)