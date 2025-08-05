import base64
import io
import sys
import time
from typing import Callable, List, Union

import psutil
import pywintypes
import win32api
import win32con
import win32gui
import win32process

from .utils import get_window_icon

try:
    from PIL import Image
except:
    pass


class Window:
    # This is wrapper for UWP apps
    _UWP_EXE = "ApplicationFrameHost.exe"

    def __init__(self, hwnd: int) -> None:
        self.hwnd = hwnd

    def exists(self) -> bool:
        if not win32gui.IsWindow(self.hwnd):
            return True
        else:
            return False

    def get_title(self) -> str:
        return win32gui.GetWindowText(self.hwnd)

    def get_thread_id(self) -> int:
        thread_id, process_id = win32process.GetWindowThreadProcessId(self.hwnd)
        return thread_id

    def get_process_id(self) -> int:
        thread_id, process_id = win32process.GetWindowThreadProcessId(self.hwnd)
        return process_id

    def get_process(self) -> psutil.Process:
        return psutil.Process(self._process_id)

    def get_icon(self, base64=False) -> "Image":
        if "PIL.Image" not in sys.modules:
            raise ImportError("Missing Pillow lib")
        try:
            return get_window_icon(self.hwnd)
        except:
            return None

    def get_class_name(self) -> str:
        return win32gui.GetClassName(self.hwnd)

    def get_children(self) -> List["Window"]:
        children_windows = []

        def callback(hwnd, windows):
            windows.append(Window(hwnd))
            return True

        win32gui.EnumChildWindows(self.hwnd, callback, children_windows)
        return children_windows

    def is_uwp(self) -> bool:
        """Check if this is UWP wrapper process(window)"""
        try:
            return self.get_process().name() == self._UWP_EXE
        except:
            return False

    def get_uwp_window(self) -> "Window":
        """Get real app window (wrapped into uwp) to gain access to the real app process"""
        for child in self.get_children():
            try:
                child_process = psutil.Process(child.get_process_id())
                # Exclude ApplicationFrameHost.exe to avoid recursion
                if child_process.name() != self._UWP_EXE:
                    return child
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def minimize(self):
        win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)

    def maximize(self) -> bool:
        win32gui.ShowWindow(self.hwnd, win32con.SW_MAXIMIZE)

    def restore(self) -> bool:
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

    def close(self):
        try:
            win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        except pywintypes.error as e:
            return False  # Access is denied

    def set_foreground(self):
        win32gui.SetForegroundWindow(self.hwnd)

    def is_minimized(self) -> bool:
        # # SW_SHOWMINIMIZED (2) indicates the window is minimized.
        # placement = win32gui.GetWindowPlacement(self.hwnd) (2, 2, (-25600, -25600), (-1, -1), (40, 0, 1078, 808))
        # return placement[1] == win32con.SW_SHOWMINIMIZED
        return bool(win32gui.IsIconic(self.hwnd))

    def is_maximized(self) -> bool:
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWMAXIMIZED

    def is_normal(self) -> bool:
        placement = win32gui.GetWindowPlacement(self.hwnd)
        return placement[1] == win32con.SW_SHOWNORMAL

    def is_visible(self) -> bool:
        return win32gui.IsWindowVisible(self.hwnd) == 1

    def is_truly_visible(self) -> bool:
        """Checks also if windows size is not 0 and it is on screen"""
        if not self.is_visible():
            return False

        left, top, right, bottom = win32gui.GetWindowRect(self.hwnd)

        # Check windows size
        width = right - left
        height = bottom - top
        if width <= 0 or height <= 0:
            return False

        # Check if window is on-screen
        if right < 0 or bottom < 0:
            return False

        return True

    def set_window_topmost(self):
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

    def set_window_fullscreen(self):
        # screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        # screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)

        new_style = style & ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME

        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, new_style)

        flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
        win32gui.SetWindowPos(self.hwnd, None, 0, 0, 0, 0, flags)

    def set_window_overrideredirect(self):
        """Remove title bar, borders, taskbar icon"""
        # Get current extended window styles
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        # Modify the extended styles
        ex_style &= ~win32con.WS_EX_APPWINDOW  # Remove WS_EX_APPWINDOW
        ex_style |= win32con.WS_EX_TOOLWINDOW  # Add WS_EX_TOOLWINDOW

        # Apply the new extended styles
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

        # Update the window's non-client area to reflect changes
        flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
        win32gui.SetWindowPos(self.hwnd, None, 0, 0, 0, 0, flags)

    def set_window_transparency(self, transparency: int):
        """
        Set the transparency level of a window.
        :param hwnd: Handle to the window.
        :param transparency: Transparency level (0-255). 255 is fully opaque, 0 is fully transparent.
        """
        # Get the current window styles
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)

        # Add layered window style if not already set
        if not (ex_style & win32con.WS_EX_LAYERED):
            ex_style |= win32con.WS_EX_LAYERED
            win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style)

        # ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, color_key, 0, win32con.LWA_COLORKEY)
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, transparency, win32con.LWA_ALPHA)

    def __repr__(self) -> str:
        exe = ""
        try:
            exe = self.get_process().exe()
        except Exception as e:
            exe = e
        return str({"title": self.get_title(), "exe": exe, "class": self.get_class_name()})


