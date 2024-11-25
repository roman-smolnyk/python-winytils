import sys
from pathlib import Path
from time import sleep

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from src.winytils.windows import Window, Windows


def test_windows():
    windows = Windows.filter(by_exe="explorer.exe")
    [print(w) for w in windows]


def test2():
    sleep(3)
    window = Windows.foregrond()

    if window:
        if window.is_uwp():
            child = window.uwp_child
            if child:
                window = child
        print(window)
        window.icon.save("icon.png")


if __name__ == "__main__":
    test2()
