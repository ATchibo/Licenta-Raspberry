from datetime import datetime

from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType


class AutoWateringCycleMessage(LogMessage):

    def __init__(self, start_time, duration, water_amount):
        _start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        _duration = round(float(duration), 2)
        _water_amount = round(float(water_amount), 2)

        message = (f"Automatic watering cycle started at {_start_time} and lasted {_duration} seconds. "
                   f"Watered {_water_amount} liters.")

        super().__init__(message, MessageType.AUTO_WATERING_CYCLE)
