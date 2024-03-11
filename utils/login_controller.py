import json
import threading

from utils.WateringProgramController import WateringProgramController
from utils.backend_controller import BackendController
from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial
from utils.raspberry_controller import RaspberryController


class LoginController:
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
        if (message_json["token"] is None
                or message_json["token"] == ""
                or message_json["email"] is None
                or message_json["email"] == ""):
            return

        self._try_login(message_json["token"], message_json["email"])

    def _on_connection_opened(self, ws):
        print("Connection opened")
        self._send_notification_for_login("Login request", self._ws_code)

    def _on_connection_closed(self, ws, stat_code, reason):
        print("Connection closed: ", stat_code, reason)

    def _on_connection_error(self, ws, error):
        print("Connection error:", error)

    def _disconnect_from_ws(self):
        BackendController().close_ws()

    def _try_login(self, auth_token: str, email: str):
        if FirebaseController().attempt_login(auth_token):
            self._is_logged_in.set()

            FirebaseController().register_raspberry_to_device(self._raspberry_id, email)
            BackendController().send_message_to_ws("OK")

            RaspberryController().start_listening_for_watering_now()
            WateringProgramController().perform_initial_setup()

            print("Logged in hehehehe")

        else:
            BackendController().send_message_to_ws("FAIL")
            print("Failed to login hehehehe")

    def try_initial_login(self):
        self._ws_code = self._backend_request()

        if self._ws_code is None:
            return

        print("Ws code: ", self._ws_code)

        self._connect_to_ws(self._ws_code)
