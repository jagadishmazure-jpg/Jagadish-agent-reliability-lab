"""Pre-execution checker: capability, provenance, policy gates."""

from agents.checker import (
    CONSTANT,
    GUESS,
    PREFERENCE,
    STATE,
    USER,
    Checker,
    ProposedCall,
)
from carenv.state import CarState
from carenv.tools import CarEnvironment


def make_checker(spec=None, sabotage=None):
    env = CarEnvironment(CarState.from_spec(spec), sabotage=sabotage)
    return Checker(env), env


def test_valid_call_allowed():
    checker, _ = make_checker({"shade_pct": 100})
    result = checker.check(
        ProposedCall("set_sunroof", {"pct": 50}, {"pct": USER}), set()
    )
    assert result.allowed


def test_removed_tool_blocked_as_capability():
    checker, _ = make_checker(sabotage={"remove_tools": ["set_fan"]})
    result = checker.check(
        ProposedCall("set_fan", {"level": 2}, {"level": USER}), set()
    )
    assert not result.allowed and result.category == "capability"


def test_removed_parameter_blocked_as_capability():
    checker, _ = make_checker(
        sabotage={"remove_params": {"set_window": ["pct"]}}
    )
    result = checker.check(
        ProposedCall(
            "set_window",
            {"window": "front_left", "pct": 50},
            {"window": USER, "pct": USER},
        ),
        set(),
    )
    assert not result.allowed and result.category == "capability"


def test_missing_argument_blocked():
    checker, _ = make_checker()
    result = checker.check(ProposedCall("set_fan", {}, {}), set())
    assert not result.allowed and result.category == "capability"


def test_out_of_range_blocked():
    checker, _ = make_checker()
    result = checker.check(
        ProposedCall("set_fan", {"level": 9}, {"level": USER}), set()
    )
    assert not result.allowed and result.category == "capability"


def test_guessed_value_blocked_as_provenance():
    checker, _ = make_checker()
    result = checker.check(
        ProposedCall("set_fan", {"level": 3}, {"level": GUESS}), set()
    )
    assert not result.allowed and result.category == "provenance"
    assert "guessed" in result.reasons[0]


def test_untagged_value_counts_as_guessed():
    checker, _ = make_checker()
    result = checker.check(ProposedCall("set_fan", {"level": 3}, {}), set())
    assert not result.allowed and result.category == "provenance"


def test_preference_and_state_tags_allowed():
    checker, _ = make_checker()
    by_pref = checker.check(
        ProposedCall("set_fan", {"level": 2}, {"level": PREFERENCE}), set()
    )
    assert by_pref.allowed
    by_state = checker.check(
        ProposedCall(
            "set_window",
            {"window": "rear_left", "pct": 0},
            {"window": STATE, "pct": CONSTANT},
        ),
        set(),
    )
    assert by_state.allowed


def test_shade_policy_blocks_roof_first():
    checker, _ = make_checker({"shade_pct": 20})
    result = checker.check(
        ProposedCall("set_sunroof", {"pct": 50}, {"pct": USER}), set()
    )
    assert not result.allowed and result.category == "policy"


def test_rain_policy_blocks_until_confirmed():
    checker, _ = make_checker({"shade_pct": 100, "weather": "rain"})
    proposal = ProposedCall("set_sunroof", {"pct": 50}, {"pct": USER})
    assert not checker.check(proposal, set()).allowed
    assert checker.check(proposal, {"rain_sunroof"}).allowed


def test_unknown_fog_blocks_high_beams():
    checker, _ = make_checker({"fog_lights": "unknown"})
    result = checker.check(
        ProposedCall("set_high_beams", {"on": True}, {"on": USER}), set()
    )
    assert not result.allowed and result.category == "policy"


def test_capability_checked_before_provenance():
    # Even a guessed value must not mask a missing-tool problem: the
    # diagnostic order matters because the agent revises on it.
    checker, _ = make_checker(sabotage={"remove_tools": ["set_fan"]})
    result = checker.check(
        ProposedCall("set_fan", {"level": 3}, {"level": GUESS}), set()
    )
    assert result.category == "capability"
