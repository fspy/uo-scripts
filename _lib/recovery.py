import time
from typing import TYPE_CHECKING

from _lib.runebook import recall_with_retry

if TYPE_CHECKING:
    import API


class Recovery:
    def __init__(self, home_serial=None, timeout=120, retries=2):
        self.home_serial = home_serial
        self.check_interval = timeout
        self.required_confirmations = retries
        self.last_pos = (API.Player.X, API.Player.Y)
        self.last_check = time.time()
        self._retries = 0

    def is_stuck(self):
        now = time.time()
        if now - self.last_check < self.check_interval:
            return False
        current_pos = (API.Player.X, API.Player.Y)
        self.last_check = now
        if current_pos == self.last_pos:
            self._retries += 1
        else:
            self._retries = 0
            self.last_pos = current_pos
        return self._retries >= self.required_confirmations

    def shutdown_cleanly(self, max_retries=3):

        if self.home_serial:
            API.SysMsg("Attempting to recall home before shutdown...", 946)
            if recall_with_retry(self.home_serial, max_retries=max_retries):
                API.SysMsg("Made it home safely", 62)
                return True
            API.SysMsg("Failed to recall home - stopping anyway", 32)
            return False

        API.SysMsg("No home target set - stopping script", 946)
        return False
