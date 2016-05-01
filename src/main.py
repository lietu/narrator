import json
import os
import time
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.screenmanager import ScreenManager, Screen, \
    WipeTransition as Transition
from kivy.uix.listview import ListItemButton, ListView
from kivy.factory import Factory
from kivy.properties import ObjectProperty, NumericProperty, ListProperty
from kivy.uix.popup import Popup
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy import platform

__version__ = "0.9.0"

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "active_book": "",
    "active_file": "",
    "active_index": 0,
    "position": 0.0,
    "duration": 0.0,
    "sleep_timeout": 60.0,
    "books": {},
}


def try_int(s):
    "Convert to integer if possible."
    try:
        return int(s)
    except:
        return s


def natsort_key(s):
    "Used internally to get a tuple by which s is sorted."
    import re
    return map(try_int, re.findall(r'(\d+|\D+)', s))


def natcmp(a, b):
    "Natural string comparison, case sensitive."
    return cmp(natsort_key(a), natsort_key(b))


def natcasecmp(a, b):
    "Natural string comparison, ignores case."
    return natcmp(a.lower(), b.lower())


class BookButton(ListItemButton):
    pass


class BookList(ListView):
    pass


def get_icon(name):
    prefix = "ic_" + name + "_white_24dp"

    prefix = os.path.join("res", prefix)

    path = os.path.join(os.path.join(prefix, "web"),
                        "ic_" + name + "_white_24dp_2x.png")

    if not os.path.exists(path):
        raise AttributeError("Could not find file {}".format(
            path)
        )

    return path

    # if platform in ('windows', 'linux', 'macosx', 'unknown'):
    #     path = os.path.join(prefix, "web")
    #     return os.path.join(path, name + "_24d_x2.png")
    # elif platform == "android":
    #     path = os.path.join(os.path.join(prefix, "android"),
    #                         "drawable-xxxhdpi")
    #     return os.path.join(path, name + "_24d.png")
    # elif platform == "ios":
    #     path = os.path.join(os.path.join(prefix, "ios"),
    #                         "ic_fast_forward.imageset")
    #     return os.path.join(path, name + "_3x.png")


