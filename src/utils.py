import os
import time
import inspect


builtins = (
    "float",
    "int",
    "str",
    "unicode",
    "bool",
)



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
    prefix = os.path.join(prefix, "android")
    prefix = os.path.join(prefix, "drawable-xxxhdpi")

    path = os.path.join(prefix,
                        "ic_" + name + "_white_24dp.png")

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


def describe(obj, level=0):
    def print_key(key):
        print("  " * level + " - " + key)

    skip = ("imag", "real", "numerator", "denominator", "proxy_ref")

    if isinstance(obj, dict):
        for key in obj:
            if key[:2] == "__" or key in skip:
                continue

            value = obj[key]

            if getattr(value, "__class__", None) and value.__class__.__name__ not in builtins:
                print_key(key + " -> ")

                if level <= 3:
                    describe(value, level+1)
                else:
                    print(("  " * (level + 2)) + str(value))
            elif isinstance(value, dict):
                print_key(key + ":")
                describe(value, level+1)
            else:
                print_key(key + ": " + str(value))
    else:
        for key in dir(obj):
            if key[:2] == "__" or key in skip:
                continue

            value = getattr(obj, key)
            if hasattr(value, '__call__'):
                args = "?"
                if getattr(value, "func_code", None):
                    args = ", ".join(value.func_code.co_varnames)
                print_key(key + "(" + args + ")")
            elif getattr(value, "__class__", None) and value.__class__.__name__ not in builtins:
                print_key(key + " -> ")
                if level <= 3:
                    describe(value, level+1)
                else:
                    print(("  " * (level + 2)) + str(value))
            elif isinstance(value, dict):
                print_key(key + ":")
                describe(value, level+1)
            else:
                print_key(key + ": " + str(value))


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
