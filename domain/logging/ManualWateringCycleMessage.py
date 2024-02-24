from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class ManualWateringCycleMessage(LogMessage):

    def __init__(self, start_time, end_time, water_amount):
        message = (f"Manual watering cycle started at {start_time} and lasted {end_time - start_time} seconds. "
                   f"Watered {water_amount} liters.")

        super().__init__(message, MessageType.MANUAL_WATERING_CYCLE)
