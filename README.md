# Narrator audiobook player

Free open source cross-platform audiobook player software.

![Screenshot](playing.png?raw=true "Playing screen")


## Development

To build the application for yourself you'll need to install Kivy as per their
installation instructions.

[https://kivy.org/docs/installation/installation.html](https://kivy.org/docs/installation/installation.html)


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

