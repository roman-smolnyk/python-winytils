import threading
import time
import inspect
from collections import defaultdict
from typing import Callable, Dict, List
from dataclasses import dataclass, astuple

import pythoncom
import win32api
import win32con
import win32gui
import win32ts


def _get_const(num: int):
    const = []
    win32con_dict = {}
    for constant_name in dir(win32con):
        if not constant_name.startswith("__"):  # Exclude built-in attributes
            win32con_dict[constant_name] = getattr(win32con, constant_name)
    for key, value in win32con_dict.items():
        if value == num:
            const.append(key)
    return const


# ! Type hints are required for dataclass fields
@dataclass(frozen=True, eq=True)
class Event:
    msg: int | None = 0
    wparam: int | None = 0
    lparam: int | None = 0


@dataclass(frozen=True, eq=True)
class AnyEvent(Event):
    msg: int | None = None
    wparam: int | None = None
    lparam: int | None = None


@dataclass(frozen=True, eq=True)
class LockEvent(Event):
    # * Screen locked
    # https://www.pinvoke.net/default.aspx/wtsapi32.wtsregistersessionnotification
    msg: int | None = 0x2B1  # WM_WTSSESSION_CHANGE
    wparam: int | None = 0x7  # WTS_SESSION_LOCK
    lparam: int | None = None  # Session identifier


@dataclass(frozen=True, eq=True)
class UnlockEvent(Event):
    # * Screen unlocked
    # https://www.pinvoke.net/default.aspx/wtsapi32.wtsregistersessionnotification
    msg: int | None = 0x2B1  # WM_WTSSESSION_CHANGE
    wparam: int | None = 0x8  # WTS_SESSION_UNLOCK
    lparam: int | None = None  # Session identifier


@dataclass(frozen=True, eq=True)
class DeviceChangeEvent(Event):
    # * USB plugged in/out
    # https://learn.microsoft.com/en-us/windows/win32/devio/wm-devicechange
    msg: int | None = 0x219  # WM_DEVICECHANGE
    wparam: int | None = 0x0007  # DBT_DEVNODES_CHANGED
    lparam: int | None = None


@dataclass(frozen=True, eq=True)
class PowerStatusChangedEvent(Event):
    # * AC/Battery
    # https://www.pinvoke.net/default.aspx/user32/RegisterPowerSettingNotification.html
    msg: int | None = win32con.WM_POWERBROADCAST
    wparam: int | None = win32con.PBT_APMPOWERSTATUSCHANGE
    lparam: int | None = None


class WorkstationEventsListener(threading.Thread):
    """Monitors workstation session events and invokes registered handlers."""

    def __init__(self):
        super().__init__(daemon=True)
        self.event_handlers: Dict[Event, List[Callable]] = defaultdict(list)
        self._window_handle = False

    def run(self):
        pythoncom.CoInitialize()

        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = f"WorkstationEventsListener_{id(self)}"  # Can be any
        wc.lpfnWndProc = self._window_procedure  # This is the window procedure

        # Create invisiable window
        self._window_handle = win32gui.CreateWindow(
            win32gui.RegisterClass(wc),  # Window class
            "WorkstationEventsListener",  # Window title, can be any
            0,  # Style
            0,  # x-coordinate
            0,  # y-coordinate
            win32con.CW_USEDEFAULT,  # Width
            win32con.CW_USEDEFAULT,  # Height
            0,  # Parent window (None, as 0)
            0,  # Menu (None, as 0)
            wc.hInstance,  # Instance handle
            None,  # Additional parameter (None here)
        )

        # Update the window
        win32gui.UpdateWindow(self._window_handle)

        # Register session notifications
        # win32ts.NOTIFY_FOR_THIS_SESSION
        win32ts.WTSRegisterSessionNotification(self._window_handle, win32ts.NOTIFY_FOR_ALL_SESSIONS)

        try:
            win32gui.PumpMessages()
        finally:
            pythoncom.CoUninitialize()

    def stop(self):
        """Stop the listener."""
        win32gui.PostMessage(self._window_handle, win32con.WM_CLOSE, 0, 0)

    def _window_procedure(self, hwnd: int, msg: int, wparam, lparam):
        """Processes window messages and invokes handlers."""
        for handler in self.event_handlers[astuple(Event(msg, wparam, lparam))]:
            handler(Event(msg, wparam, lparam))
        for handler in self.event_handlers[astuple(Event(msg, wparam, None))]:
            handler(Event(msg, wparam, lparam))
        for handler in self.event_handlers[astuple(Event(msg, None, None))]:
            handler(Event(msg, wparam, lparam))
        for handler in self.event_handlers[astuple(AnyEvent())]:
            handler(Event(msg, wparam, lparam))

        if msg in [win32con.WM_CLOSE, win32con.WM_DESTROY]:
            win32gui.PostQuitMessage(0)
            win32gui.DestroyWindow(hwnd)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def on(self, event: Event, handler: callable):
        """Registers a handler for a specific event."""
        if inspect.isclass(event):
            event = event()

        self.event_handlers[astuple(event)].append(handler)


class WorkstationState:

    def __init__(self):
        self.locked = False

        self._ws_listener = WorkstationEventsListener()

        self._ws_listener.on(LockEvent(), lambda e: setattr(self, "locked", True))
        self._ws_listener.on(UnlockEvent(), lambda e: setattr(self, "locked", False))

        self._ws_listener.start()

    def is_locked(self) -> bool:
        return self.locked

    def stop_listener(self):
        self._ws_listener.stop()


if __name__ == "__main__":

    ws_state = WorkstationState()
    while True:
        print(ws_state.is_locked())
        time.sleep(1)

    # def handler(event: Event):
    #     print(f"msg={event.msg} {hex(event.msg)}, wparam={event.wparam}, lparam={event.lparam}")
    #     print("get_const", _get_const(event.msg))

    # ws_listener = WorkstationEventsListener()
    # ws_listener.on(AnyEvent(), handler)
    # ws_listener.on(LockEvent(), lambda e: print("LockEvent"))
    # ws_listener.on(UnlockEvent(), lambda e: print("UnlockEvent"))
    # ws_listener.start()
    # time.sleep(5)
    # ws_listener.stop()
    # ws_listener.join()
