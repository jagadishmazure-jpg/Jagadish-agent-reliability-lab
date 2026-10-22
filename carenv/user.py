"""A scripted simulated user.

The user is part of the test harness, not of the agent. Each task scripts
the answers the user gives to clarification questions and to confirmation
prompts, so a conversation is fully deterministic. Asking a question the
script has no answer for returns ``None`` — the agent learns nothing, and
the scorer can still see that the question was asked.

Questions and confirmations are appended to the environment's event log
so policy checks (e.g. "confirmation must precede the roof opening") can
be verified against the true order of events.
"""

from __future__ import annotations


class ScriptedUser:
    def __init__(self, env, answers: dict | None = None,
                 confirmations: dict | None = None):
        self.env = env
        self.answers = dict(answers or {})
        self.confirmations = dict(confirmations or {})
        self.questions_asked: list[str] = []
        self.confirmed: set = set()

    def ask(self, question_key: str):
        """Ask the user a question; returns the scripted answer or None."""
        self.questions_asked.append(question_key)
        self.env.events.append({"kind": "ask", "key": question_key})
        return self.answers.get(question_key)

    def confirm(self, confirmation_key: str) -> bool:
        """Ask the user to confirm a warned action; records the event."""
        answer = bool(self.confirmations.get(confirmation_key, False))
        self.env.events.append(
            {"kind": "confirm", "key": confirmation_key, "answer": answer}
        )
        if answer:
            self.confirmed.add(confirmation_key)
        return answer
