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
        Clock.schedule_once(self.init, 0.1)

        self.raspberry_controller = RaspberryController()
        self.watering_label_variable = f"Water amount: 0L\nTime running: 0s"
        self.water_now_disabled_variable = False

        self.bind_raspberry_controller_properties()

    def init(self, *args):
        self.init_dropdown(*args)

    def init_dropdown(self, *args):
        dropdown = DropDown()
        for index in range(10):
            btn = Button(text='Value %d' % index, size_hint_y=None, height=44)
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)

        mainbutton = self.ids.mainbutton
        mainbutton.bind(on_release=dropdown.open)
        dropdown.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', x))

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
            moisture_percentage = self.raspberry_controller.get_moisture_percentage()
            self.ids.water_now_label.text = f"Moisture: {moisture_percentage}%"
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
        self.raspberry_controller.set_callback_for_watering_updates(callback=self.update_watering_label_variable)

    def update_watering_label_variable(self, is_watering, watering_time, liters_sent):
        print("Is watering: ", is_watering)

        self.water_now_disabled_variable = is_watering
        self.watering_label_variable = f"Water amount: {liters_sent}L\nTime running: {watering_time}s"
