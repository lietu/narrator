from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.listview import ListItemButton, ListView
from kivy.uix.screenmanager import Screen
from kivy.properties import ObjectProperty


class BookButton(ListItemButton):
    pass


class BookList(ListView):
    pass


class Menu(BoxLayout):
    pass


class IconButton(ButtonBehavior, Image):
    pass


class SettingsScreen(Screen):
    pass


class LibraryScreen(Screen):
    pass


class AboutScreen(Screen):
    pass


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
