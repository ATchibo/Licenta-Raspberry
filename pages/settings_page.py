from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen

from domain.RaspberryInfo import RaspberryInfo
from domain.logging.MessageType import MessageType
from utils.raspberry_controller import RaspberryController

Builder.load_file("pages/settings_page.kv")


class SettingsPage(MDScreen):
    device_name_variable = StringProperty()
    device_location_variable = StringProperty()
    device_description_variable = StringProperty()

    auto_watering_active_variable = BooleanProperty(False)
    manual_watering_active_variable = BooleanProperty(False)
    moisture_measurement_active_variable = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(SettingsPage, self).__init__(**kwargs)

        self.raspberry_info = RaspberryController().get_raspberry_info()

        self.device_name_variable = self.raspberry_info.raspberryName
        self.device_location_variable = self.raspberry_info.raspberryLocation
        self.device_description_variable = self.raspberry_info.raspberryDescription

        self.auto_watering_active_variable = self.raspberry_info.notifiableMessages[MessageType.AUTO_WATERING_CYCLE.value]
        self.manual_watering_active_variable = self.raspberry_info.notifiableMessages[MessageType.MANUAL_WATERING_CYCLE.value]
        self.moisture_measurement_active_variable = self.raspberry_info.notifiableMessages[MessageType.MOISTURE_LEVEL_MEASUREMENT.value]

    def toggle_auto_watering(self):
        self.auto_watering_active_variable = not self.auto_watering_active_variable
        self.raspberry_info.notifiableMessages[MessageType.AUTO_WATERING_CYCLE.value] = self.auto_watering_active_variable

        RaspberryController().update_raspberry_notification_info(MessageType.AUTO_WATERING_CYCLE, self.auto_watering_active_variable)

    def toggle_manual_watering(self):
        self.manual_watering_active_variable = not self.manual_watering_active_variable
        self.raspberry_info.notifiableMessages[MessageType.MANUAL_WATERING_CYCLE.value] = self.manual_watering_active_variable

        RaspberryController().update_raspberry_notification_info(MessageType.MANUAL_WATERING_CYCLE, self.manual_watering_active_variable)

    def toggle_moisture_measurement(self):
        self.moisture_measurement_active_variable = not self.moisture_measurement_active_variable
        self.raspberry_info.notifiableMessages[MessageType.MOISTURE_LEVEL_MEASUREMENT.value] = self.moisture_measurement_active_variable

        RaspberryController().update_raspberry_notification_info(MessageType.MOISTURE_LEVEL_MEASUREMENT, self.moisture_measurement_active_variable)

    # TODO: listener for settings changes or a refresh button