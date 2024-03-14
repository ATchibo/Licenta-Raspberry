import json
import threading
from datetime import datetime

from domain.logging.LogMessage import LogMessage
from domain.logging.ManualWateringCycleMessage import ManualWateringCycleMessage
from domain.logging.MessageType import MessageType
from domain.logging.MoistureMeasurementMessage import MoistureMeasurementMessage
from utils.backend_controller import BackendController
from utils.firebase_controller import FirebaseController
from domain.logging.AutoWateringCycleMessage import AutoWateringCycleMessage
from utils.get_rasp_uuid import getserial


class EventLogger:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if not cls._instance:
                cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', None):
            return
        self._initialized = True

        self._raspberry_id = getserial()

        self._log_messages = []
        self._notifiable_messages = {}

        self._gui_log_update_callback = None
        self._gui_notifiables_update_callback = None

    def perform_initial_setup(self):
        FirebaseController().add_listener_for_log_messages_changes(
            self._raspberry_id,
            self._update_logs_on_receive_from_network
        )
        #
        # FirebaseController().add_listener_for_notifiable_messages_changes(
        #     self._raspberry_id,
        #     self._update_notifiables_on_receive_from_network
        # )

        # self.load_initial_data()

    def load_log_messages(self):
        log_messages, success = FirebaseController().get_log_messages(self._raspberry_id)

        # print(f"Log messages: {log_messages}")

        if not success:
            return None, False

        self._log_messages = []

        for log_message_key, log_message_value in log_messages.items():
            self._log_messages.append(
                LogMessage(
                    message=log_message_value,
                    level=MessageType.ANY,
                    timestamp=datetime.strptime(log_message_key[:-6], "%Y-%m-%d %H:%M:%S.%f")
                )
            )

        self._log_messages.sort(key=lambda x: x.get_timestamp(), reverse=True)

        return self._log_messages, True

    def _load_notifiable_messages(self):
        notifiable_messages, success = FirebaseController().get_notifiable_messages(self._raspberry_id)

        if not success:
            return

        self._notifiable_messages = {}
        for notifiable_message_key, notifiable_message_value in notifiable_messages.items():
            self._notifiable_messages[notifiable_message_key] = notifiable_message_value

        return self._notifiable_messages

    # def load_initial_data(self):
    #     self._load_log_messages()
    #     self._load_notifiable_messages()

    def _add_log_message(self, log_message):
        if FirebaseController().add_log_message(self._raspberry_id, log_message):
            self._log_messages.append(log_message)

            if self._notifiable_messages.get(log_message.get_level()) is True or len(self._notifiable_messages.keys()) == 0:
                BackendController().send_notification(self._raspberry_id, log_message.get_message())

    def add_auto_watering_cycle_message(self, start_time, duration, water_amount):
        self._add_log_message(AutoWateringCycleMessage(start_time, duration, water_amount))

    def add_manual_watering_cycle_message(self, start_time, duration, water_amount):
        self._add_log_message(ManualWateringCycleMessage(start_time, duration, water_amount))

    def add_moisture_measurement_message(self, moisture_level, date_time):
        self._add_log_message(MoistureMeasurementMessage(moisture_level, date_time))

    def _update_logs_on_receive_from_network(
        self,
        doc_snapshot,
        changes,
        read_time
    ):
        # print(f"Received new data from network in {read_time}")

        for change in changes:
            change_type = change.type
            changed_doc = change.document
            doc_id = changed_doc.id
            doc_data = changed_doc.to_dict()

            # print(f"Change type: {change_type}")
            # print(f"Changed doc: {changed_doc}")
            # print(f"Doc id: {doc_id}")
            # print(f"Doc data: {doc_data}")

            if "messages" in doc_data.keys():
                logs = []

                for message_key, message_value in doc_data["messages"].items():
                    logs.append(
                        LogMessage(
                            message=message_value,
                            level=MessageType.ANY,
                            timestamp=datetime.strptime(message_key[:-6], "%Y-%m-%d %H:%M:%S.%f")
                        )
                    )

                logs.sort(key=lambda x: x.get_timestamp(), reverse=True)
                self._log_messages = logs

                print(f"Log messages: {self._log_messages}")

                if self._gui_log_update_callback is not None:
                    self._gui_log_update_callback(self._log_messages)

    def _update_notifiables_on_receive_from_network(self, notifiable_message_key, notifiable_message_value):
        if notifiable_message_key in self._notifiable_messages:
            del self._notifiable_messages[notifiable_message_key]

        self._notifiable_messages[notifiable_message_key] = notifiable_message_value

        if self._gui_notifiables_update_callback is not None:
            self._gui_notifiables_update_callback(self._notifiable_messages)

    def set_gui_log_update_callback(self, _populate_list_callback):
        self._gui_log_update_callback = _populate_list_callback