def _get_hwnds() -> List[int]:
    hwnds = []

    def callback(hwnd, extra):
        hwnds.append(hwnd)
        return True

    win32gui.EnumWindows(callback, None)  # None is extra
    return hwnds


def get_all_windows() -> List[Window]:
    """Ordered starting from topmost"""
    windows = []
    for hwnd in _get_hwnds():
        windows.append(Window(hwnd))
    return windows


def get_foreground_window() -> Window:
    """It's not always that you may expect due to a lot of different circumstances"""
    hwnd = win32gui.GetForegroundWindow()
    return Window(hwnd)


def get_windows_by_title(title: str, includes=False) -> List[Window]:
    windows = []
    for window in get_all_windows():
        if includes and title.lower() in window.get_title().lower():
            windows.append(window)
        elif window.get_title() == title:
            windows.append(window)
    return windows


def get_window_by_pid(pid: int) -> Window:
    for window in get_all_windows():
        if window.get_process_id() == pid:
            return window


def get_windows_by_exe_name(exe_name: str) -> List[Window]:
    windows = []
    for window in get_all_windows():
        try:
            if window.get_process().name() == exe_name:
                windows.append(window)
        except:
            continue
    return windows


def get_windows_by_class_name(class_name: str) -> List[Window]:
    windows = []
    for window in get_all_windows():
        if window.get_class_name() == class_name:
            windows.append(window)
    return windows


def get_windows_with_opened_gui(self) -> List[Window]:
    windows = []
    for window in get_all_windows():
        if not window.exists():
            continue
        if window.is_minimized():
            continue
        if not window.is_truly_visible():
            continue
        if not window.get_title():
            continue
        windows.append(window)
    return windows


def filter_windows_by(windows: List[Window], *, title=None, exe_name=None, class_name=None) -> List[Window]:
    if not (title or exe_name or class_name):
        raise ValueError("At least one of title, exe_name, or class_name must be provided")

    filtered_windows = []
    for window in windows:
        try:
            if exe_name and window.get_process().name() == exe_name:
                filtered_windows.append(window)
        except:
            pass

        if title and window.get_title() == title:
            filtered_windows.append(window)

        if class_name and window.get_class_name() == class_name:
            filtered_windows.append(window)

    return filtered_windows


def filter_non_explorer_windows(windows: List[Window]) -> List[Window]:
    """
    Removes all system explorer.exe windows(taskbar etc.) except "File Explorer" app windows itself
    """
    filtered_windows = []
    for w in windows:
        try:
            if w.get_process().name() == "explorer.exe" and w.get_class_name() not in [
                "CabinetWClass",
                "ExplorerWClass",
            ]:
                continue
            else:
                filtered_windows.append(w)
        except:
            pass
    return filtered_windows


def is_uwp_loaded(w: Window, timeout: float = 5) -> bool:
    """
    Can return False in case if application with no gui is opened so there will be no child [SystemSettings.exe example case]
    In this case it is recommended to do w.minimize() and skip step. So this window should not appear again
    timeout: Timeout to wait for load after that return False. Defaults to 5 sec
    """
    if not w.is_uwp():
        raise Exception("It is not UWP wrapper app")
    stop_t = time.time() + timeout
    child = w.get_uwp_window()
    while not child:
        if time.time() > stop_t:
            return False
        child = w.get_uwp_window()
    return True


def minimize_uwp_window(w: Window, delay: float = 0.2):
    """Minimum 0.2 sec before child minification"""
    if not w.is_uwp():
        raise Exception("It is not UWP wrapper app")

    uwp_win = w.get_uwp_window()
    if not uwp_win:
        raise Exception("Missing UWP app child")

    w.minimize()
    time.sleep(delay)
    uwp_win.minimize()

