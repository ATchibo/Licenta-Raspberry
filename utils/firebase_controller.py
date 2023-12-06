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

    def is_raspberry_registered(self, serial):
        query_result = self.db.collection('raspberry_info').where('serial', '==', serial).get()
        return len(query_result) > 0

    def register_raspberry(self, serial):
        if not self.is_raspberry_registered(serial):
            rpi_info = RaspberryInfo(raspberryId=serial)

            self.db.collection('raspberry_info').add(
                rpi_info.getInfoDict()
            )
        else:
            raise Exception("Raspberry Pi already registered")
