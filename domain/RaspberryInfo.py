
class RaspberryInfo:
    def __init__(self,
                 raspberryId = "",
                 raspberryName = "",
                 raspberryLocation = "",
                 raspberryDescription = "",
                 raspberryStatus = ""):
        self.raspberryId = raspberryId
        self.raspberryName = raspberryName
        self.raspberryLocation = raspberryLocation
        self.raspberryDescription = raspberryDescription
        self.raspberryStatus = raspberryStatus

    def __str__(self):
        return f"Name: {self.name}, IP: {self.ip}, MAC: {self.mac}, Status: {self.status}"

    def getInfoDict(self):
        return {
            "raspberryId": self.raspberryId,
            "raspberryName": self.raspberryName,
            "raspberryLocation": self.raspberryLocation,
            "raspberryDescription": self.raspberryDescription,
            "raspberryStatus": self.raspberryStatus
        }