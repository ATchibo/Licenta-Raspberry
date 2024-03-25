import datetime
import json
import threading
from datetime import datetime

from kivy.lang import Builder
from kivy.properties import StringProperty, Clock
from kivymd.uix.screen import MDScreen

from utils.WateringProgramController import WateringProgramController
from utils.backend_controller import BackendController
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.login_controller import LoginController
from utils.raspberry_controller import RaspberryController
from utils.remote_requests import RemoteRequests

Builder.load_file("pages/connect_page.kv")


class ConnectPage(MDScreen):
    qr_data = StringProperty()
    info_text = StringProperty()

    def __init__(self, **kwargs):
        super(ConnectPage, self).__init__(**kwargs)

        self._raspberry_id = getserial()

        self.info_text = ""
        self.qr_data = getserial()

        self.backend_thread = None
        self._is_logged_in = threading.Event()

        self._token = None
        self.qr_data = ""
        self._user_email = None

        LoginController().set_login_page_on_try_login_callback(self._on_login_controller_login_attempt)
        Clock.schedule_once(self._init_setup, 0.1)

    def _init_setup(self, *args):
        if self._is_logged_in.is_set():
            self.info_text = "Connected as " + self._user_email
            self.ids.connect_button.text = "Log out and connect again"
            self.qr_data = ""
            return

        self.info_text = "Device not logged in"
        self.ids.connect_button.text = "Connect"

    def start_connect(self):
        print("Starting to connect")

        if self.backend_thread is not None:
            self._is_logged_in.set()
            self.backend_thread.join()
            self.backend_thread = None

        RemoteRequests().unregister_raspberry()


        self.info_text = "Device not logged in"

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
            print("Connected to WS")
            _wait_time = self._compute_wait_time(_expiry_datetime)

            if _wait_time > 20:
                _wait_time = 19

            print("Wait time:", _wait_time)

    def _connect_to_ws(self, token):
        if self._is_logged_in.is_set():
            return

        if self._token is not None or self._token is not token:
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

        self._try_login(message_json["token"], message_json["email"])

    def _on_connection_closed(self, ws, stat_code, reason):
        print("Connection closed: ", stat_code, reason)

    def _on_connection_error(self, ws, error):
        print("Connection error in connect page:", error)
        self.info_text = "Connection error"

    def _disconnect_from_ws(self):
        BackendController().close_ws()

    def _try_login(self, auth_token: str, email: str):
        if RemoteRequests().attempt_login(auth_token):
            self._is_logged_in.set()
            self.info_text = "Connected to " + email

            self.ids.qr_code.disabled = True
            self.ids.connect_button.text = "Log out and connect again"
            self.qr_data = ""

            RemoteRequests().register_raspberry(RaspberryController().get_raspberry_info())
            RemoteRequests().register_raspberry_to_device(email)
            BackendController().send_message_to_ws("OK")

            RaspberryController().start_listening_for_watering_now()
            WateringProgramController().perform_initial_setup()

        else:
            self.info_text = "Failed to login"
            BackendController().send_message_to_ws("FAIL")

    # def _check_registered(self, *args):
    #     if not self.firebase_controller.is_raspberry_registered(serial=self.qr_data):
    #         self.info_text = "This Raspberry Pi is not registered to any account"
    #         self.ids.connect_button.text = "Register"
    #         self.qr_data = ""
    #         return False
    #
    #     if self._is_logged_in.is_set():
    #         self.info_text = "Connected as " + self._user_email
    #         self.ids.connect_button.text = "Log out and connect again"
    #         self.qr_data = ""
    #         return True
    #
    #     self.info_text = "Device not logged in"
    #     self.ids.connect_button.text = "Connect"

    def _on_login_controller_login_attempt(self, login_success, owner_email):
        if login_success:
            self.info_text = "Connected to " + owner_email
            self.ids.connect_button.text = "Log out and connect again"
            self.qr_data = ""
            self._is_logged_in.set()
        else:
            self.info_text = "Failed to login"
            self.qr_data = ""
            self.ids.connect_button.text = "Try again"
            self._is_logged_in.clear()
