from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_datetime():
    return datetime.now(ZoneInfo("Europe/Bucharest"))
