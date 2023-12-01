import firebase_admin
from firebase_admin import credentials, firestore


class FirebaseController:
    def __init__(self):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)

        self.db = firestore.client()
