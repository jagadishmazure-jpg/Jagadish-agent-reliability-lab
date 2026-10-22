"""The reliability-checked agent.

Same interpretation layer as the naive baseline — deliberately. The
difference is everything wrapped around the interpretation:

1. **Resolution before action.** A missing value is resolved from the
   preference store, then from live state, then by asking the user.
   It is never guessed (the checker blocks guessed values outright).
2. **Pre-execution checks.** Every proposed mutation passes the checker
   (capability, provenance, policy) before dispatch. A rejected proposal
   returns diagnostics; the agent may revise a bounded number of times
   (e.g. insert the shade-opening step a policy requires), then stops
   and explains the limitation.
3. **An executed-action ledger.** Only calls that actually ran are
   recorded, with their real results. A rejected proposal is not an
   observed action and never reaches the ledger.
4. **Claims from the ledger.** The final report is generated from what
   the ledger says happened — including failures — never from what the
   agent intended. If a tool errored, the report says so.
"""

from __future__ import annotations

from carenv.policies import RAIN_CONFIRM_KEY
from carenv.state import WINDOW_NAMES
from carenv.tools import TOOL_DEFS

from .checker import CONSTANT, PREFERENCE, STATE, USER, Checker, ProposedCall

MAX_REVISIONS = 2

EXPLANATION_TEXT = {
    "capability:set_shade": (
        "I can't open the sunshade: that control is not available in this "
        "car, and the sunroof must not open while the shade is closed."
    ),
    "capability:set_fan": "The fan control is not available in this car.",
    "capability:set_window": (
        "I can't set the window to an exact position: the window control "
        "does not accept a position value."
    ),
    "capability:set_sunroof": "The sunroof control is not available in this car.",
    "unknown_condition:fog_lights": (
        "I can't turn on the high beams: the car reports the fog-light "
        "status as unknown, so I can't establish that it is safe."
    ),
    "policy:high_beams_fog": (
        "I can't turn on the high beams while the fog lights are on."
    ),
    "missing_information:routes": (
        "The route service answered but returned no routes, so I have "
        "nothing to navigate with."
    ),
    "execution_error:set_sunroof": (
        "The sunroof motor reported an error, so the roof did not move."
    ),
    "declined:rain_sunroof": (
        "Understood — I'll leave the sunroof closed while it is raining."
    ),
}


