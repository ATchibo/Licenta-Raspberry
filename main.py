from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget


class PlantBuddy(Widget):
    pass


class PlantBuddyApp(App):
    def build(self):
        self.load_kv("home.kv")
        # Window.size = (480, 320)
        Window.fullscreen = 'auto'
        return PlantBuddy()


if __name__ == '__main__':
    PlantBuddyApp().run()
