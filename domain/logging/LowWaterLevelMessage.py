from datetime import datetime

from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class LowWaterLevelMessage(LogMessage):

    def __init__(self, water_volume, timestamp):
        _measurement_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        message = f"At {_measurement_time} the water level was low ({water_volume}L). "

        super().__init__(message, MessageType.AUTO_WATERING_CYCLE)
