import datetime
import json
import random
import threading
from datetime import datetime
from typing import Tuple

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

        self._token = None

        self.start_connect()

        # Clock.schedule_once(self.connect, 0.1)

    def start_connect(self):
        if self.backend_thread is not None:
            self._is_logged_in.set()
            self.backend_thread.join()
            self.backend_thread = None

        self._is_logged_in.clear()
        self.backend_thread = threading.Thread(target=self._backend_ops)
        self.backend_thread.start()

    def _backend_request(self) -> int | tuple[datetime, str]:
        error, self.qr_data, _jwt_expiry = BackendController().get_qr_data(self._raspberry_id)

        if error:
            self.info_text = "Failed to get QR data: " + error
            return 100000

        expiry_datetime = datetime.fromtimestamp(int(_jwt_expiry) / 1000)
        return expiry_datetime, self.qr_data

    def _compute_wait_time(self, expiry_time) -> int:
        current_time = datetime.now()
        delta_time = expiry_time - current_time
        return delta_time.seconds

    def _backend_ops(self):
        print("Starting backend ops")

        _expiry_datetime, token = self._backend_request()
        self._connect_to_ws(token)
        print("Connected to WS")
        _wait_time = self._compute_wait_time(_expiry_datetime)

        if _wait_time > 20:
            _wait_time = 19

        print("Wait time:", _wait_time)

        while not self._is_logged_in.wait(_wait_time):
            if self._is_logged_in.is_set():
                self._is_logged_in.clear()
                return

            print("Another token request")

            _expiry_datetime, token = self._backend_request()
            self._connect_to_ws(token)
            _wait_time = self._compute_wait_time(_expiry_datetime)

            if _wait_time > 20:
                _wait_time = 19

    def _connect_to_ws(self, token):
        if self._is_logged_in.is_set():
            return

        if self._token is not None:
            self._disconnect_from_ws()

        self._token = token
        print("Token:", token)

        def _temp():
            BackendController().connect_to_ws(
                token,
                self._on_message_received,
                self._on_connection_error,
                self._on_connection_closed
            )

        threading.Thread(target=_temp).start()

        print("Connected to WS")

    def _on_message_received(self, ws, message):
        print(message)

        message_json = json.loads(message)
        if (message_json["token"] is None
                or message_json["token"] == ""
                or message_json["email"] is None
                or message_json["email"] == ""):
            return

        auth_token = message_json["token"]

        if FirebaseController().attempt_login(auth_token):
            self._is_logged_in.set()
            self.info_text = "Connected to " + message_json["email"]

    def _on_connection_closed(self, ws, stat_code, reason):
        print("Connection closed: ", stat_code, reason)

    def _on_connection_error(self, ws, error):
        print("Connection error:", error)
        self.info_text = "Connection error: " + error

    def _disconnect_from_ws(self):
        BackendController().close_ws()

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
