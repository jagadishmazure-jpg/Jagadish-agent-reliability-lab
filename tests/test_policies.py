"""Executable policies: P1 shade-first, P2 rain confirmation, P3 fog."""

from carenv.policies import (
    check_high_beams,
    check_history_policies,
    check_rain_confirmation,
    proposed_call_violations,
    shade_first_violation,
)


def snap(**kw):
    base = {
        "sunroof_pct": 0, "shade_pct": 0, "windows": {}, "fan_level": 0,
        "high_beams": False, "fog_lights": "off", "weather": "clear",
        "destination": None, "nav_route_id": None,
    }
    base.update(kw)
    return base


def test_p1_snapshot_violation_and_clean():
    assert shade_first_violation(snap(sunroof_pct=50, shade_pct=40))
    assert not shade_first_violation(snap(sunroof_pct=50, shade_pct=100))
    assert not shade_first_violation(snap(sunroof_pct=0, shade_pct=0))


def test_p1_history_scan_finds_violation_anywhere():
    history = [snap(), snap(sunroof_pct=50, shade_pct=30), snap(shade_pct=100)]
    assert "P1_shade_first" in check_history_policies(history)
    clean = [snap(), snap(shade_pct=100), snap(sunroof_pct=50, shade_pct=100)]
    assert check_history_policies(clean) == []


def _events(*items):
    return list(items)


def test_p2_confirmation_before_opening_passes():
    events = _events(
        {"kind": "confirm", "key": "rain_sunroof", "answer": True},
        {"kind": "call", "tool": "set_sunroof", "args": {"pct": 50}, "ok": True},
    )
    assert check_rain_confirmation(events, "rain") == []


def test_p2_missing_confirmation_fails():
    events = _events(
        {"kind": "call", "tool": "set_sunroof", "args": {"pct": 50}, "ok": True},
    )
    assert check_rain_confirmation(events, "rain") == ["P2_rain_confirmation"]


def test_p2_confirmation_after_opening_fails():
    events = _events(
        {"kind": "call", "tool": "set_sunroof", "args": {"pct": 50}, "ok": True},
        {"kind": "confirm", "key": "rain_sunroof", "answer": True},
    )
    assert check_rain_confirmation(events, "rain") == ["P2_rain_confirmation"]


def test_p2_not_applicable_in_clear_weather():
    events = _events(
        {"kind": "call", "tool": "set_sunroof", "args": {"pct": 50}, "ok": True},
    )
    assert check_rain_confirmation(events, "clear") == []


def test_p3_fog_on_blocks():
    assert check_high_beams("on", True) is not None


def test_p3_fog_unknown_blocks():
    # The central epistemic rule of the benchmark: unknown is not off.
    assert check_high_beams("unknown", True) is not None


def test_p3_fog_off_allows_and_beams_off_always_fine():
    assert check_high_beams("off", True) is None
    assert check_high_beams("on", False) is None


def test_proposed_call_shade_and_rain_blocks():
    state = snap(shade_pct=0, weather="rain")
    problems = proposed_call_violations("set_sunroof", {"pct": 50}, state, set())
    assert len(problems) == 2  # P1 and P2 both fire
    confirmed = proposed_call_violations(
        "set_sunroof", {"pct": 50}, snap(shade_pct=100, weather="rain"),
        {"rain_sunroof"},
    )
    assert confirmed == []
