"""Car state for the simulated environment.

The state is deliberately small and fully observable through tools. Every
mutating tool execution appends a snapshot to ``history`` so scoring can
judge *intermediate* states, not just where the car ended up. A run that
reaches the right final state by a wrong path (open the roof fully, then
correct it) is visible here and fails intermediate-state scoring.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

WINDOW_NAMES = ("front_left", "front_right", "rear_left", "rear_right")

# Fog status is a three-valued field on purpose: "unknown" is a real value
# the environment can report, and it must never be treated as "off".
FOG_VALUES = ("on", "off", "unknown")
WEATHER_VALUES = ("clear", "rain")


@dataclass
class CarState:
    """Mutable car state. ``history`` holds deep copies, oldest first."""

    sunroof_pct: int = 0  # 0 closed .. 100 fully open
    shade_pct: int = 0  # 0 fully closed (blocking light) .. 100 fully open
    windows: dict = field(
        default_factory=lambda: {name: 0 for name in WINDOW_NAMES}
    )
    fan_level: int = 0  # 0 off .. 5 max
    high_beams: bool = False
    fog_lights: str = "off"  # "on" | "off" | "unknown"
    weather: str = "clear"  # "clear" | "rain"
    destination: str | None = None
    nav_route_id: str | None = None
    history: list = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.fog_lights not in FOG_VALUES:
            raise ValueError(f"fog_lights must be one of {FOG_VALUES}")
        if self.weather not in WEATHER_VALUES:
            raise ValueError(f"weather must be one of {WEATHER_VALUES}")
        for name, pct in self.windows.items():
            if name not in WINDOW_NAMES:
                raise ValueError(f"unknown window: {name}")
            self._check_pct("window " + name, pct)
        self._check_pct("sunroof_pct", self.sunroof_pct)
        self._check_pct("shade_pct", self.shade_pct)
        if not 0 <= self.fan_level <= 5:
            raise ValueError("fan_level must be in 0..5")
        if not self.history:
            self.record()

    @staticmethod
    def _check_pct(label: str, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{label} must be an int percentage")
        if not 0 <= value <= 100:
            raise ValueError(f"{label} must be in 0..100")

    def snapshot(self) -> dict:
        """A plain-dict copy of the observable state (no history)."""
        return {
            "sunroof_pct": self.sunroof_pct,
            "shade_pct": self.shade_pct,
            "windows": dict(self.windows),
            "fan_level": self.fan_level,
            "high_beams": self.high_beams,
            "fog_lights": self.fog_lights,
            "weather": self.weather,
            "destination": self.destination,
            "nav_route_id": self.nav_route_id,
        }

    def record(self) -> None:
        """Append the current snapshot to the ordered history."""
        self.history.append(self.snapshot())

    @classmethod
    def from_spec(cls, spec: dict | None) -> "CarState":
        """Build a state from a task's plain-dict initial-state spec."""
        spec = copy.deepcopy(spec or {})
        windows = {name: 0 for name in WINDOW_NAMES}
        windows.update(spec.pop("windows", {}))
        return cls(windows=windows, **spec)
