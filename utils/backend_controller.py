import json
import os
import threading
from typing import Tuple, Any

import requests
from dotenv import load_dotenv
from websocket import WebSocketApp

from utils.firebase_controller import FirebaseController
import rel

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
        rasp_info = FirebaseController().get_raspberry_info(rasp_id)

        message = {
            "raspberryId": rasp_id,
            "body": message,
            "title": f"{rasp_info.raspberryName}"
        }

        requests.post(f"{self._backend_url}/api/send-notification", json=message)

    def get_qr_data(self, rasp_id) -> tuple[str, str, str]:
        res = requests.post(f"{self._backend_url}/api/auth/request-qr-info/{rasp_id}")

        if res.ok:
            res = res.json()
            return "", res['token'], res['expirationTime']
        else:
            return res.text, "", ""

    def connect_to_ws(self, token, on_message: Any, on_error: Any, on_close: Any):
        ws_url = f"{self._ws_url}/api/ws/register/{token}"

        self._ws = WebSocketApp(ws_url,
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
