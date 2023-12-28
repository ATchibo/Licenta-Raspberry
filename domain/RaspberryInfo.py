
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
        return f"Id: {self.raspberryId}\n" \
               f"Name: {self.raspberryName}\n" \
               f"Location: {self.raspberryLocation}\n" \
               f"Description: {self.raspberryDescription}\n" \
               f"Status: {self.raspberryStatus}\n"

    def getInfoDict(self):
        return {
            "raspberryId": self.raspberryId,
            "raspberryName": self.raspberryName,
            "raspberryLocation": self.raspberryLocation,
            "raspberryDescription": self.raspberryDescription,
            "raspberryStatus": self.raspberryStatus
        }