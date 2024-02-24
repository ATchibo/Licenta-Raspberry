from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class MoistureMeasurementMessage(LogMessage):

    def __init__(self, moisture_level, date_time):
        message = f"Moisture level is {moisture_level}% - recorded at {date_time}"
        super().__init__(message, MessageType.MOISTURE_LEVEL_MEASUREMENT)
