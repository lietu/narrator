import os
import time


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
