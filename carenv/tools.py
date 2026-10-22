"""Tool registry and execution environment, with sabotage support.

A task may sabotage the environment in four ways, mirroring the failure
classes this benchmark exists to expose:

- ``remove_tools``: a tool disappears from the registry entirely.
- ``remove_params``: a tool stays, but one of its parameters is gone —
  presence of the tool is not presence of the capability.
- ``degrade_tools``: a tool returns ``success`` but with the payload the
  caller needs missing (an *incomplete result*).
- ``fail_tools``: a tool returns an execution error.

Sabotage changes what the registry *advertises* as well as what it does,
so an agent that inspects definitions before acting can detect the first
two classes up front. Nothing here enforces policy: the environment
executes what it is told. Policy is the agent's (and the scorer's)
business — which is exactly why a careless agent can break the rules
while every individual tool call "succeeds".
"""

from __future__ import annotations

import copy

from .state import WINDOW_NAMES, CarState

# Parameter spec: name -> (kind, minimum, maximum). kind is "pct", "level",
# "enum_window", "bool", "str" or "route_id".
TOOL_DEFS: dict[str, dict] = {
    "get_sunroof_state": {"params": {}, "mutates": False},
    "get_shade_state": {"params": {}, "mutates": False},
    "set_shade": {"params": {"pct": ("pct", 0, 100)}, "mutates": True},
    "set_sunroof": {"params": {"pct": ("pct", 0, 100)}, "mutates": True},
    "get_window_state": {"params": {}, "mutates": False},
    "set_window": {
        "params": {"window": ("enum_window", None, None), "pct": ("pct", 0, 100)},
        "mutates": True,
    },
    "set_fan": {"params": {"level": ("level", 0, 5)}, "mutates": True},
    "get_lights_state": {"params": {}, "mutates": False},
    "set_high_beams": {"params": {"on": ("bool", None, None)}, "mutates": True},
    "get_weather": {"params": {}, "mutates": False},
    "get_route": {"params": {"destination": ("str", None, None)}, "mutates": False},
    "set_navigation": {
        "params": {
            "destination": ("str", None, None),
            "route_id": ("route_id", None, None),
        },
        "mutates": True,
    },
    "get_preference": {"params": {"key": ("str", None, None)}, "mutates": False},
}

# Deterministic route table for the fictional city used by the tasks.
ROUTE_TABLE: dict[str, list[dict]] = {
    "Riverside Mall": [
        {"route_id": "R1", "duration_min": 25, "distance_km": 11.0},
        {"route_id": "R2", "duration_min": 18, "distance_km": 12.5},
        {"route_id": "R3", "duration_min": 32, "distance_km": 10.2},
    ],
    "Airport": [
        {"route_id": "A1", "duration_min": 40, "distance_km": 28.0},
        {"route_id": "A2", "duration_min": 34, "distance_km": 30.5},
    ],
}


def _validate_args(tool: str, params: dict, args: dict) -> str | None:
    for key in args:
        if key not in params:
            return f"unexpected_parameter: {key} is not accepted by {tool}"
    for key, (kind, lo, hi) in params.items():
        if key not in args:
            return f"missing_parameter: {tool} requires {key}"
        value = args[key]
        if kind in ("pct", "level"):
            if not isinstance(value, int) or isinstance(value, bool):
                return f"invalid_type: {key} must be an integer"
            if not lo <= value <= hi:
                return f"out_of_range: {key}={value} outside {lo}..{hi}"
        elif kind == "enum_window":
            if value not in WINDOW_NAMES:
                return f"invalid_value: unknown window {value!r}"
        elif kind == "bool":
            if not isinstance(value, bool):
                return f"invalid_type: {key} must be a boolean"
        elif kind in ("str", "route_id"):
            if not isinstance(value, str) or not value:
                return f"invalid_type: {key} must be a non-empty string"
    return None


