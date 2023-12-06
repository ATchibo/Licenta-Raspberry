from kivy.clock import Clock
from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial

Builder.load_file("pages/connect_page.kv")


class ConnectPage(MDScreen):
    def __init__(self, **kwargs):
        super(ConnectPage, self).__init__(**kwargs)
        self.info_text = "Scan this QR code to connect to your account"
        self.qr_data = getserial()
        self.firebase_controller = FirebaseController()

        Clock.schedule_once(self.connect, 0.1)

    def check_registered(self):
        if self.firebase_controller.is_raspberry_registered(serial=self.qr_data):
            self.ids.qr_code.opacity = 1
            self.ids.qr_code.disabled = False
            self.ids.connect_button.opacity = 0
            self.ids.connect_button.disabled = True
            self.ids.info_label.text = self.info_text
            return True

        self.ids.info_label.text = "This Raspberry Pi is not registered to any account"
        self.ids.qr_code.opacity = 0
        self.ids.qr_code.disabled = True
        self.ids.connect_button.opacity = 1
        self.ids.connect_button.disabled = False
        return False

    def connect(self, *args):
        if self.check_registered():
            return
        try:
            self.firebase_controller.register_raspberry(serial=self.qr_data)
            self.ids.info_label.text = self.info_text
            self.ids.qr_code.opacity = 1
            self.ids.qr_code.disabled = False
            self.ids.connect_button.opacity = 0
            self.ids.connect_button.disabled = True
        except Exception as e:
            self.ids.info_label.text = "Failed to register Raspberry Pi"
            print(e)
