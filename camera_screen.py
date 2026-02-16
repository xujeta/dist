from kivy.uix.screenmanager import Screen

class CameraScreen(Screen):
    def open_gallery(self):
        print("Галерея пока заглушка")

    def go_next(self):
        self.manager.parent.go_next("line")
