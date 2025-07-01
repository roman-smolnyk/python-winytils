import os
import ctypes


class Workstation:
    def __init__(self):
        pass

    def shutdown(self, *, force=False, delay: int = None):
        if force:
            os.system(f"shutdown /s /f /t 0") # does force apps close
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

    def log_out(self):
        os.system(f"shutdown /l")

    def lock(self):
        ctypes.windll.user32.LockWorkStation()

