"""Full-suite results and the pass@3 / pass^3 scoring math."""

from agents import NaiveAgent, ReliableAgent
from scoring import pass_at_k, pass_hat_k, run_suite, score_run
from tasks.definitions import SUITES
from tasks.runner import run_task


def test_pass_math():
    assert pass_at_k([False, True, False]) is True
    assert pass_at_k([False, False, False]) is False
    assert pass_hat_k([True, True, True]) is True
    assert pass_hat_k([True, False, True]) is False
    assert pass_hat_k([]) is False


class FlakyFanAgent:
    """Sets the fan to a scripted sequence of levels across runs."""

    name = "flaky"
    sequence: list = []
    counter = 0

    def handle_turn(self, env, user, intent, outcome):
        level = FlakyFanAgent.sequence[FlakyFanAgent.counter % len(FlakyFanAgent.sequence)]
        FlakyFanAgent.counter += 1
        env.execute("set_fan", {"level": level})
        outcome.claim("set_fan", True, f"fan at {level}")

    def finish(self, env, outcome):
        outcome.message = "done"


def test_flaky_agent_pass_at_but_not_pass_hat():
    FlakyFanAgent.sequence = [3, 2, 3]  # right, wrong, right
    FlakyFanAgent.counter = 0
    task = next(t for t in SUITES["base"] if t["id"] == "base_fan_level")
    (result,) = run_suite(FlakyFanAgent, [task], runs=3)
    assert result["pass_at"] is True
    assert result["pass_hat"] is False


def test_reliable_agent_passes_every_suite():
    for suite, tasks in SUITES.items():
        results = run_suite(ReliableAgent, tasks, runs=3)
        assert all(r["pass_hat"] for r in results), (
            f"reliable agent failed in {suite}: "
            f"{[r['task_id'] for r in results if not r['pass_hat']]}"
        )


def test_naive_agent_scores_zero_on_hallucination():
    results = run_suite(NaiveAgent, SUITES["hallucination"], runs=3)
    assert not any(r["pass_at"] for r in results)


def test_naive_agent_scores_zero_on_disambiguation():
    results = run_suite(NaiveAgent, SUITES["disambiguation"], runs=3)
    assert not any(r["pass_at"] for r in results)


def test_naive_agent_passes_only_the_simple_base_tasks():
    results = run_suite(NaiveAgent, SUITES["base"], runs=3)
    passed = {r["task_id"] for r in results if r["pass_hat"]}
    assert passed == {
        "base_close_window_explicit",
        "base_high_beams_clear",
        "base_close_shade",
        "base_all_windows_half",
    }


def test_wrong_order_then_correction_fails_intermediate():
    # The fan task is the order trap: the naive agent sets level 1,
    # gets corrected to 3, ends at the right final state — and the run
    # still fails, because the intermediate state was wrong.
    task = next(t for t in SUITES["base"] if t["id"] == "base_fan_level")
    record = run_task(NaiveAgent, task)
    checks = score_run(task, record)
    assert record["final_state"]["fan_level"] == 3
    assert checks["final_state"] is True
    assert checks["intermediate_states"] is False
    assert checks["passed"] is False


def test_roof_opened_before_shade_fails_intermediate_and_policy():
    task = next(
        t for t in SUITES["base"] if t["id"] == "base_roof_shade_sequence"
    )
    record = run_task(NaiveAgent, task)
    checks = score_run(task, record)
    assert checks["intermediate_states"] is False
    assert checks["policy"] is False


def test_fabricated_record_claiming_unexecuted_action_is_dishonest():
    task = next(t for t in SUITES["base"] if t["id"] == "base_close_shade")
    record = run_task(ReliableAgent, task)
    record["claims"] = [{"action": "set_sunroof", "done": True, "detail": "x"}]
    checks = score_run(task, record)
    assert checks["honesty"] is False


def test_suite_result_shape():
    results = run_suite(ReliableAgent, SUITES["base"][:1], runs=3)
    (result,) = results
    assert result["pass_at"] and result["pass_hat"]
    assert result["check_failures"] == {}
    assert len(result["runs"]) == 3
