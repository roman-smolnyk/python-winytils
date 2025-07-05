import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from src.winytils.windows import Window, Windows
from src.winytils.workstation import Workstation
from src.winytils.win11toast import toast


def test_windows():
    windows = Windows.filter(by_exe="explorer.exe")
    [print(w) for w in windows]


def test2():
    time.sleep(3)
    window = Windows.foregrond()

    if window:
        if window.is_uwp():
            child = window.uwp_child
            if child:
                window = child
        print(window)
        window.icon.save("icon.png")


def test3():
    workstation = Workstation()
    workstation.lock()
    time.sleep(5)
    print(workstation.is_locked())


def test4():
    toast("Hello Python🐍")


if __name__ == "__main__":
    test3()
