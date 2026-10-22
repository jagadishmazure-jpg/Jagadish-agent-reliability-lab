"""Run one agent on one task and capture everything scoring needs.

A fresh environment, user and agent are built per run, so runs are
independent and repeatable. The record keeps the full state history,
the ordered event log, the questions asked, and the agent's structured
claims and explanations.
"""

from __future__ import annotations

import copy

from agents.base import AgentOutcome
from carenv.state import CarState
from carenv.tools import CarEnvironment
from carenv.user import ScriptedUser


def run_task(agent_cls, task: dict) -> dict:
    env = CarEnvironment(
        CarState.from_spec(task.get("initial_state")),
        preferences=task.get("preferences"),
        sabotage=task.get("sabotage"),
    )
    user = ScriptedUser(
        env,
        answers=task.get("user_answers"),
        confirmations=task.get("user_confirmations"),
    )
    agent = agent_cls()
    if hasattr(agent, "begin"):
        agent.begin(env, user)
    outcome = AgentOutcome()

    for turn in task["turns"]:
        agent.handle_turn(env, user, copy.deepcopy(turn["intent"]), outcome)

    followup = task.get("followup")
    if followup:
        value = getattr(env.state, followup["field"])
        if value not in followup["not_in"]:
            agent.handle_turn(
                env, user, copy.deepcopy(followup["intent"]), outcome
            )

    agent.finish(env, outcome)

    return {
        "task_id": task["id"],
        "suite": task["suite"],
        "agent": agent_cls.name,
        "final_state": env.state.snapshot(),
        "history": copy.deepcopy(env.state.history),
        "events": copy.deepcopy(env.events),
        "questions": list(user.questions_asked),
        "claims": copy.deepcopy(outcome.claims),
        "explanations": list(outcome.explanations),
        "message": outcome.message,
    }
