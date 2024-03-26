from datetime import datetime


class WateringProgram:
    def __init__(self, id="", name="", frequency_days=0.0, quantity_l=0.0, starting_date_time=None, min_moisture=0.0, max_moisture=0.0):
        self.id = id
        self.name = name
        self.frequency_days = frequency_days
        self.quantity_l = quantity_l
        self.starting_date_time = starting_date_time if starting_date_time is not None else datetime.now()
        self.min_moisture = min_moisture
        self.max_moisture = max_moisture

    # def __str__(self):
    #     return f"WateringProgram(id={self.id}, name={self.name}, frequency_days={self.frequency_days}, quantity_l={self.quantity_l}, time_of_day_min={self.time_of_day_min}, min_moisture={self.min_moisture}, max_moisture={self.max_moisture})"

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return str(self)

    def getInfoDict(self):
        return {
            "id": self.id,
            "name": self.name,
            "frequencyDays": self.frequency_days,
            "quantityL": self.quantity_l,
            "startingDateTime": self.starting_date_time,
            "minMoisture": self.min_moisture,
            "maxMoisture": self.max_moisture
        }

    def fromDict(self, _dict):
        self.id = _dict["id"]
        self.name = _dict["name"]
        self.frequency_days = _dict["frequencyDays"]
        self.quantity_l = _dict["quantityL"]
        self.starting_date_time = _dict["startingDateTime"]
        self.min_moisture = _dict["minMoisture"]
        self.max_moisture = _dict["maxMoisture"]
        return self
