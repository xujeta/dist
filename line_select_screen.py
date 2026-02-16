from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty

class LineSelectScreen(Screen):
    image_path = StringProperty("")

    def set_image(self, path):
        self.image_path = path
