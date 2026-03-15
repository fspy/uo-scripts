from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import API


def is_heavy(buffer: int = 50) -> bool:
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight >= (API.Player.WeightMax - buffer)


def is_overweight(threshold: int = 0) -> bool:
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False
    return API.Player.Weight >= (API.Player.WeightMax + threshold)


def is_overweight_by(over: int) -> bool:
    if not API.Player or API.Player.WeightMax is None or API.Player.Weight is None:
        return False

    return API.Player.Weight >= (API.Player.WeightMax + over)
