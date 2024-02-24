
class LogMessage:
    def __init__(self, message, level):
        self.message = message
        self.level = level

    def __str__(self):
        return self.message

    def from_json(self, json):
        self.message = json['message']
        self.level = json['level']

    def to_json(self):
        return {
            'message': self.message,
            'level': self.level
        }

    def get_level(self):
        return self.level

    def get_message(self):
        return self.message

    def set_message(self, message):
        self.message = message
