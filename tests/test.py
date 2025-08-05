import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from winytils import guiwin
from src.winytils.workstation import Workstation
from src.winytils.win11toast import toast


def test_windows():
    windows = guiwin.filter_windows_by(guiwin.get_all_windows(), exe_name="explorer.exe")
    [print(w) for w in windows]


def test2():
    time.sleep(3)
    window = guiwin.get_foreground_window()

    if window:
        if window.is_uwp():
            child = window.get_uwp_window()
            if child:
                window = child
        print(window)
        window.get_icon().save("icon.png")


def test3():
    workstation = Workstation()
    workstation.start_monitor()
    workstation.lock()
    time.sleep(5)
    print(workstation.is_locked())


def test4():
    toast("Hello Python🐍")


if __name__ == "__main__":
    test4()
