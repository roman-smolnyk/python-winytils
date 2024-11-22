import sys
from pathlib import Path
from time import sleep

sys.path.append(str(Path(__file__).parent.parent.absolute()))


def test_windows():
    from src.winytils.windows import Windows

    windows = Windows.filter(by_exe="explorer.exe")
    [print(w) for w in windows]


if __name__ == "__main__":
    test_windows()
