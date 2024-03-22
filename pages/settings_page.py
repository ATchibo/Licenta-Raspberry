from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen

from domain.RaspberryInfo import RaspberryInfo
from domain.logging.MessageType import MessageType
from utils.local_storage_controller import LocalStorageController
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

        Clock.schedule_once(self._init_setup, 0.1)

    def on_pre_enter(self, *args):
        self._load_data()

    def _load_data(self):
        self.raspberry_info = RaspberryController().get_raspberry_info()

        self.device_name_variable = self.raspberry_info.raspberryName
        self.device_location_variable = self.raspberry_info.raspberryLocation
        self.device_description_variable = self.raspberry_info.raspberryDescription

        self.auto_watering_active_variable = self.raspberry_info.notifiableMessages[MessageType.AUTO_WATERING_CYCLE.value]
        self.manual_watering_active_variable = self.raspberry_info.notifiableMessages[MessageType.MANUAL_WATERING_CYCLE.value]
        self.moisture_measurement_active_variable = self.raspberry_info.notifiableMessages[MessageType.MOISTURE_LEVEL_MEASUREMENT.value]

    def _init_setup(self, *args):
        self._load_data()

        self.ids.sw1.bind(active=self.toggle_auto_watering)
        self.ids.sw2.bind(active=self.toggle_manual_watering)
        self.ids.sw3.bind(active=self.toggle_moisture_measurement)

    def toggle_auto_watering(self, instance, value):
        self.auto_watering_active_variable = value
        self.raspberry_info.notifiableMessages[MessageType.AUTO_WATERING_CYCLE.value] = value

        RaspberryController().update_raspberry_notification_info(MessageType.AUTO_WATERING_CYCLE, value)

    def toggle_manual_watering(self, instance, value):
        self.manual_watering_active_variable = value
        self.raspberry_info.notifiableMessages[MessageType.MANUAL_WATERING_CYCLE.value] = value

        RaspberryController().update_raspberry_notification_info(MessageType.MANUAL_WATERING_CYCLE, value)

    def toggle_moisture_measurement(self, instance, value):
        self.moisture_measurement_active_variable = value
        self.raspberry_info.notifiableMessages[MessageType.MOISTURE_LEVEL_MEASUREMENT.value] = value

        RaspberryController().update_raspberry_notification_info(MessageType.MOISTURE_LEVEL_MEASUREMENT, value)

    def refresh_data(self, *args):
        self._load_data()

    def reset_data(self, *args):
        LocalStorageController().clear_all()
        # TODO: Add a confirmation dialog and remove from firestore