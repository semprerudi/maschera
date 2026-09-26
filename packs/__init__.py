"""Pack-Loader (SPEC §12). Ein Pack traegt die gesamte Laenderlogik.

    from packs import load_pack
    PACK = load_pack("ch")
"""

from __future__ import annotations

import importlib
from types import ModuleType

AVAILABLE = ("ch",)


def load_pack(name: str = "ch") -> ModuleType:
    if name not in AVAILABLE:
        raise ValueError(f"unbekannter Pack {name!r}, verfügbar: {AVAILABLE}")
    return importlib.import_module(f"packs.{name}.adapter")
