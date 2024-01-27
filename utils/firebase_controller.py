import firebase_admin
from firebase_admin import credentials, firestore

from domain.RaspberryInfo import RaspberryInfo


class FirebaseController:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(FirebaseController, cls).__new__(cls)
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)
            cls._instance.db = firestore.client()
        return cls._instance

    def __init__(self):
        self.deviceLinksCollectionName = "device_links"
        self.raspberryInfoCollectionName = "raspberry_info"
        self.moistureInfoCollectionName = "humidity_readings"
        self.wateringNowCollectionName = "watering_info"
        self.watering_now_callback = None
        self.watering_now_listener = None

    def is_raspberry_registered(self, serial):
        query_result = self.db.collection(self.raspberryInfoCollectionName).where('raspberryId', '==', serial).get()
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

        query = moisture_info_ref.where('raspberryId', '==', rpi_id) \
            .where('measurementTime', '>=', start_datetime) \
            .where('measurementTime', '<=', end_datetime)

        docs = query.stream()
        moisture_info_list = [doc.to_dict() for doc in docs]

        return moisture_info_list

    def update_watering_info(self, serial, command, liters_sent, watering_time):
        doc_ref = self.db.collection(self.wateringNowCollectionName).document(serial)

        doc_ref.update({
            'command': command,
            'watering_duration': watering_time,
            'water_volume': liters_sent
        })

