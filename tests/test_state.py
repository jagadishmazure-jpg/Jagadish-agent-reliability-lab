"""Car state: transitions, history recording, validation."""

import pytest

from carenv.state import CarState


def test_initial_snapshot_is_recorded():
    st = CarState()
    assert len(st.history) == 1
    assert st.history[0]["sunroof_pct"] == 0


def test_history_keeps_every_intermediate_state():
    st = CarState()
    st.sunroof_pct = 100
    st.record()
    st.sunroof_pct = 50
    st.record()
    assert [s["sunroof_pct"] for s in st.history] == [0, 100, 50]


def test_snapshot_is_a_copy():
    st = CarState()
    snap = st.snapshot()
    snap["windows"]["front_left"] = 99
    assert st.windows["front_left"] == 0


def test_from_spec_merges_window_defaults():
    st = CarState.from_spec({"windows": {"rear_right": 60}, "fan_level": 2})
    assert st.windows["rear_right"] == 60
    assert st.windows["front_left"] == 0
    assert st.fan_level == 2


def test_invalid_percentage_rejected():
    with pytest.raises(ValueError):
        CarState(sunroof_pct=140)


def test_invalid_fog_value_rejected():
    with pytest.raises(ValueError):
        CarState(fog_lights="dim")


def test_invalid_fan_level_rejected():
    with pytest.raises(ValueError):
        CarState(fan_level=9)


def test_unknown_window_rejected():
    with pytest.raises(ValueError):
        CarState.from_spec({"windows": {"skylight": 10}})
