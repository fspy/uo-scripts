import json
from typing import TYPE_CHECKING, cast

from API import PersistentVar

if TYPE_CHECKING:
    import API


def load_int(
    key: str, default: int = 0, scope: API.PersistentVar = cast(API.PersistentVar, 1)
) -> int:
    value_str = API.GetPersistentVar(key, str(default), scope)
    try:
        value = int(str(value_str).strip(), 0)
    except Exception:
        return default

    if value < 0:
        return default

    return value


def save_int(key, value, scope=API.PersistentVar.Char) -> None:
    API.SavePersistentVar(key, str(int(value)), cast(API.PersistentVar, scope))


def setup_target(
    key, prompt, verify_in_range=True, scope=API.PersistentVar.Char
) -> int:
    saved = API.GetPersistentVar(key, "0", cast(API.PersistentVar, scope))
    if saved and saved != "0":
        try:
            serial = int(saved)

            if not verify_in_range:
                API.SysMsg(f"Using saved {key}: 0x{serial:X}", 946)
                return serial

            item = API.FindItem(serial)
            if item:
                API.SysMsg(f"Using saved {key}: 0x{serial:X}", 946)
                return serial

            mob = API.FindMobile(serial)
            if mob:
                API.SysMsg(f"Using saved {key}: 0x{serial:X}", 946)
                return serial

            API.SysMsg(f"Saved {key} not found - please re-target", 32)
        except ValueError:
            pass

    # Ask user to target
    API.SysMsg(prompt, 32)
    target = API.RequestTarget(timeout=30.0)
    if not target:
        API.SysMsg(f"No target selected for {key}", 32)
        return 0

    API.SavePersistentVar(key, str(target), cast(PersistentVar, scope))
    API.SysMsg(f"{key} saved: 0x{target:X}", 946)
    return target


def load_json(key, default=None, scope=API.PersistentVar.Char):
    raw = API.GetPersistentVar(key, "", cast(PersistentVar, scope))

    if not raw:
        return default

    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return default


def save_json(key, data, scope=API.PersistentVar.Char) -> None:
    raw = json.dumps(data)
    API.SavePersistentVar(key, raw, cast(PersistentVar, scope))
