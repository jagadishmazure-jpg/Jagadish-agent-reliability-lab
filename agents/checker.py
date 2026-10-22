"""The pre-execution checker: no proposal leaves the agent unchecked.

The model (here, a scripted interpretation layer) *proposes* tool calls.
This checker decides whether a proposal may be dispatched, examining it
on three axes before anything touches the car:

(a) **Capability** — the tool exists in the registry as currently
    advertised, and it accepts exactly these parameters with valid
    values. A removed tool or a removed parameter is caught here, before
    execution, not after a confused failure.

(b) **Provenance** — every argument value carries a tag recording where
    it came from: stated by the user, retrieved from the preference
    store, read from live state, or *guessed*. A guessed value for a
    required parameter blocks execution; the agent must resolve the
    value (preference lookup, state read, or a clarifying question)
    instead of inventing one.

(c) **Policy** — the car's executable rules (see carenv.policies),
    including required confirmations and the rule that an "unknown"
    sensor field cannot establish a safety condition.

A rejected proposal returns diagnostics, never silence: the agent may
revise a bounded number of times, then must explain the limitation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from carenv.policies import proposed_call_violations

# Provenance tags
USER = "user"                # stated by the user in this conversation
PREFERENCE = "preference"    # retrieved from the preference store
STATE = "state"              # read from live car state
CONSTANT = "constant"        # fixed by the procedure itself (e.g. shade=100)
GUESS = "guess"              # invented by the agent — never dispatchable


@dataclass
class ProposedCall:
    tool: str
    args: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)


@dataclass
class CheckResult:
    allowed: bool
    category: str | None = None  # "capability" | "provenance" | "policy"
    reasons: list = field(default_factory=list)


def _capability_problems(env, proposal: ProposedCall) -> list[str]:
    defs = env.tool_definitions()
    if proposal.tool not in defs:
        return [
            f"capability: tool {proposal.tool!r} is not available in this car"
        ]
    params = defs[proposal.tool]["params"]
    problems: list[str] = []
    for key in proposal.args:
        if key not in params:
            problems.append(
                f"capability: {proposal.tool} does not accept a {key!r} parameter"
            )
    for key, (kind, lo, hi) in params.items():
        if key not in proposal.args:
            problems.append(
                f"capability: {proposal.tool} requires a {key!r} argument"
            )
            continue
        value = proposal.args[key]
        if kind in ("pct", "level"):
            if not isinstance(value, int) or isinstance(value, bool):
                problems.append(f"capability: {key!r} must be an integer")
            elif not lo <= value <= hi:
                problems.append(
                    f"capability: {key}={value} is outside {lo}..{hi}"
                )
        elif kind == "bool" and not isinstance(value, bool):
            problems.append(f"capability: {key!r} must be a boolean")
        elif kind in ("str", "route_id") and not (
            isinstance(value, str) and value
        ):
            problems.append(f"capability: {key!r} must be a non-empty string")
    return problems


def _provenance_problems(proposal: ProposedCall) -> list[str]:
    problems: list[str] = []
    for key in proposal.args:
        tag = proposal.provenance.get(key, GUESS)
        if tag == GUESS:
            problems.append(
                f"provenance: the value for {key!r} was guessed; it must be "
                "stated by the user, retrieved from preferences, or read "
                "from the car's state"
            )
        elif tag not in (USER, PREFERENCE, STATE, CONSTANT):
            problems.append(f"provenance: unknown tag {tag!r} for {key!r}")
    return problems


class Checker:
    """Validates proposed calls against the live environment."""

    def __init__(self, env):
        self.env = env

    def check(self, proposal: ProposedCall, confirmations: set) -> CheckResult:
        problems = _capability_problems(self.env, proposal)
        if problems:
            return CheckResult(False, "capability", problems)
        problems = _provenance_problems(proposal)
        if problems:
            return CheckResult(False, "provenance", problems)
        problems = proposed_call_violations(
            proposal.tool,
            proposal.args,
            self.env.state.snapshot(),
            set(confirmations),
        )
        if problems:
            return CheckResult(False, "policy", problems)
        return CheckResult(True)
