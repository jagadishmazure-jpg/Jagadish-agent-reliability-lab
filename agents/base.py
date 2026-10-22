"""Shared plumbing for the two agents.

Both agents receive exactly the same interpretation of each user turn: a
structured intent (action + any values the user actually stated). The
benchmark is not about parsing — it is about what the agent *does* with
an interpretation: which values it invents, which checks it runs, which
order it acts in, and whether its final report matches reality.

An agent fills an :class:`AgentOutcome`:
- ``claims``: structured statements of what the agent says it did.
  The scorer cross-checks every "done" claim against the environment's
  event log, so a claim is a falsifiable assertion, not prose.
- ``explanations``: limitation keys the agent surfaced (e.g.
  ``capability:set_shade``), used by conversational-outcome scoring.
- ``message``: the human-readable final reply.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentOutcome:
    claims: list = field(default_factory=list)
    explanations: list = field(default_factory=list)
    message: str = ""

    def claim(self, action: str, done: bool, detail: str = "") -> None:
        self.claims.append({"action": action, "done": done, "detail": detail})

    def explain(self, key: str) -> None:
        if key not in self.explanations:
            self.explanations.append(key)
