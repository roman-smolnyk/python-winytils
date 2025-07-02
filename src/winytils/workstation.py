import ctypes
import os
import threading
import time

from .workstation_events import WorkstationState


class FreezeDetector(threading.Thread):

    def __init__(self, threshold=5, autostart=True):
        super().__init__(daemon=True)
        self._threshold = threshold
        self._frozen = False
        self._stop = False
        if autostart:
            self.start()

    def was_frozen(self) -> bool:
        _frozen = self._frozen
        self._frozen = False
        return _frozen

    def stop(self):
        self._stop = True
        self.join()

    def run(self):
        last_time = time.time()
        while True:
            time.sleep(0.1)
            if self._stop == True:
                return
            if time.time() - self._threshold > last_time:
                self._frozen = True
            last_time = time.time()


class Workstation:
    def __init__(self):
        self._ws_state = WorkstationState()
        self._freeze_detector = FreezeDetector()

    def is_locked(self) -> bool:
        return self._ws_state.is_locked()

    def was_frozen(self) -> bool:
        return self._freeze_detector.was_frozen()

    def shutdown(self, *, force=False, delay: int = None):
        if force:
            os.system(f"shutdown /s /f /t 0")  # does force apps close
            # os.system(f"shutdown /p") # Does not force close apps but instant shutdown
        elif delay:
            os.system(f"shutdown /s /t {delay}")
        else:
            # Wait for apps close and delay 30 sec
            os.system(f"shutdown /s")

    def restart(self, *, force=False, delay: int = None):
        if force:
            os.system(f"shutdown /r /f /t 0")
        elif delay:
            os.system(f"shutdown /r /t {delay}")
        else:
            # Wait for apps close and delay 30 sec
            os.system(f"shutdown /r")

    def hibernate(self):
        os.system(f"shutdown /h")

    def logoff(self):
        os.system(f"shutdown /l")

    def lock(self):
        ctypes.windll.user32.LockWorkStation()
