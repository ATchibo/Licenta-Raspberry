from google.protobuf.internal.well_known_types import Timestamp


class MoistureInfo:
    def __init__(self, raspberry_id="", measurement_value_percent=0.0, measurement_time=None):
        self.raspberry_id = raspberry_id
        self.measurement_value_percent = measurement_value_percent
        self.measurement_time = measurement_time or Timestamp()

    def to_dict(self):
        return {
            'raspberryId': self.raspberry_id,
            'measurementValuePercent': self.measurement_value_percent,
            'measurementTime': self.measurement_time,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            raspberry_id=data.get('raspberryId', ""),
            measurement_value_percent=data.get('measurementValuePercent', 0.0),
            measurement_time=data.get('measurementTime', Timestamp())
        )