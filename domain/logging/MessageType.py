from enum import Enum


class MessageType(Enum):
    ANY = 0
    AUTO_WATERING_CYCLE = 1
    MANUAL_WATERING_CYCLE = 2
    MOISTURE_LEVEL_MEASUREMENT = 3
    LOW_WATER_LEVEL = 4
    EMPTY_WATER_TANK = 5
