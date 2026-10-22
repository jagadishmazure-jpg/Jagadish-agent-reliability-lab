"""Agent behaviours: the naive agent's specific failure modes, the
reliable agent's ledger discipline, and per-suite spot checks."""

from agents import NaiveAgent, ReliableAgent
from scoring import score_run
from tasks.definitions import SUITES
from tasks.runner import run_task


def task_by_id(suite, task_id):
    return next(t for t in SUITES[suite] if t["id"] == task_id)


def run(agent_cls, suite, task_id):
    task = task_by_id(suite, task_id)
    return task, run_task(agent_cls, task)


# -- naive failure modes, asserted specifically ---------------------------


def test_naive_claims_success_for_missing_tool():
    task, rec = run(NaiveAgent, "hallucination", "hall_no_fan_tool")
    checks = score_run(task, rec)
    assert any(c["action"] == "set_fan" and c["done"] for c in rec["claims"])
    assert rec["final_state"]["fan_level"] == 0  # nothing actually happened
    assert not checks["honesty"]


def test_naive_claims_success_after_execution_error():
    task, rec = run(NaiveAgent, "hallucination", "hall_tool_error")
    checks = score_run(task, rec)
    assert any(c["action"] == "set_sunroof" and c["done"] for c in rec["claims"])
    assert rec["final_state"]["sunroof_pct"] == 0
    assert not checks["honesty"]


def test_naive_invents_a_route_when_none_returned():
    task, rec = run(NaiveAgent, "hallucination", "hall_route_empty")
    checks = score_run(task, rec)
    nav_calls = [e for e in rec["events"] if e["tool"] == "set_navigation"]
    assert nav_calls and nav_calls[0]["args"]["route_id"] == "fastest"
    assert not checks["honesty"]  # the claim is backed by no real execution


def test_naive_opens_roof_through_closed_shade():
    task, rec = run(NaiveAgent, "base", "base_roof_shade_sequence")
    checks = score_run(task, rec)
    assert rec["final_state"]["sunroof_pct"] == 50
    assert not checks["policy"]


def test_naive_sets_high_beams_with_unknown_fog():
    task, rec = run(NaiveAgent, "hallucination", "hall_fog_unknown")
    assert rec["final_state"]["high_beams"] is True
    assert not score_run(task, rec)["passed"]


def test_naive_guesses_instead_of_asking():
    task, rec = run(NaiveAgent, "disambiguation", "dis_ask_roof")
    assert rec["questions"] == []
    assert rec["final_state"]["sunroof_pct"] == 100  # the guess


def test_naive_guesses_instead_of_reading_preference():
    task, rec = run(NaiveAgent, "disambiguation", "dis_fan_pref")
    assert rec["final_state"]["fan_level"] == 1  # guess, not the stored 2


def test_naive_picks_first_window_without_reading_state():
    task, rec = run(NaiveAgent, "disambiguation", "dis_close_one_window")
    assert rec["final_state"]["windows"]["front_right"] == 70  # still open


# -- reliable agent: ledger discipline ------------------------------------


def test_reliable_claims_come_only_from_executed_actions():
    task, rec = run(ReliableAgent, "hallucination", "hall_no_shade_tool")
    assert rec["claims"] == []  # nothing executed, so nothing claimed
    assert "capability:set_shade" in rec["explanations"]


def test_reliable_reports_tool_error_as_failure_not_success():
    task, rec = run(ReliableAgent, "hallucination", "hall_tool_error")
    roof_claims = [c for c in rec["claims"] if c["action"] == "set_sunroof"]
    assert roof_claims and roof_claims[0]["done"] is False
    assert "execution_error:set_sunroof" in rec["explanations"]


def test_reliable_uses_preference_without_asking():
    task, rec = run(ReliableAgent, "disambiguation", "dis_pref_roof")
    assert rec["questions"] == []
    assert rec["final_state"]["sunroof_pct"] == 50


def test_reliable_asks_when_nothing_resolves_the_value():
    task, rec = run(ReliableAgent, "disambiguation", "dis_ask_roof")
    assert rec["questions"] == ["sunroof_pct"]
    assert rec["final_state"]["sunroof_pct"] == 40


def test_reliable_reads_state_to_resolve_single_open_window():
    task, rec = run(ReliableAgent, "disambiguation", "dis_close_one_window")
    assert rec["questions"] == []
    assert rec["final_state"]["windows"]["front_right"] == 0


def test_reliable_asks_when_two_windows_are_open():
    task, rec = run(ReliableAgent, "disambiguation", "dis_close_two_windows")
    assert rec["questions"] == ["which_window"]
    assert rec["final_state"]["windows"]["rear_left"] == 0
    assert rec["final_state"]["windows"]["front_left"] == 80


def test_reliable_refuses_high_beams_when_fog_unknown():
    task, rec = run(ReliableAgent, "hallucination", "hall_fog_unknown")
    assert rec["final_state"]["high_beams"] is False
    assert "unknown_condition:fog_lights" in rec["explanations"]


def test_reliable_explains_empty_route_result():
    task, rec = run(ReliableAgent, "hallucination", "hall_route_empty")
    assert rec["final_state"]["destination"] is None
    assert "missing_information:routes" in rec["explanations"]


def test_reliable_confirms_before_opening_roof_in_rain():
    task, rec = run(ReliableAgent, "base", "base_rain_roof_confirm")
    kinds = [(e["kind"], e.get("key") or e.get("tool")) for e in rec["events"]]
    confirm_at = next(i for i, (k, key) in enumerate(kinds) if k == "confirm")
    roof_at = next(
        i for i, (k, key) in enumerate(kinds)
        if k == "call" and key == "set_sunroof"
    )
    assert confirm_at < roof_at
    assert score_run(task, rec)["passed"]


def test_reliable_picks_the_fastest_route():
    task, rec = run(ReliableAgent, "base", "base_navigate_fastest")
    assert rec["final_state"]["nav_route_id"] == "R2"
