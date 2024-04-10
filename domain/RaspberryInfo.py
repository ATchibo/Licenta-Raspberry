from domain.logging.MessageType import MessageType


class RaspberryInfo:
    def __init__(self,
                 raspberryId = "",
                 raspberryName = "___",
                 raspberryLocation = "",
                 raspberryDescription = "",
                 notifiableMessages = {}):
        self.raspberryId = raspberryId
        self.raspberryName = raspberryName
        self.raspberryLocation = raspberryLocation
        self.raspberryDescription = raspberryDescription

        if len(notifiableMessages.keys()) == 0:
            self.notifiableMessages = {
                MessageType.AUTO_WATERING_CYCLE.value: False,
                MessageType.MANUAL_WATERING_CYCLE.value: False,
                MessageType.MOISTURE_LEVEL_MEASUREMENT.value: False,
                MessageType.LOW_WATER_LEVEL.value: False,
                MessageType.EMPTY_WATER_TANK.value: False,
            }
        else:
            self.notifiableMessages = notifiableMessages

    def __str__(self):
        return f"Id: {self.raspberryId}\n" \
               f"Name: {self.raspberryName}\n" \
               f"Location: {self.raspberryLocation}\n" \
               f"Description: {self.raspberryDescription}\n" \
               f"Notifiable messages: {self.notifiableMessages}"

    def to_dict(self):
        return {
            "id": self.raspberryId,
            "name": self.raspberryName,
            "location": self.raspberryLocation,
            "description": self.raspberryDescription,
            "notifiable_messages": self.notifiableMessages
        }

    def from_dict(self, info_dict):
        if info_dict is None:
            return self

        self.raspberryName = info_dict["name"]
        self.raspberryLocation = info_dict["location"]
        self.raspberryDescription = info_dict["description"]
        self.notifiableMessages = {}

        try:
            if type(info_dict["notifiable_messages"]) is tuple:
                for key, value in info_dict["notifiable_messages"][0].items():
                    self.notifiableMessages[key] = value
            else:
                for key, value in info_dict["notifiable_messages"].items():
                    self.notifiableMessages[key] = value
        except Exception as e:
            print(f"Failed to parse notifiable messages: {e}")

        return self

    def set_notifiable_message(self, message_type: MessageType, value):
        self.notifiableMessages[message_type.value] = value


class RaspberryInfoBuilder:
    def __init__(self):
        self.raspberry_id = ""
        self.raspberry_name = "___"
        self.raspberry_location = ""
        self.raspberry_description = ""
        self.notifiable_messages = {}

    def with_id(self, raspberry_id):
        self.raspberry_id = raspberry_id
        return self

    def with_name(self, raspberry_name):
        self.raspberry_name = raspberry_name
        return self

    def with_location(self, raspberry_location):
        self.raspberry_location = raspberry_location
        return self

    def with_description(self, raspberry_description):
        self.raspberry_description = raspberry_description
        return self

    def with_notifiable_messages(self, notifiable_messages):
        self.notifiable_messages = notifiable_messages
        return self

    def build(self):
        return RaspberryInfo(
            self.raspberry_id,
            self.raspberry_name,
            self.raspberry_location,
            self.raspberry_description,
            self.notifiable_messages
        )
