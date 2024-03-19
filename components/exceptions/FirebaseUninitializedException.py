
class FirebaseUninitializedException(Exception):
    def __init__(self):
        super().__init__("Firebase is not initialized.")
