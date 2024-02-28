
class RaspberryInfo:
    def __init__(self,
                 raspberryId = "",
                 raspberryName = "___",
                 raspberryLocation = "",
                 raspberryDescription = "",
                 raspberryStatus = "OFFLINE",
                 notifiableMessages = {}):
        self.raspberryId = raspberryId
        self.raspberryName = raspberryName
        self.raspberryLocation = raspberryLocation
        self.raspberryDescription = raspberryDescription
        self.raspberryStatus = raspberryStatus
        self.notifiableMessages = {}

    def __str__(self):
        return f"Id: {self.raspberryId}\n" \
               f"Name: {self.raspberryName}\n" \
               f"Location: {self.raspberryLocation}\n" \
               f"Description: {self.raspberryDescription}\n" \
               f"Status: {self.raspberryStatus}\n" \
               f"Notifiable messages: {self.notifiableMessages}"

    def get_info_dict(self):
        return {
            "name": self.raspberryName,
            "location": self.raspberryLocation,
            "description": self.raspberryDescription,
            "status": self.raspberryStatus,
            "notifiable_messages": self.notifiableMessages
        }

    def from_dict(self, info_dict):
        self.raspberryName = info_dict["name"]
        self.raspberryLocation = info_dict["location"]
        self.raspberryDescription = info_dict["description"]
        self.raspberryStatus = info_dict["status"]
        self.notifiableMessages = info_dict["notifiable_messages"]