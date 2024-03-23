import json
import os
import threading
from typing import List, Any

# import firebase_admin
import keyring
from dotenv import load_dotenv
from google.cloud.firestore_v1 import FieldFilter
from requests import HTTPError

from components.exceptions.FirebaseUninitializedException import FirebaseUninitializedException
from domain.RaspberryInfo import RaspberryInfo
from domain.WateringProgram import WateringProgram

import requests
import google.oauth2.credentials
from google.cloud import firestore

from utils.get_rasp_uuid import getserial


class FirebaseController:
    __project_id = None
    __api_key = None
    __refresh_token = None
    __token = None
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(FirebaseController, cls).__new__(cls)

        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self.db = None
        self._ownerInfoCollectionName = "owner_info"
        self._raspberryInfoCollectionName = "raspberry_info"
        self._moistureInfoCollectionName = "humidity_readings"
        self._wateringNowCollectionName = "watering_info"
        self._wateringProgramsCollectionName = "watering_programs"
        self._wateringProgramsCollectionNestedCollectionName = "programs"
        self._globalWateringProgramsCollectionName = "global_watering_programs"
        self._logsCollectionName = "logs"
        self._wsCollectionName = "general_purpose_ws"

        self.watering_now_callback = None
        self.watering_now_listener = None

        self.watering_programs_callback = None
        self.watering_programs_fields_listener = None
        self.watering_programs_collection_listener = None

    def _is_raspberry_registered(self, serial) -> bool:
        if self.db is None:
            raise FirebaseUninitializedException()

        print("Checking if raspberry is registered")
        doc_ref = self.db.collection(self._raspberryInfoCollectionName).document(serial)
        query_result = doc_ref.get()
        print("Raspberry registered query result: " + str(query_result.exists))
        return query_result.exists

    def register_raspberry(self, rpi_info: RaspberryInfo) -> bool:
        print("Registering raspberry with id: " + rpi_info.raspberryId)
        print("Raspberry info: " + str(rpi_info.to_dict()))

        if self.db is None:
            raise FirebaseUninitializedException()

        print("Registering raspberry: db is not none")

        _is_registered = self._is_raspberry_registered(rpi_info.raspberryId)
        print("Is registered: " + str(_is_registered))

        if not _is_registered:
            print("Registering raspberry: " + rpi_info.raspberryId)
            self.db.collection(self._raspberryInfoCollectionName).document(rpi_info.raspberryId).set(rpi_info.to_dict())

            return True
        else:
            raise Exception("Raspberry Pi already registered")

    def get_raspberry_info(self, serial) -> RaspberryInfo | None:
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._raspberryInfoCollectionName).document(serial)

        if not doc_ref.get().exists:
            return None

        doc_dict = doc_ref.get().to_dict()

        rasp_info = RaspberryInfo().from_dict(doc_dict)
        return rasp_info

    def add_watering_now_listener(self, serial, callback):
        if self.db is None:
            raise FirebaseUninitializedException()

        self.watering_now_callback = callback

        doc_ref = self.db.collection(self._wateringNowCollectionName).document(serial)
        self.watering_now_listener = doc_ref.on_snapshot(callback)

    def get_moisture_info_for_rasp_id(self, rpi_id, start_datetime, end_datetime) -> list[Any] | None:
        if self.db is None:
            raise FirebaseUninitializedException()

        moisture_info_ref = self.db.collection(self._moistureInfoCollectionName)

        query = (moisture_info_ref
                 .where(filter=FieldFilter('raspberryId', '==', rpi_id))
                 .where(filter=FieldFilter('measurementTime', '>=', start_datetime))
                 .where(filter=FieldFilter('measurementTime', '<=', end_datetime))
                 )

        docs = query.stream()
        moisture_info_list = [doc.to_dict() for doc in docs]

        return moisture_info_list

    def update_watering_info(self, serial, command, liters_sent, watering_time):
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._wateringNowCollectionName).document(serial)

        if command != '':
            doc_ref.update({
                'command': command,
                'watering_duration': watering_time,
                'water_volume': liters_sent
            })
        else:
            doc_ref.update({
                'watering_duration': watering_time,
                'water_volume': liters_sent
            })

        return True

    def get_watering_programs(self, raspberry_id) -> list[WateringProgram] | None:
        if self.db is None:
            raise FirebaseUninitializedException()

        watering_programs_ref = self.db.collection(self._wateringProgramsCollectionName).document(
            raspberry_id).collection(
            self._wateringProgramsCollectionNestedCollectionName)

        watering_programs = []

        for doc_snapshot in watering_programs_ref.get():
            watering_program_data = doc_snapshot.to_dict()

            if watering_program_data:
                watering_program_data["id"] = doc_snapshot.id
                watering_programs.append(WateringProgram().fromDict(watering_program_data))

        # global_watering_programs_ref = self.db.collection(self._globalWateringProgramsCollectionName)
        #
        # global_watering_programs = []
        #
        # for doc_snapshot in global_watering_programs_ref.get():
        #     global_watering_program_data = doc_snapshot.to_dict()
        #
        #     if global_watering_program_data:
        #         global_watering_program_data["id"] = doc_snapshot.id
        #         global_watering_programs.append(WateringProgram().fromDict(global_watering_program_data))
        #
        # watering_programs.extend(global_watering_programs)
        return watering_programs

    def get_active_watering_program_id(self, raspberry_id) -> str | None:
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._wateringProgramsCollectionName).document(raspberry_id)
        doc = doc_ref.get()

        try:
            return doc.get("activeProgramId")
        except Exception as e:
            raise Exception(f"Error getting active watering program id: {e}")

    def set_active_watering_program_id(self, raspberry_id, program_id):
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._wateringProgramsCollectionName).document(raspberry_id)
        doc_ref.update({"activeProgramId": program_id})

    def get_is_watering_programs_active(self, raspberry_id) -> bool:
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._wateringProgramsCollectionName).document(raspberry_id)
        doc = doc_ref.get()
        try:
            return doc.get("wateringProgramsEnabled")
        except Exception as e:
            raise Exception(f"Error getting is watering programs active: {e}")

    def set_is_watering_programs_active(self, raspberry_id, is_active):
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._wateringProgramsCollectionName).document(raspberry_id)
        doc_ref.update({"wateringProgramsEnabled": is_active})

    def add_listener_for_watering_programs_changes(self, raspberry_id, _update_values_on_receive_from_network):
        if self.db is None:
            raise FirebaseUninitializedException()

        self.watering_programs_callback = _update_values_on_receive_from_network

        fields_doc_ref = self.db.collection(self._wateringProgramsCollectionName).document(raspberry_id)
        self.watering_programs_fields_listener = fields_doc_ref.on_snapshot(_update_values_on_receive_from_network)

        programs_collection = fields_doc_ref.collection(self._wateringProgramsCollectionNestedCollectionName)
        programs_collection_query = programs_collection.where(filter=FieldFilter('name', '!=', ''))
        self.watering_programs_collection_listener = programs_collection_query.on_snapshot(
            _update_values_on_receive_from_network)

    def add_listener_for_log_messages_changes(self, raspberry_id, _update_values_on_receive_from_network):
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._logsCollectionName).document(raspberry_id)
        doc_ref.on_snapshot(_update_values_on_receive_from_network)

    def unregister_raspberry(self, raspberry_id):
        if self.db is None:
            raise FirebaseUninitializedException()

        query = (self.db.collection(self._ownerInfoCollectionName)
                 .where(filter=FieldFilter("raspberry_ids", "array_contains", raspberry_id)))

        docs = query.stream()

        my_doc = None

        for doc in docs:
            if my_doc is not None:
                print("More than one document found for the same raspberry id")
                return

            my_doc = doc

        if my_doc is None:
            print("No document found for the raspberry id")
            return

        owner_id = my_doc.id

        print(f"Owner id: {owner_id}")

        self.db.collection(self._ownerInfoCollectionName).document(owner_id).update({
            "raspberry_ids": firestore.ArrayRemove([raspberry_id])
        })

        return True

    def link_raspberry_to_device(self, raspberry_id, device_id) -> bool:
        if self.db is None:
            raise FirebaseUninitializedException()

        doc_ref = self.db.collection(self._ownerInfoCollectionName).document(device_id)
        doc_ref.update({"raspberry_ids": firestore.ArrayUnion([raspberry_id])})

        return True

    # Event logger methods
    def get_log_messages(self, raspberry_id) -> dict:
        if self.db is None:
            raise FirebaseUninitializedException()

        try:
            log_messages_ref = self.db.collection(self._logsCollectionName).document(raspberry_id).get()
            log_messages = log_messages_ref.get("messages")
            return log_messages
        except Exception as e:
            raise Exception(f"Error getting log messages: {e}")

    def add_log_message(self, raspberry_id, log_message) -> bool:
        if self.db is None:
            raise FirebaseUninitializedException()

        try:
            data = {
                str(log_message.get_timestamp()): log_message.get_message()
            }

            log_messages_ref = self.db.collection(self._logsCollectionName).document(raspberry_id)
            log_messages_ref.set({"messages": data}, merge=True)
            return True
        except Exception as e:
            raise Exception(f"Error adding log message: {e}")

    def update_raspberry_notifiable_message(self, raspberry_id, message_type, value):
        if self.db is None:
            raise FirebaseUninitializedException()

        data = {
            message_type.value: value
        }

        doc_ref = self.db.collection(self._raspberryInfoCollectionName).document(raspberry_id)
        doc_ref.set({"notifiable_messages": data}, merge=True)

    def get_notifiable_messages(self, raspberry_id):
        try:
            notifiable_messages_ref = self.db.collection(self._raspberryInfoCollectionName).document(raspberry_id).get()
            notifiable_messages = notifiable_messages_ref.get("notifiable_messages")
            return notifiable_messages, True

        except Exception as e:
            raise Exception(f"Error getting notifiable messages: {e}")

    def update_moisture_info(self, _raspberry_id, param):
        if self.db is None:
            raise FirebaseUninitializedException()

        try:
            data = {
                "soilMoisture": param
            }

            self.db.collection(self._wateringNowCollectionName).document(_raspberry_id).set(data, merge=True)
            return True
        except Exception as e:
            raise Exception(f"Error updating moisture info: {e}")

    def add_moisture_percentage_measurement(self, _raspberry_id, moisture_perc, timestamp) -> bool:
        if self.db is None:
            raise FirebaseUninitializedException()

        try:
            data = {
                "raspberryId": _raspberry_id,
                "measurementTime": timestamp,
                "measurementValuePercent": moisture_perc
            }

            self.db.collection(self._moistureInfoCollectionName).add(data)
            return True

        except Exception as e:
            raise Exception(f"Error adding moisture percentage measurement: {e}")

    def unsubscribe_watering_now_listener(self):
        self.watering_now_listener.unsubscribe()

    def _start_listening_for_ping(self):
        if self.db is None:
            return

        doc_ref = self.db.collection(self._wsCollectionName).document(getserial())
        doc_ref.set({"message": "+"})
        doc_ref.on_snapshot(self._on_ping_from_phone)

    def _on_ping_from_phone(self,
        doc_snapshot,
        changes,
        read_time):

        for change in changes:
            changed_doc = change.document
            doc_data = changed_doc.to_dict()

            if "message" in doc_data.keys():
                if doc_data["message"] == "PING":
                    self.db.collection(self._wsCollectionName).document(getserial()).set({"message": "PONG"})

    def login_with_custom_token(self, token=None):
        print("Attempting login")

        self.db = None

        if token is None:
            return False

        load_dotenv()
        self.__api_key = os.getenv("PROJECT_WEB_API_KEY")
        self.__project_id = os.getenv("PROJECT_ID")

        request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={self.__api_key}"
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        data = json.dumps({"token": token, "returnSecureToken": True})
        response = requests.post(request_url, headers=headers, data=data)

        try:
            response.raise_for_status()
        except (HTTPError, Exception):
            content = response.json()
            error = f"error: {content['error']['message']}"

            raise Exception(error)

        json_response = response.json()
        _token = json_response["idToken"]
        _refresh_token = json_response["refreshToken"]
        _expires_in = int(json_response["expiresIn"])

        if self._authenticate_firestore_client_with_tokens(_token, _refresh_token):
            self._start_listening_for_ping()

            self.__token = _token
            self.__refresh_token = _refresh_token
            self._schedule_token_refresh(_expires_in - 1)

            return True
        else:
            return False

    def anonymous_login(self):
        load_dotenv()
        self.__api_key = os.getenv("PROJECT_WEB_API_KEY")
        self.__project_id = os.getenv("PROJECT_ID")

        request_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.__api_key}"
        headers = {"Content-Type": "application/json; charset=UTF-8"}
        data = json.dumps({"returnSecureToken": True})
        response = requests.post(request_url, headers=headers, data=data)
        try:
            response.raise_for_status()
        except (HTTPError, Exception):
            content = response.json()
            error = f"error: {content['error']['message']}"

            self._instance.db = None

            raise Exception(error)

        json_response = response.json()
        _token = json_response["idToken"]
        _refresh_token = json_response["refreshToken"]
        _expires_in = int(json_response["expiresIn"])

        if self._authenticate_firestore_client_with_tokens(_token, _refresh_token):
            self._start_listening_for_ping()
            self.__token = _token
            self.__refresh_token = _refresh_token
            self._schedule_token_refresh(_expires_in - 1)

            return True
        else:
            return False

    def _get_new_tokens(self, refresh_token) -> tuple[str, str, int] | None:
        load_dotenv()
        self.__api_key = os.getenv("PROJECT_WEB_API_KEY")

        request_url = f"https://securetoken.googleapis.com/v1/token?key={self.__api_key}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        response = requests.post(request_url, headers=headers, data=data)

        try:
            response.raise_for_status()
        except (HTTPError, Exception):
            content = response.json()
            error = f"error: {content['error']['message']}"

            raise Exception(error)

        json_response = response.json()
        _token = json_response["id_token"]
        _refresh_token = json_response["refresh_token"]
        _expires_in = int(json_response["expires_in"])

        return _token, _refresh_token, _expires_in

    def _authenticate_firestore_client_with_tokens(self, token, refresh_token) -> bool:
        try:
            _credentials = google.oauth2.credentials.Credentials(token,
                                                                 refresh_token,
                                                                 client_id="",
                                                                 client_secret="",
                                                                 token_uri=f"https://securetoken.googleapis.com/v1/token?key={self.__api_key}"
                                                                 )

            self._instance.db = firestore.Client(self.__project_id, _credentials)
            return True

        except Exception as e:
            print(f"Error attempting anonymous login: {e}")
            self._instance.db = None
            return False

    def _schedule_token_refresh(self, delay):
        _refresh_thread = threading.Timer(delay, self._auto_refresh_firestore_client)
        _refresh_thread.daemon = True
        _refresh_thread.start()

    def _auto_refresh_firestore_client(self):
        try:
            _token, _refresh_token, _expires_in = self._get_new_tokens(self.__refresh_token)

            if self._authenticate_firestore_client_with_tokens(_token, _refresh_token):
                self.__token = _token
                self.__refresh_token = _refresh_token
                self._schedule_token_refresh(_expires_in - 1)

                print("Token refreshed")

        except Exception as e:
            print(f"Error attempting to refresh token: {e}")


