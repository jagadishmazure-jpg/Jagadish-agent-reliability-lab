"""Tool registry behaviour and the four sabotage mechanics."""

from carenv.state import CarState
from carenv.tools import CarEnvironment


def make_env(spec=None, sabotage=None, prefs=None):
    return CarEnvironment(
        CarState.from_spec(spec), preferences=prefs, sabotage=sabotage
    )


def test_set_and_get_roundtrip():
    env = make_env()
    assert env.execute("set_sunroof", {"pct": 50})["success"]
    assert env.execute("get_sunroof_state")["sunroof_pct"] == 50


def test_mutation_appends_history_snapshot():
    env = make_env()
    before = len(env.state.history)
    env.execute("set_fan", {"level": 3})
    assert len(env.state.history) == before + 1


def test_read_does_not_append_history():
    env = make_env()
    before = len(env.state.history)
    env.execute("get_weather")
    assert len(env.state.history) == before


def test_events_recorded_in_order():
    env = make_env()
    env.execute("get_weather")
    env.execute("set_fan", {"level": 1})
    assert [e["tool"] for e in env.events] == ["get_weather", "set_fan"]
    assert env.events[1]["ok"] is True


def test_out_of_range_rejected():
    env = make_env()
    result = env.execute("set_sunroof", {"pct": 250})
    assert not result["success"]
    assert "out_of_range" in result["error"]


def test_missing_parameter_rejected():
    env = make_env()
    result = env.execute("set_window", {"window": "front_left"})
    assert not result["success"]
    assert "missing_parameter" in result["error"]


def test_unknown_window_rejected():
    env = make_env()
    result = env.execute("set_window", {"window": "skylight", "pct": 10})
    assert not result["success"]


def test_removed_tool_not_advertised_and_not_executable():
    env = make_env(sabotage={"remove_tools": ["set_shade"]})
    assert "set_shade" not in env.tool_definitions()
    result = env.execute("set_shade", {"pct": 100})
    assert not result["success"]
    assert "tool_not_available" in result["error"]


def test_removed_parameter_disappears_from_definition():
    env = make_env(sabotage={"remove_params": {"set_window": ["pct"]}})
    defs = env.tool_definitions()
    assert "pct" not in defs["set_window"]["params"]
    assert "window" in defs["set_window"]["params"]


def test_removed_parameter_call_fails():
    env = make_env(sabotage={"remove_params": {"set_window": ["pct"]}})
    result = env.execute("set_window", {"window": "front_left", "pct": 50})
    assert not result["success"]
    assert "unexpected_parameter" in result["error"]


def test_degraded_route_returns_success_without_routes():
    env = make_env(sabotage={"degrade_tools": ["get_route"]})
    result = env.execute("get_route", {"destination": "Riverside Mall"})
    assert result["success"] is True
    assert "routes" not in result


def test_failing_tool_returns_execution_error():
    env = make_env(sabotage={"fail_tools": ["set_sunroof"]})
    result = env.execute("set_sunroof", {"pct": 50})
    assert not result["success"]
    assert "execution_error" in result["error"]
    assert env.state.sunroof_pct == 0


def test_navigation_requires_a_known_route():
    env = make_env()
    result = env.execute(
        "set_navigation", {"destination": "Riverside Mall", "route_id": "ZZ"}
    )
    assert not result["success"]
    env.execute("get_route", {"destination": "Riverside Mall"})
    ok = env.execute(
        "set_navigation", {"destination": "Riverside Mall", "route_id": "R2"}
    )
    assert ok["success"]
    assert env.state.nav_route_id == "R2"


def test_preference_lookup_hit_and_miss():
    env = make_env(prefs={"sunroof_pct": 50})
    assert env.execute("get_preference", {"key": "sunroof_pct"})["value"] == 50
    assert env.execute("get_preference", {"key": "fan_level"})["value"] is None
