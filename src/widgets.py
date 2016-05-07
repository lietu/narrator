from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.listview import ListItemButton, ListView
from kivy.properties import ObjectProperty


class BookButton(ListItemButton):
    pass


class BookList(ListView):
    pass


class Menu(BoxLayout):
    pass


class IconButton(ButtonBehavior, Image):
    pass


class LoadDialog(FloatLayout):
    load = ObjectProperty(None)
    cancel = ObjectProperty(None)
