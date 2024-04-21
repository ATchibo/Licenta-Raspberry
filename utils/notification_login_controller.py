import json
import threading

from utils.WateringProgramController import WateringProgramController
from utils.backend_controller import BackendController
from utils.event_logger import EventLogger
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.raspberry_controller import RaspberryController
from utils.remote_requests import RemoteRequests


class NotificationLoginController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self._raspberry_id = getserial()
        self._is_logged_in = threading.Event()
        self._user_email = None
        self._ws_code = None

        self._login_page_on_try_login_callback = None

        self._initial_login_delay_seconds = 60 * 60 * 5  # 5 hours
        self._retry_login_notification_delay_seconds = self._initial_login_delay_seconds
        self._retry_login_notification_event = threading.Event()
        self._retry_login_notification_thread = None

        self._start_retry_login_notification_thread()

    def set_login_page_on_try_login_callback(self, callback):
        self._login_page_on_try_login_callback = callback

    def _backend_request(self):
        error, response = BackendController().request_login_id(self._raspberry_id)

        if error:
            print("Failed to send notification for login: " + error)
            return None
            # raise Exception("Failed to send notification for login: " + response)

        return response

    def _send_notification_for_login(self, message, ws_code):
        BackendController().send_notification_for_login(self._raspberry_id, message, ws_code)

    def _connect_to_ws(self, token):
        if self._is_logged_in.is_set():
            return

        def _temp():
            BackendController().close_ws()
            BackendController().connect_to_ws(
                token,
                self._on_message_received,
                self._on_connection_error,
                self._on_connection_closed,
                self._on_connection_opened
            )

        threading.Thread(target=_temp, daemon=True).start()

        print("Connected to WS")

    def _on_message_received(self, ws, message):
        print(message)

        message_json = json.loads(message)

        if "message" in message_json.keys() and message_json["message"] == "REJECT_CONN":
            BackendController().close_ws()
            return

        if (message_json["token"] is None
                or message_json["token"] == ""
                or message_json["email"] is None
                or message_json["email"] == ""):
            return

        self._try_login(message_json["token"], message_json["email"])

    def _on_connection_opened(self, ws):
        print("Connection opened")
        _raspberry_info = RaspberryController().get_raspberry_info()
        _message = f"{_raspberry_info.raspberryName} requests permission to log in"
        self._send_notification_for_login(_message, self._ws_code)

    def _on_connection_closed(self, ws, stat_code, reason):
        print("Connection closed: ", stat_code, reason)

    def _on_connection_error(self, ws, error):
        print("Connection error in login controller:", error)

    def _disconnect_from_ws(self):
        BackendController().close_ws()

    def _try_login(self, auth_token: str, email: str):
        if FirebaseController().login_with_custom_token(auth_token):
            self._is_logged_in.set()

            BackendController().send_message_to_ws("OK")
            self._login_page_on_try_login_callback(True, email)

            print("Logged in hehehehe")

            self._retry_login_notification_delay_seconds = self._initial_login_delay_seconds

        else:
            BackendController().send_message_to_ws("FAIL")
            self._login_page_on_try_login_callback(False, None)

            print("Failed to login hehehehe")

            self._retry_login_notification_delay_seconds *= 2

        self._start_retry_login_notification_thread()

    def try_send_login_notification(self):
        self._ws_code = self._backend_request()

        if self._ws_code is None:
            return

        print("Ws code: ", self._ws_code)

        self._connect_to_ws(self._ws_code)

    def _start_retry_login_notification_thread(self):
        self._retry_login_notification_event.set()
        if self._retry_login_notification_thread is not None:
            self._retry_login_notification_thread.join()
        self._retry_login_notification_event.clear()

        self._retry_login_notification_thread = threading.Thread(target=self._retry_login_notification, daemon=True)
        self._retry_login_notification_thread.start()

    def _retry_login_notification(self):
        while not self._retry_login_notification_event.is_set():
            self._retry_login_notification_event.wait(self._retry_login_notification_delay_seconds)
            if self._retry_login_notification_event.is_set():
                return

            if not FirebaseController().is_logged_in():
                self._is_logged_in.clear()
                self.try_send_login_notification()
