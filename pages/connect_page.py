import datetime
import random
import threading

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

from utils.backend_controller import BackendController
from utils.datetime_utils import get_current_datetime_tz
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial

Builder.load_file("pages/connect_page.kv")


class ConnectPage(MDScreen):
    qr_data = StringProperty()
    info_text = StringProperty()

    def __init__(self, **kwargs):
        super(ConnectPage, self).__init__(**kwargs)

        self._raspberry_id = getserial()

        self.info_text = "Scan this QR code to connect to your account"
        self.qr_data = getserial()
        self.firebase_controller = FirebaseController()

        self.backend_thread = None
        self._is_logged_in = threading.Event()

        self.start_connect()

        # Clock.schedule_once(self.connect, 0.1)

    def start_connect(self):
        self._is_logged_in.clear()
        self.backend_thread = threading.Thread(target=self._backend_ops)
        self.backend_thread.start()

    def _backend_request(self) -> int:
        print("Requesting QR data")

        error, self.qr_data, _jwt_expiry = BackendController().get_qr_data(self._raspberry_id)

        if error:
            self.info_text = "Failed to get QR data: " + error
            return 100000

        expiry_datetime = datetime.datetime.fromtimestamp(int(_jwt_expiry) / 1000)
        current_datetime = datetime.datetime.now()
        delta_time = expiry_datetime - current_datetime

        print("Delta time:", delta_time.seconds)

        return delta_time.seconds

    def _backend_ops(self):
        _wait_time = self._backend_request()

        while not self._is_logged_in.wait(_wait_time):
            if self._is_logged_in.is_set():
                self._is_logged_in.clear()
                return

            _wait_time = self._backend_request()


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
