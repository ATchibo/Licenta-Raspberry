import os
import threading

import requests
from dotenv import load_dotenv

from utils.firebase_controller import FirebaseController
from utils.get_rasp_uuid import getserial


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

    def send_notification(self, rasp_id, message):
        rasp_info = FirebaseController().get_raspberry_info(rasp_id)

        message = {
            "raspberryId": rasp_id,
            "body": message,
            "title": f"{rasp_info.raspberryName}"
        }

        requests.post(f"{self._backend_url}/api/send-notification", json=message)
