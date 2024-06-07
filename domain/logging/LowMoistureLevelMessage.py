from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class LowMoistureLevelMessage(LogMessage):

    def __init__(self, recorded_moisture, min_moisture, timestamp):
        _measurement_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        message = f"At {_measurement_time} the recorded moisture level was {recorded_moisture}% " \
                  f"which is below the set minimum value of {min_moisture}%."

        super().__init__(message, MessageType.LOW_MOISTURE_LEVEL)
