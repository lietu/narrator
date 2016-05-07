# Narrator audiobook player

Free open source cross-platform audiobook player software.

![Screenshot](playing.png?raw=true "Playing screen")

A demo video of an early version is available at:
[https://www.youtube.com/watch?v=BaNTT4RuA90](https://www.youtube.com/watch?v=BaNTT4RuA90)


## How to use it?

Assuming you can find a binary from the [Releases](https://github.com/lietu/narrator/releases), you should start with downloading the app. If
not, you can try building one for yourself with the `Development` -instructions.

After you have the application running, you should be prompted to choose a
directory to scan for audiobooks. Pick a directory and choose `Load`.

Give the application a few moments to go through your hard drive contents and
scan for available audiobooks. Detection is based on the following rules:

1) If a directory contains subdirectories, all the files in it are considered
separate books. The name is based on the filename.

2) If we only find files inside a folder, they are all considered a part of a
book, the name is based on the directory name.

Tap on a book from the list to start listening to it.

The controls should be fairly self-explanatory, but they have keyboard bindings
for non-mobile users.

 * `Space`: Play/Pause
 * `Down arrow`: Back 30s
 * `Left arrow`: Back 10s
 * `Right arrow`: Forward 10s
 * `Up arrow`: Forward 30s
 * `Esc`: Quit


## Development

To build the application for yourself you'll need to install Kivy as per their
installation instructions.

[https://kivy.org/docs/installation/installation.html](https://kivy.org/docs/installation/installation.html)

## Debugging

Edit `src/narrator.kv` and uncomment the `Debug` -button. Run the app. Tapping
that button will launch an interactive debugger in the console.


## Builds

### Windows

You'll need [PyInstaller](http://www.pyinstaller.org)

```
cd windows
python -m PyInstaller --noconsole audiobook.spec
```

## Android (not tested)

You will need [buildozer](https://github.com/kivy/buildozer) and [Python for
Android](https://github.com/kivy/python-for-android/).pip i


```
buildozer android debug deploy run
# OR
buildozer android release deploy run
```


## Licensing

Material design icons by Google with the CC BY 4.0 license. 
https://design.google.com/icons/

The source is provided with the MIT and new BSD licenses, more details in
`LICENSE.md`.
