import threading

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter

from domain.RaspberryInfo import RaspberryInfo
from domain.WateringProgram import WateringProgram


class FirebaseController:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(FirebaseController, cls).__new__(cls)
                cred = credentials.Certificate("serviceAccountKey.json")
                firebase_admin.initialize_app(cred)
                cls._instance.db = firestore.client()
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self.deviceLinksCollectionName = "device_links"
        self.raspberryInfoCollectionName = "raspberry_info"
        self.moistureInfoCollectionName = "humidity_readings"
        self.wateringNowCollectionName = "watering_info"
        self.wateringProgramsCollectionName = "watering_programs"
        self.wateringProgramsCollectionNestedCollectionName = "programs"
        self.globalWateringProgramsCollectionName = "global_watering_programs"
        self.logsCollectionName = "logs"
        self.deviceInfoCollectionName = "device_info"

        self.watering_now_callback = None
        self.watering_now_listener = None

        self.watering_programs_callback = None
        self.watering_programs_fields_listener = None
        self.watering_programs_collection_listener = None

    def is_raspberry_registered(self, serial):
        query_result = self.db.collection(self.raspberryInfoCollectionName).where(
            filter=FieldFilter('raspberryId', '==', serial)
        ).get()
        return len(query_result) > 0

    def register_raspberry(self, serial):
        if not self.is_raspberry_registered(serial):
            rpi_info = RaspberryInfo(raspberryId=serial)

            self.db.collection(self.raspberryInfoCollectionName).add(
                rpi_info.getInfoDict()
            )
        else:
            raise Exception("Raspberry Pi already registered")

    def add_watering_now_listener(self, serial, callback):
        self.watering_now_callback = callback

        doc_ref = self.db.collection(self.wateringNowCollectionName).document(serial)
        self.watering_now_listener = doc_ref.on_snapshot(callback)

    def get_moisture_info_for_rasp_id(self, rpi_id, start_datetime, end_datetime):
        moisture_info_ref = self.db.collection(self.moistureInfoCollectionName)

        query = (moisture_info_ref
                 .where(filter=FieldFilter('raspberryId', '==', rpi_id))
                 .where(filter=FieldFilter('measurementTime', '>=', start_datetime))
                 .where(filter=FieldFilter('measurementTime', '<=', end_datetime))
                 )

        docs = query.stream()
        moisture_info_list = [doc.to_dict() for doc in docs]

        return moisture_info_list

    def update_watering_info(self, serial, command, liters_sent, watering_time):
        doc_ref = self.db.collection(self.wateringNowCollectionName).document(serial)

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

    def get_watering_programs(self, raspberry_id):
        watering_programs_ref = self.db.collection(self.wateringProgramsCollectionName).document(
            raspberry_id).collection(
            self.wateringProgramsCollectionNestedCollectionName)

        watering_programs = []

        for doc_snapshot in watering_programs_ref.get():
            watering_program_data = doc_snapshot.to_dict()

            if watering_program_data:
                watering_program_data["id"] = doc_snapshot.id
                watering_programs.append(WateringProgram().fromDict(watering_program_data))

        global_watering_programs_ref = self.db.collection(self.globalWateringProgramsCollectionName)

        global_watering_programs = []

        for doc_snapshot in global_watering_programs_ref.get():
            global_watering_program_data = doc_snapshot.to_dict()

            if global_watering_program_data:
                global_watering_program_data["id"] = doc_snapshot.id
                global_watering_programs.append(WateringProgram().fromDict(global_watering_program_data))

        watering_programs.extend(global_watering_programs)
        return watering_programs

    def get_active_watering_program_id(self, raspberry_id):
        doc_ref = self.db.collection(self.wateringProgramsCollectionName).document(raspberry_id)
        doc = doc_ref.get()

        try:
            return doc.get("activeProgramId")
        except Exception as e:
            return None

    def set_active_watering_program_id(self, raspberry_id, program_id):
        doc_ref = self.db.collection(self.wateringProgramsCollectionName).document(raspberry_id)
        doc_ref.update({"activeProgramId": program_id})

    def get_is_watering_programs_active(self, raspberry_id):
        doc_ref = self.db.collection(self.wateringProgramsCollectionName).document(raspberry_id)
        doc = doc_ref.get()
        return doc.get("wateringProgramsEnabled")

    def set_is_watering_programs_active(self, raspberry_id, is_active):
        doc_ref = self.db.collection(self.wateringProgramsCollectionName).document(raspberry_id)
        doc_ref.update({"wateringProgramsEnabled": is_active})

    def add_listener_for_watering_programs_changes(self, raspberry_id, _update_values_on_receive_from_network):
        self.watering_programs_callback = _update_values_on_receive_from_network

        fields_doc_ref = self.db.collection(self.wateringProgramsCollectionName).document(raspberry_id)
        self.watering_programs_fields_listener = fields_doc_ref.on_snapshot(_update_values_on_receive_from_network)

        programs_collection = fields_doc_ref.collection(self.wateringProgramsCollectionNestedCollectionName)
        programs_collection_query = programs_collection.where(filter=FieldFilter('name', '!=', ''))
        self.watering_programs_collection_listener = programs_collection_query.on_snapshot(
            _update_values_on_receive_from_network)

    # Event logger methods
    def get_log_messages(self, raspberry_id):
        try:
            log_messages_ref = self.db.collection(self.logsCollectionName).document(raspberry_id).get()
            log_messages = log_messages_ref.get("messages")
            return log_messages, True
        except Exception as e:
            print(f"Error getting log messages: {e}")
            return None, False

    def add_log_message(self, raspberry_id, log_message):
        try:
            data = {
                log_message.get_timestamp(): log_message.get_message()
            }

            log_messages_ref = self.db.collection(self.logsCollectionName).document(raspberry_id)
            log_messages_ref.update({"messages": data})
            return True
        except Exception as e:
            print(f"Error adding log message: {e}")
            return False

    def get_notifiable_messages(self, raspberry_id):
        try:
            notifiable_messages_ref = self.db.collection(self.deviceInfoCollectionName).document(raspberry_id).get()
            notifiable_messages = notifiable_messages_ref.get("notifiable_messages")
            return notifiable_messages, True
        except Exception as e:
            print(f"Error getting notifiable messages: {e}")
            return None, False

    def update_notifiable_message(self, raspberry_id, notifiable_message, value):
        try:
            data = {
                notifiable_message: value
            }

            notifiable_messages_ref = self.db.collection(self.deviceInfoCollectionName).document(raspberry_id)
            notifiable_messages_ref.update({"notifiable_messages": data})
            return True
        except Exception as e:
            print(f"Error updating notifiable message: {e}")
            return False
