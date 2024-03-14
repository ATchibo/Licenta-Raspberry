from datetime import datetime

from domain.logging.LogMessage import LogMessage
from domain.logging.MessageType import MessageType
from utils.datetime_utils import get_current_datetime_tz


class ManualWateringCycleMessage(LogMessage):

    def __init__(self, start_time, duration, water_amount):
        _start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        _duration = round(float(duration), 2)
        _water_amount = round(float(water_amount), 2)

        message = (f"Manual watering cycle started at {_start_time} and lasted {_duration} seconds. "
                   f"Watered {_water_amount} liters.")

        super().__init__(message, MessageType.MANUAL_WATERING_CYCLE, get_current_datetime_tz())
