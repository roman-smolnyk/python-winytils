import base64
import io
import sys
import time
from typing import Callable, List

import psutil
import pywintypes
import win32api
import win32con
import win32gui
import win32process

from .utils import _get_window_icon

try:
    from PIL import Image
except:
    pass


class Window:
    # This is wrapper for UWP apps
    _UWP_EXE = "ApplicationFrameHost.exe"

    def __init__(self, hwnd: int) -> None:
        self.hwnd = hwnd

    @property
    def title(self) -> str:
        return win32gui.GetWindowText(self.hwnd)

    @property
    def process(self) -> psutil.Process:
        return psutil.Process(self._process_id)

    @property
    def icon(self) -> "Image":
        if "PIL.Image" not in sys.modules:
            raise ImportError("Missing Pillow lib")
        try:
            return _get_window_icon(self.hwnd)
        except:
            return None

    @property
    def icon_base64(self) -> str:
        icon = self.icon
        if not icon:
            return None
        buffer = io.BytesIO()
        icon.save(buffer, format="PNG")
        buffer.seek(0)
        icon_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return icon_base64

    @property
    def class_name(self) -> str:
        return win32gui.GetClassName(self.hwnd)

    @property
    def children(self) -> List["Window"]:
        """Retrieve all child window handles of the current window."""
        child_windows = []

        def callback(hwnd, windows):
            windows.append(Window(hwnd))
            return True

        win32gui.EnumChildWindows(self.hwnd, callback, child_windows)
        return child_windows

    @property
    def uwp_child(self) -> "Window":
        """Skip UWP"""
        for child in self.children:
            try:
                child_thread, child_pid = win32process.GetWindowThreadProcessId(child.hwnd)
                child_process = psutil.Process(child_pid)
                # Exclude ApplicationFrameHost.exe to avoid recursion
                if child_process.name().lower() != self._UWP_EXE.lower():
                    return child
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def minimize(self, verify_timeout: float = None) -> bool:
        win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)

        if verify_timeout:
            stop_t = time.time() + 2
            while not self.is_minimized():
                if time.time() > stop_t:
                    return False
                time.sleep(0.01)
            return True
        else:
            return None

    def maximize(self, verify_timeout: float = None) -> bool:
        win32gui.ShowWindow(self.hwnd, win32con.SW_MAXIMIZE)

        if verify_timeout:
            stop_t = time.time() + 2
            while self.is_minimized():
                if time.time() > stop_t:
                    return False
                time.sleep(0.01)
            return True
        else:
            return None

    def restore(self, verify_timeout: float = None) -> bool:
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)  # SW_SHOWNORMAL

        if verify_timeout:
            stop_t = time.time() + 2
            while self.is_minimized():
                if time.time() > stop_t:
                    return False
                time.sleep(0.01)
            return True
        else:
            return None

    def activate(self):
        win32gui.SetForegroundWindow(self.hwnd)

    def is_uwp(self) -> bool:
        return self.process.name().lower() == self._UWP_EXE.lower()

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

    def is_visiable(self) -> bool:
        return win32gui.IsWindowVisible(self.hwnd) == 1

    def close(self, verify_timeout: int = None) -> bool:
        try:
            win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        except pywintypes.error as e:
            return False  # Access is denied

        if verify_timeout:
            # Optionally, wait and verify if the window has closed
            # Wait for some time
            stop_t = time.time() + 5
            while not self.is_closed():
                if time.time() > stop_t:
                    return False
                time.sleep(0.01)
            return True
        else:
            return None

    def is_closed(self) -> bool:
        if not win32gui.IsWindow(self.hwnd):
            return True
        else:
            return False

    def kill(self, verify_timeout: float = None) -> bool:
        process = self.process
        process.kill()
        if verify_timeout:
            stop_t = time.time() + verify_timeout
            while process.is_running():
                if time.time() > stop_t:
                    return False
                time.sleep(0.01)
            return True
        else:
            return None

    @property
    def _thread_id(self) -> int:
        thread_id, process_id = win32process.GetWindowThreadProcessId(self.hwnd)
        return thread_id

    @property
    def _process_id(self) -> int:
        thread_id, process_id = win32process.GetWindowThreadProcessId(self.hwnd)
        return process_id

    def __repr__(self) -> str:
        return str({"title": self.title, "exe": self.process.exe(), "class": self.class_name})


class Windows:

    def __init__(self) -> None:
        pass

    @staticmethod
    def filter(
        *,
        has_gui: bool = None,
        opened: bool = None,
        has_title: bool = None,
        by_title: str = None,
        by_exe: str = None,
        by_class_name: str = None,
        custom_filter: Callable = None,
    ) -> List[Window]:
        """
        Z axis from tompost to last
        """
        windows = Windows.get_all()
        # Filter windows that have GUI
        if has_gui == True:
            windows = [w for w in windows if w.is_visiable()]
        elif has_gui == False:
            windows = [w for w in windows if not w.is_visiable()]
        # Filter winows that are maximized(opened)
        if opened == True:
            windows = [w for w in windows if not w.is_minimized()]
        elif opened == False:
            windows = [w for w in windows if w.is_minimized()]
        # Filter windows that have title
        if has_title == True:
            windows = [w for w in windows if w.title]
        elif has_title == False:
            windows = [w for w in windows if not w.title]

        if by_title or by_exe or by_class_name:
            windows = Windows._filter_windows_by(windows, title=by_title, exe=by_exe, class_name=by_class_name)

        if callable(custom_filter):
            windows = custom_filter(windows)

        return windows

    @staticmethod
    def foregrond() -> Window:
        """"""
        # windows = Windows.filter(has_gui=has_gui, opened=opened, has_title=has_title, custom_filter=custom_filter)
        # return windows[0] if windows[:1] else None
        hwnd = win32gui.GetForegroundWindow()
        return Window(hwnd)

    @staticmethod
    def get_all() -> List[Window]:
        """Ordered starting from topmost"""
        windows = []
        for hwnd in Windows._get_hwnds():
            windows.append(Window(hwnd))
        return windows

    @staticmethod
    def _get_hwnds() -> List[int]:
        hwnds = []

        def callback(hwnd, extra):
            hwnds.append(hwnd)
            return True

        win32gui.EnumWindows(callback, None)  # None is extra
        return hwnds

    @staticmethod
    def _filter_windows_by(windows: List[Window], *, title=None, exe=None, class_name=None) -> List[Window]:
        if not (title or exe or class_name):
            raise ValueError("At least one of title, exe, or class_name must be provided")

        found_windows = []
        for w in windows:
            if title is not None and w.title != title:
                continue
            if exe is not None and w.process.name() != exe:
                continue
            if class_name is not None and w.class_name != class_name:
                continue
            found_windows.append(w)

        return found_windows


