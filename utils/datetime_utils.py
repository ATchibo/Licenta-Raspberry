import datetime
from tzlocal import get_localzone


def get_current_datetime_tz():
    return datetime.datetime.now(get_localzone())
