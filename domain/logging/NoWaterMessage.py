from datetime import datetime

from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class NoWaterMessage(LogMessage):

    def __init__(self, timestamp):
        _measurement_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        message = f"At {_measurement_time} the water tank was empty so no watering occurred."

        super().__init__(message, MessageType.AUTO_WATERING_CYCLE)
