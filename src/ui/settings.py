"""
Remembers per-user UI preferences (theme, sidebar, sort, compact tiles)
in ~/Lab_master/ui_settings.json. Missing or broken files fall back to defaults.
"""
import json
from pathlib import Path

PATH = Path("~/Lab_master/ui_settings.json").expanduser()

DEFAULTS = {
    "theme":           "dark",
    "sidebar_visible": True,
    "sort":            "ip",
    "compact":         False,
}

_values = None


def _load():
    global _values
    _values = dict(DEFAULTS)
    try:
        stored = json.loads(PATH.read_text(encoding="utf-8"))
        _values.update({k: v for k, v in stored.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass


def get(key):
    if _values is None:
        _load()
    return _values.get(key, DEFAULTS.get(key))


def set(key, value):
    if _values is None:
        _load()
    _values[key] = value
    try:
        PATH.parent.mkdir(parents=True, exist_ok=True)
        PATH.write_text(json.dumps(_values, indent=2), encoding="utf-8")
    except OSError:
        pass                      # preferences are a convenience, never an error
