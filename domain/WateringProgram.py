class WateringProgram:
    def __init__(self, id="", name="", frequency_days=0.0, quantity_l=0.0, time_of_day_min=0, min_moisture=0.0, max_moisture=0.0):
        self.id = id
        self.name = name
        self.frequency_days = frequency_days
        self.quantity_l = quantity_l
        self.time_of_day_min = time_of_day_min
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
            "timeOfDayMin": self.time_of_day_min,
            "minMoisture": self.min_moisture,
            "maxMoisture": self.max_moisture
        }

    def fromDict(self, dict):
        self.id = dict["id"]
        self.name = dict["name"]
        self.frequency_days = dict["frequencyDays"]
        self.quantity_l = dict["quantityL"]
        self.time_of_day_min = dict["timeOfDayMin"]
        self.min_moisture = dict["minMoisture"]
        self.max_moisture = dict["maxMoisture"]
        return self