class CarEnvironment:
    """State + tool registry + preferences + an ordered event log."""

    def __init__(self, state: CarState, preferences: dict | None = None,
                 sabotage: dict | None = None):
        self.state = state
        self.preferences = dict(preferences or {})
        sabotage = sabotage or {}
        self.removed_tools: set = set(sabotage.get("remove_tools", []))
        self.removed_params: dict = {
            k: set(v) for k, v in sabotage.get("remove_params", {}).items()
        }
        self.degraded_tools: set = set(sabotage.get("degrade_tools", []))
        self.failing_tools: set = set(sabotage.get("fail_tools", []))
        self.events: list[dict] = []  # calls / asks / confirms, in order
        self.last_routes: list[dict] = []

    # -- registry introspection (what an agent may legitimately inspect) --

    def tool_definitions(self) -> dict:
        """Definitions as currently advertised, sabotage applied."""
        defs: dict = {}
        for name, spec in TOOL_DEFS.items():
            if name in self.removed_tools:
                continue
            params = {
                p: s for p, s in spec["params"].items()
                if p not in self.removed_params.get(name, set())
            }
            defs[name] = {"params": params, "mutates": spec["mutates"]}
        return defs

    def has_tool(self, name: str) -> bool:
        return name in self.tool_definitions()

    # -- execution ---------------------------------------------------------

    def execute(self, tool: str, args: dict | None = None) -> dict:
        """Execute one call. Always returns a structured result dict."""
        args = dict(args or {})
        result = self._execute_inner(tool, args)
        self.events.append({
            "kind": "call",
            "tool": tool,
            "args": copy.deepcopy(args),
            "ok": bool(result.get("success")),
            "error": result.get("error"),
        })
        return result

    def _execute_inner(self, tool: str, args: dict) -> dict:
        if tool in self.removed_tools or tool not in TOOL_DEFS:
            return {"success": False, "error": f"tool_not_available: {tool}"}
        params = {
            p: s for p, s in TOOL_DEFS[tool]["params"].items()
            if p not in self.removed_params.get(tool, set())
        }
        problem = _validate_args(tool, params, args)
        if problem:
            return {"success": False, "error": problem}
        if tool in self.failing_tools:
            return {"success": False, "error": f"execution_error: {tool} failed in the car"}
        return self._dispatch(tool, args)

    def _dispatch(self, tool: str, args: dict) -> dict:
        st = self.state
        if tool == "get_sunroof_state":
            return {"success": True, "sunroof_pct": st.sunroof_pct}
        if tool == "get_shade_state":
            return {"success": True, "shade_pct": st.shade_pct}
        if tool == "get_window_state":
            return {"success": True, "windows": dict(st.windows)}
        if tool == "get_lights_state":
            return {"success": True, "high_beams": st.high_beams,
                    "fog_lights": st.fog_lights}
        if tool == "get_weather":
            return {"success": True, "weather": st.weather}
        if tool == "get_preference":
            return {"success": True, "key": args["key"],
                    "value": self.preferences.get(args["key"])}
        if tool == "get_route":
            if tool in self.degraded_tools:
                # Success, but the payload the caller needs is absent.
                return {"success": True, "destination": args["destination"]}
            routes = copy.deepcopy(ROUTE_TABLE.get(args["destination"], []))
            self.last_routes = routes
            return {"success": True, "destination": args["destination"],
                    "routes": routes}
        if tool == "set_shade":
            st.shade_pct = args["pct"]
            st.record()
            return {"success": True, "shade_pct": st.shade_pct}
        if tool == "set_sunroof":
            st.sunroof_pct = args["pct"]
            st.record()
            return {"success": True, "sunroof_pct": st.sunroof_pct}
        if tool == "set_window":
            st.windows[args["window"]] = args["pct"]
            st.record()
            return {"success": True, "window": args["window"],
                    "pct": st.windows[args["window"]]}
        if tool == "set_fan":
            st.fan_level = args["level"]
            st.record()
            return {"success": True, "fan_level": st.fan_level}
        if tool == "set_high_beams":
            st.high_beams = args["on"]
            st.record()
            return {"success": True, "high_beams": st.high_beams}
        if tool == "set_navigation":
            known = {r["route_id"] for r in self.last_routes}
            if args["route_id"] not in known:
                return {"success": False,
                        "error": f"unknown_route_id: {args['route_id']}"}
            st.destination = args["destination"]
            st.nav_route_id = args["route_id"]
            st.record()
            return {"success": True, "destination": st.destination,
                    "route_id": st.nav_route_id}
        raise AssertionError(f"unhandled tool {tool}")  # pragma: no cover
