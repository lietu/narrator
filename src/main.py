import os
import json
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, \
    WipeTransition as Transition
from kivy.factory import Factory
from kivy.properties import NumericProperty, ListProperty, \
    StringProperty
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.clock import Clock
from kivy import platform
from widgets import BookButton, BookList, IconButton, \
    LoadDialog, Menu
from time import time
from utils import get_icon, natcasecmp, seconds_to_text, SleepTimer, describe

__version__ = "0.9.1"

SETTINGS_FILE = "settings.json"

DEFAULT_SETTINGS = {
    "active_book": "",
    "active_file": "",
    "active_index": 0,
    "position": 0.0,
    "duration": 0.0,
    "sleep_timeout": 60.0 * 30,
    "books": {},
}


class Root(ScreenManager):
    def on_touch_down(self, touch):
        app.sleep_timer.update_start()

        super(Root, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        super(Root, self).on_touch_move(touch)
        app.sleep_timer.update_start()


class LibraryScreen(Screen):
    pass


class PlayScreen(Screen):
    slider_value = None

    def on_touch_down(self, touch):
        app.skip_slider_updates = True
        self.slider_value = app._position_slider.value
        app.sleep_timer.update_start()

        super(PlayScreen, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        super(PlayScreen, self).on_touch_move(touch)
        app.sleep_timer.update_start()

        if self.slider_value != app._position_slider.value:
            app.skip_position_updates = True
            app.update_position(app._position_slider.value)

    def on_touch_up(self, touch):
        super(PlayScreen, self).on_touch_up(touch)

        # User moved the slider
        if app._position_slider.value != self.slider_value:
            app.seek_to_slider()

        app.skip_slider_updates = False
        app.skip_position_updates = False


class SettingsScreen(Screen):
    pass


class AboutScreen(Screen):
    pass


class NarratorApp(App):
    title = StringProperty("Narrator audiobook player")

    # Settings
    active_book = StringProperty("Animal farm")
    active_file = StringProperty("")
    active_index = NumericProperty(0)
    position = NumericProperty(0.0)
    duration = NumericProperty(0.0)
    books = {}
    book_list = ListProperty()
    sleep_timeout = NumericProperty(0.0)

    # Other widget Properties
    icon_ff = StringProperty(get_icon("fast_forward"))
    icon_f10 = StringProperty(get_icon("forward_10"))
    icon_f30 = StringProperty(get_icon("forward_30"))
    icon_help = StringProperty(get_icon("help"))
    icon_library = StringProperty(get_icon("library_books"))
    icon_pause = StringProperty(get_icon("pause"))
    icon_play = StringProperty(get_icon("play_arrow"))
    icon_playing = StringProperty(get_icon("playlist_play"))
    icon_search = StringProperty(get_icon("search"))
    icon_rr = StringProperty(get_icon("fast_rewind"))
    icon_r10 = StringProperty(get_icon("replay_10"))
    icon_r30 = StringProperty(get_icon("replay_30"))
    icon_settings = StringProperty(get_icon("settings"))
    icon_next = StringProperty(get_icon("skip_next"))
    icon_prev = StringProperty(get_icon("skip_previous"))
    icon_snooze = StringProperty(get_icon("snooze"))
    icon_play_pause = StringProperty(get_icon("play_arrow"))

    sleep_timer_setting_text = StringProperty("")
    sleep_timer_minutes = NumericProperty(0.0)
    file_label = StringProperty("")
    sleep_text = StringProperty("")
    duration_text = StringProperty("0:00:00")
    position_text = StringProperty("0:00:00")

    x, y = 0, 0

    # Runtime variables
    skip_slider_updates = False
    skip_position_updates = False
    sleep_timer = None
    _file_loaded = False
    _position_slider = None
    _sound = None
    _playing = False
    _popup = None
    _keyboard = None
    _paused_at = None
    _stopping = False
    _autosave_at = None

    def on_start(self):
        print("Narrator starting up.")

        self.load_elements()
        self.setup_event_listeners()

        self.root.transition = Transition()
        self.sleep_timer = SleepTimer(self.sleep_timeout)

        self.load_settings()

        if self.active_book and self.active_file:
            path = self.books[self.active_book]["path"]
            fullpath = os.path.join(path, self.active_file)
            self.load_file(fullpath)
            self.goto("play")
        elif not self.books:
            self.goto("library")
            self.show_load()

        Clock.schedule_interval(self.update, 0.2)

    def load_elements(self):

        play = self.root.ids.play
        self._position_slider = play.ids.position

    def setup_event_listeners(self):
        settings = self.root.ids.settings
        sleep_timer_slider = settings.ids.sleep_timer_slider
        sleep_timer_slider.bind(value=self.on_sleep_timer_minutes_changed)

    def clear_library(self):
        self.stop_playback()
        self.active_book = ""
        self.active_file = ""
        self.active_index = 0
        self.books = {}
        self._sound = None
        self.update_book_list()
        self.update_playing()

    def on_pause(self):
        print("Narrator pausing.")
        self.save_settings()

    def _request_keyboard(self):
        print("Requesting keyboard.")
        self._keyboard = Window.request_keyboard(
            self._keyboard_closed,
            self
        )
        self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        print("Keyboard was closed.")
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        """
        Triggered every time you press a key on the keyboard. Resets sleep
        timer and triggers some controls.
        :param keyboard:
        :param keycode:
        :param text:
        :param modifiers:
        :return:
        """

        code, key = keycode

        # Toggle pause/play when user presses space
        if text == " ":
            self.pause_play()

        # Jump forward/back with arrows
        if key == "down":
            self.seek_backward(30)
        if key == "left":
            self.seek_backward(10)
        if key == "right":
            self.seek_forward(10)
        if key == "up":
            self.seek_forward(30)

        self.sleep_timer.update_start()

    def on_mouse_pos(self, *args):
        """
        Triggered every time there's a mouse event. Resets sleep timer if you
        touch the mouse.
        :param args:
        :return:
        """
        self.sleep_timer.update_start()

    def goto(self, screen):
        print("Switching to screen " + screen)
        self.root.current = screen

    def on_stop(self):
        print("Narrator stopping.")
        self.save_settings()

    def cancel(self):
        print("Cancel clicked")
        self.dismiss_popup()

    def dismiss_popup(self):
        if self._popup:
            print("Closing scan popup")
            self._popup.dismiss()
            self._popup = None

    def show_load(self):
        content = LoadDialog(load=self.on_load, cancel=self.dismiss_popup)
        self._popup = Popup(title="Select folder to scan", content=content,
                            size_hint=(0.9, 0.9))
        self._popup.open()

    def select_book(self, book):
        print("Selected book " + book.text)
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
        if self._playing:
            self.update_playing()

        self.update_sleep()

        if not self.skip_slider_updates:
            self.update_slider()

        if not self.skip_position_updates:
            self.update_position()

        if str(platform) in ('win', 'linux', 'macosx',):
            if not self._keyboard:
                self._request_keyboard()

            Window.bind(mouse_pos=self.on_mouse_pos)

        if self._autosave_at is not None:
            if self._autosave_at <= time():
                print("Autosaving settings")
                self.save_settings()
                self._autosave_at = None

    def update_playing(self):
        self.position = self._get_pos()
        self.update_duration()

        if self.active_book:
            self.file_label = "File {index} / {total}: {name}".format(
                index=self.active_index + 1,
                total=len(self.books[self.active_book]["files"]),
                name=self.active_file
            )
        else:
            self.file_label = "No file loaded."

    def update_sleep(self):
        if self._playing:
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
        self._position_slider.value = self.position

    def update_duration(self):
        self.duration = self._get_duration()
        self.duration_text = seconds_to_text(self.duration)

    def load_settings(self):
        print("Loading settings")

        settings = {}
        settings.update(DEFAULT_SETTINGS)

        try:
            with open(SETTINGS_FILE) as f:
                data = json.load(f)

            settings.update(data)
        except IOError:
            pass

        for key in settings:
            setattr(self, key, settings[key])

        self.position_text = seconds_to_text(self.position)
        self.duration_text = seconds_to_text(self.duration)
        self.sleep_timer.timeout = self.sleep_timeout
        self.update_book_list()
        self.sleep_timer_minutes = self.sleep_timeout / 60.0

    def save_settings(self):
        print("Saving settings")
        settings = {}
        for key in DEFAULT_SETTINGS:
            settings[key] = getattr(self, key, DEFAULT_SETTINGS[key])

        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, sort_keys=True,
                      indent=4, separators=(',', ': '))

    def load_file(self, path):
        print("Loading sound file " + path)
        self._file_loaded = False
        self.duration = -1

        sound = SoundLoader.load(path)

        if sound:
            self._sound = sound
            self._sound.on_stop = self.on_sound_stop
            self.active_file = os.path.basename(path)

        # describe(sound)

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
        print("Scan completed, now have {} books".format(
            len(self.book_list)
        ))

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

        self.books[name] = book

    def update_book_list(self):
        items = self.books.keys()
        items.sort(natcasecmp)
        self.book_list = items

    def seek_to_slider(self):
        self._seek(self._position_slider.value)

    def seek_backward(self, jump):
        pos = max(self.position - jump, 0)
        self._seek(pos)

    def seek_forward(self, jump):
        pos = min(self.position + jump, self.duration)
        self._seek(pos)

    def on_sound_stop(self):
        if self._stopping:
            return

        print("File ended")
        self.next_file()

    def next_file(self):
        print("Going to next file")
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
        print("Stopping the book")
        self.stop_playback()

    def prev_file(self):
        print("Loading previous file")
        if self.active_index == 0:
            self._seek(0)
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
        print("Stopping playback")
        self._playing = False
        self.icon_play_pause = self.icon_play
        self.position = 0

        if self._sound:
            self._stop()

    def pause_playback(self):
        print("Pausing playback")
        self._playing = False
        self.icon_play_pause = self.icon_play

        if self._sound:
            self._pause()

    def play(self):
        if not self._sound:
            return

        print("Playing sound file")

        self._playing = True
        self.icon_play_pause = self.icon_pause

        self._play()

        if not self._file_loaded:
            self._file_loaded = True
            self.update_duration()
            self._seek(self.position)

        if self._paused_at:
            print("Continuing from {}".format(self._paused_at))
            self._seek(self._paused_at)
            self._paused_at = None

    def pause_play(self):
        if not self._sound:
            return

        if self._playing:
            self.pause_playback()
        else:
            self.play()

    def on_sleep_timer_minutes_changed(self, _, value):
        self.sleep_timer_minutes = value
        self.sleep_timeout = value * 60.0
        self.sleep_timer.timeout = self.sleep_timeout
        self.sleep_timer_setting_text = "Sleep after {} minutes".format(
            int(self.sleep_timer_minutes)
        )

        # Autosave in 5 seconds if no more changes are made
        self._autosave_at = time() + 5.0

    def start_debug(self):
        import pdb
        pdb.set_trace()

    def to_window(self, x, y):
        return x, y

    # Functions that take care of abstracting various platform
    # differences.

    def _seek(self, position):
        print("Seeking to {}".format(position))
        self.position = position
        self._sound.seek(position)
        self.update_position(position)

    def _stop(self):
        # Stupid events getting triggered by stop
        if self._stopping:
            return

        self._stopping = True

        if getattr(self._sound, "stop", None):
            self._sound.stop()
        else:
            self._sound.player.stop()

        self._stopping = False

    def _pause(self):
        if getattr(self._sound, "player", None):
            self._sound.player.pause()
        else:
            self._paused_at = self._get_pos()
            print("Paused at {}".format(self._paused_at))
            self._stop()

    def _play(self):
        if getattr(self._sound, "play", None):
            self._sound.play()
        else:
            self._sound.player.play()

    def _get_pos(self):
        if not self._sound:
            return 0

        if getattr(self._sound, "get_pos", None):
            return self._sound.get_pos()
        else:
            return self._sound.player.get_position()

    def _get_duration(self):
        if not self._sound:
            return 0

        if getattr(self._sound, "length", None) is not None:
            return self._sound.length
        elif getattr(self._sound, "_data", None):
            return self._sound._data.get_length()
        else:
            return self._sound.player.get_duration()


if __name__ == '__main__':
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

    app = NarratorApp()
    app.run()
