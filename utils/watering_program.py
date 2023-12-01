
class WateringProgram:
    def __init__(self, name, liters_needed, time_interval, min_moisture, max_moisture):
        self._name = name
        self._liters_needed = liters_needed
        self._time_interval = time_interval
        self._min_moisture = min_moisture
        self._max_moisture = max_moisture

    def get_name(self):
        return self._name

    def get_liters_needed(self):
        return self._liters_needed

    def get_time_interval(self):
        return self._time_interval

    def get_min_moisture(self):
        return self._min_moisture

    def get_max_moisture(self):
        return self._max_moisture

