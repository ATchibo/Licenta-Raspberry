from datetime import datetime

from utils.datetime_utils import get_current_datetime_tz


class LogMessage:
    def __init__(self, message, level, timestamp=None):
        self.message = message
        self.level = level

        if timestamp is not None:
            self.timestamp = timestamp
        else:
            self.timestamp = get_current_datetime_tz()

    def __str__(self):
        return self.message

    def from_json(self, json):
        self.message = json['message']
        self.level = json['level']
        self.timestamp = json['timestamp']

    def to_json(self):
        return {
            'message': self.message,
            'level': self.level,
            'timestamp': self.timestamp
        }

    def get_level(self):
        return self.level

    def get_message(self):
        return self.message

    def set_message(self, message):
        self.message = message

    def get_timestamp(self):
        return self.timestamp