class ReliableAgent:
    name = "reliable"

    def __init__(self):
        self.env = None
        self.user = None
        self.checker: Checker | None = None
        self.ledger: list[dict] = []
        self._revisions = 0

    # -- lifecycle ---------------------------------------------------------

    def begin(self, env, user) -> None:
        self.env = env
        self.user = user
        self.checker = Checker(env)
        self.ledger = []

    def handle_turn(self, env, user, intent, outcome) -> None:
        if self.checker is None:
            self.begin(env, user)
        self._revisions = 0
        handler = getattr(self, f"_do_{intent['action']}")
        handler(env, user, intent, outcome)

    def finish(self, env, outcome) -> None:
        """Build claims and the final message from the ledger only."""
        parts: list[str] = []
        for entry in self.ledger:
            outcome.claim(entry["tool"], entry["ok"], entry["detail"])
            parts.append(entry["detail"])
        for key in outcome.explanations:
            parts.append(EXPLANATION_TEXT.get(key, f"Limitation: {key}."))
        outcome.message = " ".join(parts) if parts else "Nothing to do."

    # -- checked dispatch ----------------------------------------------------

    def _dispatch(self, proposal: ProposedCall):
        """Check, then execute. Returns (result|None, CheckResult|None)."""
        check = self.checker.check(proposal, self.user.confirmed)
        if not check.allowed:
            return None, check
        result = self.env.execute(proposal.tool, proposal.args)
        if TOOL_DEFS[proposal.tool]["mutates"]:
            self.ledger.append({
                "tool": proposal.tool,
                "args": dict(proposal.args),
                "ok": bool(result.get("success")),
                "error": result.get("error"),
                "detail": self._detail(proposal, result),
            })
        return result, None

    @staticmethod
    def _detail(proposal: ProposedCall, result: dict) -> str:
        tool, args = proposal.tool, proposal.args
        if not result.get("success"):
            return f"{tool} failed: {result.get('error')}."
        if tool == "set_sunroof":
            return f"The sunroof is open to {args['pct']}%."
        if tool == "set_shade":
            return f"The shade is set to {args['pct']}%."
        if tool == "set_window":
            return f"The {args['window']} window is set to {args['pct']}%."
        if tool == "set_fan":
            return f"The fan is on at level {args['level']}."
        if tool == "set_high_beams":
            return "The high beams are on." if args["on"] else "The high beams are off."
        if tool == "set_navigation":
            return f"Navigation is set to {args['destination']}."
        return f"{tool} done."

    def _explain_block(self, outcome, check, tool: str) -> None:
        if check.category == "capability":
            outcome.explain(f"capability:{tool}")
        elif check.category == "policy":
            outcome.explain(f"policy:{tool}")
        else:
            outcome.explain(f"blocked:{tool}")

    # -- value resolution ----------------------------------------------------

    def _resolve(self, stated, preference_key, question_key):
        """Resolve a value: stated > preference > ask. Never guess."""
        if stated is not None:
            return stated, USER
        if preference_key:
            result = self.env.execute("get_preference", {"key": preference_key})
            if result.get("value") is not None:
                return result["value"], PREFERENCE
        if question_key:
            answer = self.user.ask(question_key)
            if answer is not None:
                return answer, USER
        return None, None

    # -- actions ---------------------------------------------------------------

    def _open_shade_fully(self, outcome) -> bool:
        proposal = ProposedCall("set_shade", {"pct": 100}, {"pct": CONSTANT})
        result, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_shade")
            return False
        return bool(result and result.get("success"))

    def _do_open_sunroof(self, env, user, intent, outcome):
        pct, prov = self._resolve(intent.get("pct"), "sunroof_pct", "sunroof_pct")
        if pct is None:
            outcome.explain("unresolved_value:sunroof_pct")
            return
        if pct > 0:
            weather = env.execute("get_weather", {}).get("weather")
            if weather == "rain" and RAIN_CONFIRM_KEY not in user.confirmed:
                # Policy P2: warn, then obtain confirmation before acting.
                if not user.confirm(RAIN_CONFIRM_KEY):
                    outcome.explain("declined:rain_sunroof")
                    return
        proposal = ProposedCall("set_sunroof", {"pct": pct}, {"pct": prov})
        result, check = self._dispatch(proposal)
        if check is not None and check.category == "policy" and self._revisions < MAX_REVISIONS:
            # The expected block: shade not fully open yet. Revise by
            # performing the required preparatory step, then re-propose.
            if any("shade" in r for r in check.reasons):
                self._revisions += 1
                if not self._open_shade_fully(outcome):
                    return
                result, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_sunroof")
            return
        if result is not None and not result.get("success"):
            outcome.explain("execution_error:set_sunroof")

    def _do_set_shade(self, env, user, intent, outcome):
        proposal = ProposedCall(
            "set_shade", {"pct": intent["pct"]}, {"pct": USER}
        )
        _, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_shade")

    def _do_close_shade(self, env, user, intent, outcome):
        proposal = ProposedCall("set_shade", {"pct": 0}, {"pct": CONSTANT})
        _, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_shade")

    def _do_less_sunlight(self, env, user, intent, outcome):
        pct, prov = self._resolve(None, "shade_pct", "shade_pct")
        if pct is None:
            outcome.explain("unresolved_value:shade_pct")
            return
        proposal = ProposedCall("set_shade", {"pct": pct}, {"pct": prov})
        _, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_shade")

    def _do_close_window(self, env, user, intent, outcome):
        window = intent.get("window")
        prov = USER
        if window is None:
            state = env.execute("get_window_state", {}).get("windows", {})
            open_windows = [w for w in WINDOW_NAMES if state.get(w, 0) > 0]
            if len(open_windows) == 1:
                window, prov = open_windows[0], STATE
            elif not open_windows:
                outcome.explain("nothing_to_close")
                return
            else:
                answer = user.ask("which_window")
                if answer is None:
                    outcome.explain("unresolved_value:which_window")
                    return
                window, prov = answer, USER
        proposal = ProposedCall(
            "set_window",
            {"window": window, "pct": 0},
            {"window": prov, "pct": CONSTANT},
        )
        _, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_window")

    def _do_set_window(self, env, user, intent, outcome):
        proposal = ProposedCall(
            "set_window",
            {"window": intent["window"], "pct": intent["pct"]},
            {"window": USER, "pct": USER},
        )
        _, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_window")

    def _do_all_windows(self, env, user, intent, outcome):
        for window in WINDOW_NAMES:
            proposal = ProposedCall(
                "set_window",
                {"window": window, "pct": intent["pct"]},
                {"window": CONSTANT, "pct": USER},
            )
            _, check = self._dispatch(proposal)
            if check is not None:
                self._explain_block(outcome, check, "set_window")
                return

    def _do_set_fan(self, env, user, intent, outcome):
        level, prov = self._resolve(intent.get("level"), "fan_level", "fan_level")
        if level is None:
            outcome.explain("unresolved_value:fan_level")
            return
        proposal = ProposedCall("set_fan", {"level": level}, {"level": prov})
        _, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_fan")

    def _do_high_beams(self, env, user, intent, outcome):
        lights = env.execute("get_lights_state", {})
        fog = lights.get("fog_lights")
        proposal = ProposedCall("set_high_beams", {"on": True}, {"on": USER})
        _, check = self._dispatch(proposal)
        if check is not None:
            if fog == "unknown":
                outcome.explain("unknown_condition:fog_lights")
            elif fog == "on":
                outcome.explain("policy:high_beams_fog")
            else:
                self._explain_block(outcome, check, "set_high_beams")

    def _do_navigate(self, env, user, intent, outcome):
        destination = intent["destination"]
        result = env.execute("get_route", {"destination": destination})
        routes = result.get("routes")
        if not routes:
            # A successful call that returned no usable evidence is not
            # a success for the task. Say so; do not invent a route.
            outcome.explain("missing_information:routes")
            return
        best = min(routes, key=lambda r: r["duration_min"])
        proposal = ProposedCall(
            "set_navigation",
            {"destination": destination, "route_id": best["route_id"]},
            {"destination": USER, "route_id": STATE},
        )
        _, check = self._dispatch(proposal)
        if check is not None:
            self._explain_block(outcome, check, "set_navigation")
