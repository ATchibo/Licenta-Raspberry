from datetime import datetime

from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class HighMoistureLevelMessage(LogMessage):

    def __init__(self, recorded_moisture, max_moisture, timestamp):
        _measurement_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        message = f"At {_measurement_time} the recorded moisture level was {recorded_moisture}% " \
                  f"which is above the maximum value of {max_moisture}%."

        super().__init__(message, MessageType.HIGH_MOISTURE_LEVEL)