def seconds_to_text(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return "%d:%02d:%02d" % (hours, minutes, seconds)


class SleepTimer(object):
    def __init__(self, timeout):
        self.timeout = timeout
        self.remaining = timeout
        self.start = 0

        self.update_start()
        self.update()

    def update(self):
        self.remaining = self.timeout - (time.time() - self.start)

    def update_start(self):
        self.start = time.time()


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


class Root(ScreenManager):
    def on_touch_down(self, touch):
        app.sleep_timer.update_start()

        super(Root, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        super(Root, self).on_touch_move(touch)
        app.sleep_timer.update_start()


class PlayScreen(Screen):
    slider_value = None

    def on_touch_down(self, touch):
        app.skip_slider_updates = True
        self.slider_value = app.slider.value
        app.sleep_timer.update_start()

        super(PlayScreen, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        super(PlayScreen, self).on_touch_move(touch)
        app.sleep_timer.update_start()

        if self.slider_value != app.slider.value:
            app.skip_position_updates = True
            app.update_position(app.slider.value)

    def on_touch_up(self, touch):
        super(PlayScreen, self).on_touch_up(touch)

        # User moved the slider
        if app.slider.value != self.slider_value:
            app.seek_to_slider()

        app.skip_slider_updates = False
        app.skip_position_updates = False


class AudiobookApp(App):
    # Settings
    active_book = ObjectProperty("Animal farm")
    active_file = ObjectProperty("")
    active_index = NumericProperty(0)
    position = NumericProperty(0.0)
    duration = NumericProperty(0.0)
    books = {}
    book_list = ListProperty([])
    sleep_timeout = NumericProperty(60.0)

    # Other widget Properties
    icon_ff = ObjectProperty(get_icon("fast_forward"))
    icon_f10 = ObjectProperty(get_icon("forward_10"))
    icon_f30 = ObjectProperty(get_icon("forward_30"))
    icon_help = ObjectProperty(get_icon("help"))
    icon_library = ObjectProperty(get_icon("library_books"))
    icon_pause = ObjectProperty(get_icon("pause"))
    icon_play = ObjectProperty(get_icon("play_arrow"))
    icon_playing = ObjectProperty(get_icon("playlist_play"))
    icon_help = ObjectProperty(get_icon("help"))
    icon_search = ObjectProperty(get_icon("search"))
    icon_rr = ObjectProperty(get_icon("fast_rewind"))
    icon_r10 = ObjectProperty(get_icon("replay_10"))
    icon_r30 = ObjectProperty(get_icon("replay_30"))
    icon_settings = ObjectProperty(get_icon("settings"))
    icon_next = ObjectProperty(get_icon("skip_next"))
    icon_prev = ObjectProperty(get_icon("skip_previous"))
    icon_snooze = ObjectProperty(get_icon("snooze"))
    icon_play_pause = ObjectProperty(get_icon("play_arrow"))

    file_label = ObjectProperty("")
    sleep_text = ObjectProperty("")
    duration_text = ObjectProperty("0:00:00")
    position_text = ObjectProperty("0:00:00")

    # Runtime variables
    file_loaded = False
    slider = None
    sound = None
    playing = False
    prev_position = 0
    skip_slider_updates = False
    skip_position_updates = False
    sleep_timer = None
    popup = None

    def on_start(self):
        self.root.transition = Transition()
        self.sleep_timer = SleepTimer(self.sleep_timeout)

        self.load_settings()

        print(self.active_book)
        print(self.active_file)
        if self.active_book and self.active_file:
            path = self.books[self.active_book]["path"]
            fullpath = os.path.join(path, self.active_file)
            self.load_file(fullpath)
            self.goto("play")

        Clock.schedule_interval(self.update, 0.2)

    def find_slider(self):
        for w in self.root.walk(True):
            if w.__class__.__name__ == "Slider":
                self.slider = w

        return self.slider != None

    def goto(self, screen):
        print("Switching to screen " + screen)
        self.root.current = screen

    def on_stop(self):
        self.save_settings()

    def cancel(self):
        self.dismiss_popup()

    def dismiss_popup(self):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def show_load(self):
        content = LoadDialog(load=self.on_load, cancel=self.dismiss_popup)
        self.popup = Popup(title="Select folder", content=content,
                           size_hint=(0.9, 0.9))
        self.popup.open()

    def select_book(self, book):
        self.stop_playback()

        name = book.text
        self.active_book = name
        self.active_index = 0
        file = self.books[name]["files"][self.active_index]
        path = os.path.join(self.books[name]["path"], file)
        self.load_file(path)
        self.play()

        self.root.current = "play"

    def on_load(self, path, files):
        if path:
            app.scan_books(path)
        else:
            app.load_file(files[0])

        self.dismiss_popup()

    def update(self, _=None):
        if self.playing:
            self.position = self.sound.player.get_position()

            self.update_duration()

        self.update_sleep()

        if not self.skip_slider_updates:
            self.update_slider()

        if not self.skip_position_updates:
            self.update_position()

        self.file_label = "File {index} / {total}: {name}".format(
            index=self.active_index + 1,
            total=len(self.books[self.active_book]["files"]),
            name=self.active_file
        )

    def update_sleep(self):
        if self.playing:
            self.sleep_timer.update()

            if self.sleep_timer.remaining <= 0:
                self.pause_playback()

            self.sleep_text = "{} to sleep. Tap to reset.".format(
                self.get_timer_text()
            )
        else:
            self.sleep_text = "Playback paused. Tap play to continue.".format(
                int(self.sleep_timer.remaining)
            )

    def get_timer_text(self):
        seconds = int(round(self.sleep_timer.remaining))
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        parts = []
        if hours > 0:
            parts.append("{}h".format(hours))
        if minutes > 0:
            parts.append("{}m".format(minutes))
        parts.append("{}s".format(seconds))

        return " ".join(parts)

    def update_position(self, value=None):
        if value is None:
            value = self.position

        self.position_text = seconds_to_text(value)

    def update_slider(self):
        if not self.slider:
            if not self.find_slider():
                return

        self.slider.value = self.position
        self.prev_position = self.position

    def update_duration(self):
        self.duration = self.sound.player.get_duration()
        self.duration_text = seconds_to_text(self.duration)

    def load_settings(self):
        settings = {}
        settings.update(DEFAULT_SETTINGS)

        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)

            settings.update(data)
        except IOError:
            pass

        print("Loaded settings")

        for key in settings:
            setattr(self, key, settings[key])

        self.position_text = seconds_to_text(self.position)
        self.duration_text = seconds_to_text(self.duration)
        self.sleep_timer.timeout = self.sleep_timeout
        self.update_book_list()

    def save_settings(self):
        settings = {}
        for key in DEFAULT_SETTINGS:
            settings[key] = getattr(self, key, DEFAULT_SETTINGS[key])

        print("Saving settings...")

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, sort_keys=True,
                      indent=4, separators=(',', ': '))

    def load_file(self, path):
        self.file_loaded = False
        self.duration = -1

        print("Loaded {}".format(path))
        sound = SoundLoader.load(path)

        if sound:
            self.sound = sound
            self.sound.on_stop = self.on_sound_stop
            self.active_file = os.path.basename(path)

        self.dismiss_popup()

    def scan_books(self, path):
        for name, subdirs, files in os.walk(path):
            if subdirs:
                for file in files:
                    self.add_book_from_files(file, [file])
            else:
                self.add_book_from_files(name, files)
        self.save_settings()
        self.update_book_list()

    def add_book_from_files(self, path, files):
        name = os.path.basename(path)

        images = []
        sounds = []

        for file in files:
            _, extension = os.path.splitext(file)
            extension = extension.lower()
            if extension in (".mp3", ".wav", ".ogg", ".flac"):
                sounds.append(file)
            elif extension in (".jpg", ".png"):
                images.append(file)

        if not sounds:
            return

        book = {
            "path": path,
            "files": sounds,
            "images": images
        }

        print("{}: {} sounds, {} images".format(
            name, len(book["files"]), len(book["images"])
        ))

        self.books[name] = book

    def update_book_list(self):
        items = self.books.keys()
        items.sort(natcasecmp)
        self.book_list = items

    def seek_to_slider(self):
        self.seek(self.slider.value)

    def seek(self, position):
        self.position = position
        print("Seeking to position {}".format(position))
        self.sound.seek(position)
        self.update_position(position)

    def seek_backward(self, jump):
        pos = max(self.position - jump, 0)
        self.seek(pos)

    def seek_forward(self, jump):
        pos = min(self.position + jump, self.duration)
        self.seek(pos)

    def on_sound_stop(self):
        print("{} ended".format(self.active_file))
        self.next_file()

    def next_file(self):
        self.stop_playback()

        book = self.books[self.active_book]
        max_index = len(book["files"])
        if self.active_index + 1 >= max_index:
            self.stop_book()
            return

        self.active_index += 1
        path, file = book["path"], book["files"][self.active_index]
        fullpath = os.path.join(path, file)
        self.load_file(fullpath)
        self.play()
        self.update()

    def stop_book(self):
        self.stop_playback()

    def prev_file(self):
        if self.active_index == 0:
            self.seek(0)
            return

        self.stop_playback()

        book = self.books[self.active_book]

        self.active_index -= 1

        path, file = book["path"], book["files"][self.active_index]
        fullpath = os.path.join(path, file)

        self.load_file(fullpath)
        self.play()
        self.update()

    def stop_playback(self):
        self.playing = False
        self.icon_play_pause = self.icon_play
        print(self.icon_play_pause)
        self.position = 0

        if self.sound:
            self.sound.player.stop()

    def pause_playback(self):
        self.playing = False
        self.icon_play_pause = self.icon_play
        print(self.icon_play_pause)

        if self.sound:
            self.sound.player.pause()

    def play(self):
        if not self.sound:
            return

        self.playing = True
        self.icon_play_pause = self.icon_pause
        print(self.icon_play_pause)

        self.sound.player.play()

        if not self.file_loaded:
            self.file_loaded = True
            self.update_duration()
            self.seek(self.position)

    def pause_play(self):
        if not self.sound:
            return

        if self.playing:
            self.pause_playback()
        else:
            self.play()

    def start_debug(self):
        import pdb
        pdb.set_trace()


Factory.register('IconButton', cls=IconButton)
Factory.register('Root', cls=Root)
Factory.register('Menu', cls=Menu)
Factory.register('LoadDialog', cls=LoadDialog)
Factory.register('LibraryScreen', cls=LibraryScreen)
Factory.register('SettingsScreen', cls=SettingsScreen)
Factory.register('PlayScreen', cls=PlayScreen)
Factory.register('AboutScreen', cls=AboutScreen)
Factory.register('BookList', cls=BookList)
Factory.register('BookButton', cls=BookButton)

if __name__ == '__main__':
    app = AudiobookApp()
    app.run()
