import threading
import time
from collections import defaultdict
from datetime import datetime
from enum import Enum

import psutil
import win32api
import win32con
import win32gui
import win32ts


def get_system_boot_time():
    """
    Retrieves the system boot time using psutil.

    :return: A datetime object representing the boot time.
    """
    boot_timestamp = psutil.boot_time()
    boot_dt = datetime.fromtimestamp(boot_timestamp)
    return boot_dt


class SessionEvent(Enum):
    ANY = 0
    CHANGE = 0x2B1
    CONSOLE_CONNECT = 0x1
    CONSOLE_DISCONNECT = 0x2
    REMOTE_CONNECT = 0x3
    REMOTE_DISCONNECT = 0x4
    SESSION_LOGON = 0x5
    SESSION_LOGOFF = 0x6
    SESSION_LOCK = 0x7
    SESSION_UNLOCK = 0x8
    SESSION_REMOTE_CONTROL = 0x9


class WorkstationMonitor:
    CLASS_NAME = "WorkstationMonitor"
    WINDOW_TITLE = "Workstation Event Monitor"

    def __init__(self):
        self.window_handle = None
        self.event_handlers = defaultdict(list)
        self._register_listener()

    def _register_listener(self):
        """Registers the listener with Win32 GUI to listen to session events."""
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = self.CLASS_NAME
        wc.lpfnWndProc = self._window_procedure  # This is the window procedure

        # Register the window class
        window_class = win32gui.RegisterClass(wc)

        # Create the window with the correct arguments
        self.window_handle = win32gui.CreateWindow(
            window_class,  # Window class
            self.WINDOW_TITLE,  # Window title
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
        win32gui.UpdateWindow(self.window_handle)

        # Register session notifications
        # win32ts.NOTIFY_FOR_THIS_SESSION
        win32ts.WTSRegisterSessionNotification(self.window_handle, win32ts.NOTIFY_FOR_ALL_SESSIONS)

    def listen(self):
        """Start listening for events."""
        win32gui.PumpMessages()

    def stop(self):
        """Stop the listener."""
        win32gui.PostQuitMessage(0)

    def _window_procedure(self, hwnd: int, msg: int, wparam, lparam):
        """Processes window messages and invokes handlers."""
        if msg == SessionEvent.CHANGE.value:
            self._handle_session_change(SessionEvent(wparam), lparam)
        elif msg in [win32con.WM_CLOSE, win32con.WM_DESTROY]:
            win32gui.DestroyWindow(hwnd)
            win32gui.PostQuitMessage(0)
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def _handle_session_change(self, event: SessionEvent, session_id: int):
        """Handles session change events."""
        for handler in self.event_handlers[event]:
            handler(event, session_id)
        for handler in self.event_handlers[SessionEvent.ANY]:
            handler(event, session_id)

    def register_handler(self, event: SessionEvent, handler: callable):
        """Registers a handler for a specific event."""
        self.event_handlers[event].append(handler)


class MachineStateScanner(threading.Thread):
    def __init__(self):
        super().__init__()
        self.locked = False
        self.unlocked = False
        self.on_lock_func = None
        self.on_unlock_func = None

    def on_lock(self, func: callable, *args, **kwargs):
        """Sets the lock handler."""
        self.on_lock_func = func
        self.on_lock_args = args
        self.on_lock_kwargs = kwargs

    def on_unlock(self, func: callable, *args, **kwargs):
        """Sets the unlock handler."""
        self.on_unlock_func = func
        self.on_unlock_args = args
        self.on_unlock_kwargs = kwargs

    def handler(self, event, session_id):
        """Main event handler for lock/unlock events."""
        if event == SessionEvent.SESSION_LOCK:
            self.locked = True
            self.unlocked = False
            if self.on_lock_func:
                self.on_lock_func(*self.on_lock_args, **self.on_lock_kwargs)
        elif event == SessionEvent.SESSION_UNLOCK:
            self.locked = False
            self.unlocked = True
            if self.on_unlock_func:
                self.on_unlock_func(*self.on_unlock_args, **self.on_unlock_kwargs)

    def run(self):
        """Run method for the thread, used to start the listener."""
        self.wm = WorkstationMonitor()
        self.wm.register_handler(SessionEvent.ANY, self.handler)
        self.wm.listen()  # Do not try listen in thread as it won't work

    def stop(self):
        """Stop the workstation monitor."""
        self.wm.stop()


def handler(event, session_id):
    """Simple handler for lock/unlock events."""
    if event == SessionEvent.SESSION_LOCK:
        print("Session Locked")
    elif event == SessionEvent.SESSION_UNLOCK:
        print("Session Unlocked")


def on_lock():
    """Custom lock handler."""
    print("Custom Lock Handler")


def on_unlock(text):
    """Custom unlock handler."""
    print(f"Custom Unlock Handler: {text}")


def example0():
    """Example for basic event listening."""
    wm = WorkstationMonitor()
    wm.register_handler(SessionEvent.ANY, handler=handler)
    wm.listen()


def example1():
    """TaskScheduler example with custom lock/unlock handlers."""
    ms = MachineStateScanner()
    ms.on_lock(on_lock)
    ms.on_unlock(on_unlock, "Hello from unlock!")
    ms.start()
    try:
        ms.join()
    except KeyboardInterrupt:
        print("Stopping...")
        ms.stop()
        ms.join()


def example2():
    """Another example demonstrating manual state checking."""
    ms = MachineStateScanner()
    ms.start()
    try:
        already_locked = False
        already_unlocked = False
        while True:
            if ms.locked:
                if not already_locked:
                    print("System Locked - Example2")
                    already_locked = True
                    already_unlocked = False
            elif ms.unlocked:
                if not already_unlocked:
                    print("System Unlocked - Example2")
                    already_unlocked = True
                    already_locked = False
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("Stopping...")
        ms.stop()


if __name__ == "__main__":
    example2()  # Choose the example you want to run.
