from kivy.app import App
from kivy.uix.widget import Widget


class PlantBuddy(Widget):
    pass


class PlantBuddyApp(App):
    def build(self):
        self.load_kv("home.kv")
        return PlantBuddy()


if __name__ == '__main__':
    PlantBuddyApp().run()
