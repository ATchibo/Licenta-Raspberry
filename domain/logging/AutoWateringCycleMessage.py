from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class AutoWateringCycleMessage(LogMessage):

    def __init__(self, start_time, end_time, water_amount):
        message = (f"Auto watering cycle started at {start_time} and lasted {end_time - start_time} seconds. "
                   f"Watered {water_amount} liters.")

        super().__init__(message, MessageType.AUTO_WATERING_CYCLE)
