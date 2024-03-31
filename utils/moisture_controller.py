from gpiozero import MCP3008

from utils.local_storage_controller import LocalStorageController

class MoistureController:
    def __init__(self, channel):
        self.sensor = MCP3008(channel=channel)

        # the absolute values for dry and wet recorded from the sensor
        self.absolute_dry = 0.7498778700537372
        self.absolute_wet = 0.3082559843673669

        _absolute_dry, _absolute_wet = LocalStorageController().get_moisture_sensor_absolute_values()
        if _absolute_dry is not None and _absolute_wet is not None:
            self.absolute_dry = _absolute_dry
            self.absolute_wet = _absolute_wet
        else:
            LocalStorageController().set_moisture_sensor_absolute_values(self.absolute_dry, self.absolute_wet)

        self.interval = self.absolute_dry - self.absolute_wet

    def get_moisture(self):
        # pass
        return self.sensor.value

    def get_moisture_percentage(self):
        # pass
        perc = round(1 - (self.get_moisture() - self.absolute_wet) / self.interval, 2) * 100
        if perc < 0.0:
            return 0.0
        if perc > 100.0:
            return 100.0
        return perc

    def update_absolute_values(self, dry, wet):
        self.absolute_dry = dry
        self.absolute_wet = wet
        self.interval = self.absolute_dry - self.absolute_wet
        LocalStorageController().set_moisture_sensor_absolute_values(self.absolute_dry, self.absolute_wet)
