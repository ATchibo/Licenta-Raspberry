from kivy.lang import Builder
from kivymd.uix.screen import MDScreen

from utils.get_rasp_uuid import getserial

Builder.load_file("pages/connect_page.kv")


class ConnectPage(MDScreen):
    def __init__(self, **kwargs):
        super(ConnectPage, self).__init__(**kwargs)
        self.info_text = "Scan this QR code to connect to your account"
        self.qr_data = getserial()

