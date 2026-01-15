import time
from typing import cast

import API
from _lib.utils import chebyshev_distance, format_time_remaining


class ProvocationScript:
    PROVO_COOLDOWN_SUCCESS = 11
    PROVO_COOLDOWN_FAIL = 3
    PROVO_COOLDOWN_WAIT = 1
    PROXIMITY_THRESHOLD = 5
    SCAN_RADIUS = 12

    PROVO_FAIL_MSG = "Your music fails to incite enough anger"
    PROVO_SUCCESS_MSG = "Your music succeeds, as you start a fight"

    def __init__(self):
        self._last_provo_time = 0
        self._cooldown = self.PROVO_COOLDOWN_SUCCESS
        self._status = ""

    def run(self):
        while not API.StopRequested:
            self._tick()

    def _tick(self):
        self._check_cooldown()

        if not self._is_cooldown_ready():
            return

        mobs = self._find_mobs()
        if len(mobs) < 2:
            self._set_status("Waiting for mobs...")
            API.Pause(1)
            return

        pair = self._find_best_pair(mobs)
        if pair is None:
            self._set_status("No close mob pairs found")
            API.Pause(2)
            return

        success = self._execute_provocation(pair[0], pair[1])
        self._handle_result(success)

    def _find_mobs(self):
        px, py = API.Player.X, API.Player.Y

        mobs = API.NearestMobiles(
            [
                cast(API.Notoriety, API.Notoriety.Murderer),
                cast(API.Notoriety, API.Notoriety.Criminal),
                cast(API.Notoriety, API.Notoriety.Enemy),
                cast(API.Notoriety, API.Notoriety.Gray),
            ],
            self.SCAN_RADIUS,
        )

        return sorted(mobs, key=lambda m: chebyshev_distance(px, py, m.X, m.Y))

    def _find_best_pair(self, mobs):
        px, py = API.Player.X, API.Player.Y
        pairs = []

        for i, mob_a in enumerate(mobs):
            for mob_b in mobs[i + 1 :]:
                dist_between = chebyshev_distance(mob_a.X, mob_a.Y, mob_b.X, mob_b.Y)

                if dist_between <= self.PROXIMITY_THRESHOLD:
                    dist_to_player = chebyshev_distance(px, py, mob_a.X, mob_a.Y)
                    pairs.append((mob_a, mob_b, dist_between, dist_to_player))

        if not pairs:
            return None

        pairs.sort(key=lambda x: (x[2], x[3]))
        return (pairs[0][0], pairs[0][1])

    def _execute_provocation(self, mob_a, mob_b):
        API.ClearJournal()

        API.UseSkill("Provocation")
        if not API.WaitForTarget():
            return False

        API.Target(mob_a.Serial)  # pyright: ignore
        API.HeadMsg(f"Target A: {mob_a.Name}", API.Player)
        if not API.WaitForTarget():
            return False

        API.Target(mob_b.Serial)  # pyright: ignore
        API.HeadMsg(f"Target B: {mob_b.Name}", API.Player)
        API.Pause(0.5)

        if API.InJournal(self.PROVO_SUCCESS_MSG):
            return True

        if API.InJournal(self.PROVO_FAIL_MSG):
            return False

        return False

    def _is_cooldown_ready(self):
        elapsed = time.time() - self._last_provo_time
        return elapsed >= self._cooldown

    def _check_cooldown(self):
        elapsed = time.time() - self._last_provo_time
        remaining = max(0, self._cooldown - elapsed)

        if remaining > 0:
            status = f"Cooldown: {format_time_remaining(remaining)}"
            self._set_status(status)
            API.Pause(1)

    def _handle_result(self, success: bool):
        self._last_provo_time = time.time()

        if success:
            self._cooldown = self.PROVO_COOLDOWN_SUCCESS
            self._set_status(f"Provoked! Next in {self._cooldown}s")
        else:
            self._cooldown = self.PROVO_COOLDOWN_FAIL
            self._set_status(f"Failed. Retry in {self._cooldown}s")

    def _set_status(self, msg: str):
        if msg != self._status:
            self._status = msg
            API.HeadMsg(msg, API.Player)


ProvocationScript().run()
