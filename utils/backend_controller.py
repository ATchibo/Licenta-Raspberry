import json
import os
import threading
from typing import Tuple, Any

import requests
from dotenv import load_dotenv
from websocket import WebSocketApp

from utils.firebase_controller import FirebaseController
import rel

from utils.remote_requests import RemoteRequests


class BackendController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(BackendController, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        load_dotenv()
        self._backend_url = os.getenv('BACKEND_URL')
        self._ws_url = self._backend_url.replace('http', 'ws')
        self._ws = None

    def send_notification(self, rasp_id, message):
        rasp_info = RemoteRequests().get_raspberry_info()

        data = {
            "raspberryId": rasp_id,
            "type": "LOG"
        }

        message = {
            "raspberryId": rasp_id,
            "body": message,
            "title": f"{rasp_info.raspberryName}",
            "data": json.dumps(data)
        }

        requests.post(f"{self._backend_url}/api/send-notification", json=message)

    def get_qr_data(self, rasp_id) -> tuple[str, str, str]:
        res = requests.post(f"{self._backend_url}/api/auth/request-qr-info/{rasp_id}")

        if res.ok:
            res = res.json()
            return "", res['token'], res['expirationTime']
        else:
            return res.text, "", ""

    def connect_to_ws(self, token, on_message: Any, on_error: Any, on_close: Any, on_open: Any = None):
        ws_url = f"{self._ws_url}/api/ws/register/{token}"

        self._ws = WebSocketApp(ws_url,
                          on_open=on_open,
                          on_message=on_message,
                          on_error=on_error,
                          on_close=on_close)

        self._ws.run_forever()

    def close_ws(self):
        if self._ws:
            self._ws.close()
            self._ws = None

    def send_message_to_ws(self, param):
        if self._ws:
            data = {
                "body": param
            }
            self._ws.send(json.dumps(data))

    def request_login_id(self, rasp_id) -> Tuple[str, str]:
        res = requests.post(f"{self._backend_url}/api/auth/request-login/{rasp_id}")

        if res.ok:
            res = res.json()
            return "", res['token']
        else:
            return res.text, ""

    def send_notification_for_login(self, rasp_id, message, ws_token):
        _data = {
            "wsToken": ws_token,
            "type": "LOGIN_REQUEST"
        }

        _message = {
            "title": "Login request",
            "body": message if message else "A linked device is requesting to log in",
            "raspberryId": rasp_id,
            "data": json.dumps(_data)
        }

        res = requests.post(f"{self._backend_url}/api/send-notification", json=_message)

        print(f"Login notification send result: {res.text}")
