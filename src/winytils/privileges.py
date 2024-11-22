import ctypes, sys
import win32api, win32con

from pathlib import Path

ROOT = Path(__file__).parent.absolute()


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def rerun_with_admin_privileges():
    # Re-run the program with admin rights
    # ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
    win32api.ShellExecute(None, "runas", sys.executable, " ".join(sys.argv), None, win32con.SW_SHOWNORMAL)


if __name__ == "__main__":
    """
    https://stackoverflow.com/questions/130763/request-uac-elevation-from-within-a-python-script
    Also note that if you converted you python script into an executable file (using tools like py2exe, cx_freeze, pyinstaller) then you should use sys.argv[1:] instead of sys.argv in the fourth parameter.
    """

    if is_admin():
        with open(ROOT / "result.txt", "w", encoding="utf-8") as f:
            f.write("admin")
    else:
        rerun_with_admin_privileges()