def windows_filter(windows: List[Window]) -> List[Window]:
    """
    Filters all explorer.exe opened windows(taskbar etc.) except "File Explorer" windows
    """
    filtered_windows = []
    for w in windows:
        # Skip all "explorer.exe" that are not File Explorer
        if w.process.name() == "explorer.exe" and w.class_name not in ["CabinetWClass", "ExplorerWClass"]:
            continue
        else:
            filtered_windows.append(w)
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
    child = w.uwp_child
    while not child:
        if time.time() > stop_t:
            return False
        child = w.uwp_child
    return True


def minimize_uwp(w: Window, delay: float = 0.2):
    """Minimum 0.2 sec before child minification"""
    if not w.is_uwp():
        raise Exception("It is not UWP wrapper app")

    uwp_child_win = w.uwp_child
    if not uwp_child_win:
        raise Exception("Missing UWP app child")

    w.minimize()
    time.sleep(delay)
    uwp_child_win.minimize()


def set_window_topmost(hwnd):
    """Set the specified window as topmost."""
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
    print("Window set to topmost.")


def set_window_fullscreen(hwnd):
    """Make the specified window fullscreen."""
    # Get screen dimensions
    screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
    screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)

    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

    new_style = style & ~win32con.WS_CAPTION & ~win32con.WS_THICKFRAME

    win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, new_style)

    flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
    win32gui.SetWindowPos(hwnd, None, 0, 0, 0, 0, flags)


def set_window_overrideredirect(hwnd):
    """Remove title bar, borders, taskbar icon"""
    # Get current extended window styles
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    # Modify the extended styles
    ex_style &= ~win32con.WS_EX_APPWINDOW  # Remove WS_EX_APPWINDOW
    ex_style |= win32con.WS_EX_TOOLWINDOW  # Add WS_EX_TOOLWINDOW

    # Apply the new extended styles
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    # Update the window's non-client area to reflect changes
    flags = win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
    win32gui.SetWindowPos(hwnd, None, 0, 0, 0, 0, flags)


def set_window_transparency(hwnd, transparency: int):
    """
    Set the transparency level of a window.
    :param hwnd: Handle to the window.
    :param transparency: Transparency level (0-255). 255 is fully opaque, 0 is fully transparent.
    """
    # Get the current window styles
    ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    # Add layered window style if not already set
    if not (ex_style & win32con.WS_EX_LAYERED):
        ex_style |= win32con.WS_EX_LAYERED
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)

    # ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, color_key, 0, win32con.LWA_COLORKEY)
    win32gui.SetLayeredWindowAttributes(hwnd, 0, transparency, win32con.LWA_ALPHA)


if __name__ == "__main__":
    # time.sleep(3)
    # windows = Windows.filter(has_gui=True, opened=True, has_title=True, custom_filter=windows_filter)
    windows = Windows.filter(has_gui=True)
    program_manager = Windows.filter(by_title="Program Manager", by_exe="explorer.exe")[0]
    task_switching = Windows.filter(by_title="Task Switching", by_exe="explorer.exe")[0]
    explorer_windows = Windows.filter(by_exe="explorer.exe")
    explorer_windows2 = Windows.filter(has_title=False, by_exe="explorer.exe")

    windows = Windows.filter(by_exe="explorer.exe")
    while True:
        time.sleep(0.3)
        classes = [w.class_name for w in windows]
        print(classes)
        windows = Windows.filter(by_exe="explorer.exe")

        # # print()
        # set_a = set(classes)
        # set_b = set([w.class_name for w in windows])

        # # Find unique items using set difference
        # unique_to_a = set_a - set_b  # Items in A but not in B
        # unique_to_b = set_b - set_a  # Items in B but not in A
        # print(list(unique_to_a) + list(unique_to_b))
        # print(len(windows))
        # print("\n\n")
        # popup_host = Windows.filter(by_title="PopupHost", by_exe="explorer.exe")
        popup_host = Windows.filter(by_class_name="ThumbnailDeviceHelperWnd", by_exe="explorer.exe")
        if popup_host:
            print(popup_host[0])
            popup_host[0].minimize()
            popup_host[0].close()

    windows = Windows.filter(by_exe="explorer.exe")
    while True:
        windows_new = Windows.filter(by_exe="explorer.exe")
        [print(w) for w in windows_new if w.hwnd not in [x.hwnd for x in windows]]
        windows = windows_new
        print(len(Windows.filter(by_exe="explorer.exe")))
        time.sleep(0.3)

    [print(w) for w in windows]
    w = windows[0]
    if w.is_uwp():
        cw = w.uwp_child
        cw.minimize()

    w.minimize()
    print()
