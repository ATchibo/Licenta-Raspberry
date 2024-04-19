import json
import threading
from datetime import datetime

from domain.logging.LogMessage import LogMessage
from domain.logging.LowWaterLevelMessage import LowWaterLevelMessage
from domain.logging.ManualWateringCycleMessage import ManualWateringCycleMessage
from domain.logging.MessageType import MessageType
from domain.logging.MoistureMeasurementMessage import MoistureMeasurementMessage
from domain.logging.NoWaterMessage import NoWaterMessage
from domain.observer.Observer import Observer
from domain.observer.ObserverNotificationType import ObserverNotificationType
from utils.backend_controller import BackendController
from utils.firebase_controller import FirebaseController
from domain.logging.AutoWateringCycleMessage import AutoWateringCycleMessage
from utils.get_rasp_uuid import getserial
from utils.remote_requests import RemoteRequests


class EventLogger(Observer):
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

    def perform_initial_setup(self):
        RemoteRequests().add_listener_for_log_messages_changes(
            self._update_logs_on_receive_from_network
        )

        RemoteRequests().add_listener_for_notification_changes(
            self._update_notifiables_on_receive_from_network
        )

        self._load_initial_data()

    def load_log_messages(self):
        log_messages = RemoteRequests().get_log_messages()
        self._log_messages = []

        try:
            for log_message_key, log_message_value in log_messages.items():
                self._log_messages.append(
                    LogMessage(
                        message=log_message_value,
                        level=MessageType.ANY,
                        timestamp=datetime.strptime(str(log_message_key)[:-6], "%Y-%m-%d %H:%M:%S.%f")
                    )
                )

            self._log_messages.sort(key=lambda x: x.get_timestamp(), reverse=True)
        except Exception as e:
            print(f"Failed to parse log messages: {e}")

        return self._log_messages, True

    def _load_notifiable_messages(self):
        notifiable_messages, success = RemoteRequests().get_notifiable_messages()

        if not success:
            return

        self._notifiable_messages = {}
        try:
            for notifiable_message_key, notifiable_message_value in notifiable_messages.items():
                self._notifiable_messages[notifiable_message_key] = notifiable_message_value
        except Exception as e:
            print(f"Failed to parse notifiable messages: {e}")

        return self._notifiable_messages

    def _load_initial_data(self):
        self.load_log_messages()
        self._load_notifiable_messages()

    def _add_log_message(self, log_message):
        print("Adding log message: ", log_message.get_message())

        if RemoteRequests().add_log_message(log_message):
            print("Added log message: ", log_message.get_message())
            self._log_messages.append(log_message)

            if self._notifiable_messages.get(log_message.get_level().value) is True:
                print("Sending notification")
                BackendController().send_notification(self._raspberry_id, log_message.get_message())
            else:
                print(f"Dont send notification: {log_message.get_level().value}")
        else:
            print("Did not add log message")

    def add_auto_watering_cycle_message(self, start_time, duration, water_amount):
        self._add_log_message(AutoWateringCycleMessage(start_time, duration, water_amount))

    def add_manual_watering_cycle_message(self, start_time, duration, water_amount):
        self._add_log_message(ManualWateringCycleMessage(start_time, duration, water_amount))

    def add_moisture_measurement_message(self, moisture_level, date_time):
        self._add_log_message(MoistureMeasurementMessage(moisture_level, date_time))

    def add_no_water_in_tank_message(self, date_time):
        self._add_log_message(NoWaterMessage(date_time))

    def add_water_level_after_watering_message(self, level, date_time):
        self._add_log_message(LowWaterLevelMessage(level, date_time))

    def _update_logs_on_receive_from_network(
        self,
        doc_snapshot,
        changes,
        read_time
    ):
        for change in changes:
            changed_doc = change.document
            doc_data = changed_doc.to_dict()

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

                if self._gui_log_update_callback is not None:
                    self._gui_log_update_callback(self._log_messages)

    def _update_notifiables_on_receive_from_network(
        self,
        doc_snapshot,
        changes,
        read_time
    ):
        for change in changes:
            changed_doc = change.document
            doc_data = changed_doc.to_dict()

            print(f"Received new notifiable messages: {doc_data}")

            if "notifiable_messages" in doc_data.keys():
                self._notifiable_messages = doc_data["notifiable_messages"]
                print(f"New notifiable messages: {self._notifiable_messages}")

    def set_gui_log_update_callback(self, _populate_list_callback):
        self._gui_log_update_callback = _populate_list_callback

    def on_notification_from_subject(self, notification_type: ObserverNotificationType) -> None:
        if notification_type == ObserverNotificationType.FIRESTORE_CLIENT_CHANGED:
            self.perform_initial_setup()
        else:
            print(f"Unknown notification type: {notification_type}")
