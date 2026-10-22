"""The naive baseline agent.

This agent is not stupid; it is *un checked*. It interprets each request
literally, fills gaps with plausible defaults instead of asking, calls
tools in the order the request mentions them, never reads a policy, and
— the failure this benchmark exists to expose — reports success based
on what it *intended* to do. Tool errors, missing tools and missing
parameters do not change its story. Its final message is generated from
its plan, not from observed results.

Every behaviour here is a real failure mode seen in shipped assistants:
claiming an action that never happened, guessing a value the user never
gave, and treating a tool's silence as consent.
"""

from __future__ import annotations

from carenv.state import WINDOW_NAMES

# Plausible defaults the naive agent invents instead of resolving values.
GUESS_SUNROOF_PCT = 100
GUESS_FAN_LEVEL = 1
GUESS_SHADE_PCT = 50


class NaiveAgent:
    name = "naive"

    def handle_turn(self, env, user, intent, outcome) -> None:
        action = intent["action"]
        handler = getattr(self, f"_do_{action}")
        handler(env, user, intent, outcome)

    def finish(self, env, outcome) -> None:
        done = [c["detail"] for c in outcome.claims if c["done"]]
        outcome.message = (
            "Done. " + " ".join(done) if done else "Done."
        )

    # -- helpers -----------------------------------------------------------

    def _call(self, env, tool, args):
        return env.execute(tool, args)

    def _claim_done(self, outcome, tool, detail):
        # The naive agent claims from intention: the call was *made*,
        # so in its story the action *happened* — result unchecked.
        outcome.claim(tool, True, detail)

    # -- actions -----------------------------------------------------------

    def _do_open_sunroof(self, env, user, intent, outcome):
        pct = intent.get("pct")
        if pct is None:
            pct = GUESS_SUNROOF_PCT
        self._call(env, "set_sunroof", {"pct": pct})
        self._claim_done(outcome, "set_sunroof", f"The sunroof is open to {pct}%.")

    def _do_set_shade(self, env, user, intent, outcome):
        pct = intent["pct"]
        self._call(env, "set_shade", {"pct": pct})
        self._claim_done(outcome, "set_shade", f"The shade is set to {pct}%.")

    def _do_close_shade(self, env, user, intent, outcome):
        self._call(env, "set_shade", {"pct": 0})
        self._claim_done(outcome, "set_shade", "The shade is closed.")

    def _do_less_sunlight(self, env, user, intent, outcome):
        self._call(env, "set_shade", {"pct": GUESS_SHADE_PCT})
        self._claim_done(
            outcome, "set_shade",
            f"I reduced the sunlight by setting the shade to {GUESS_SHADE_PCT}%.",
        )

    def _do_close_window(self, env, user, intent, outcome):
        window = intent.get("window")
        if window is None:
            window = WINDOW_NAMES[0]  # arbitrary pick, no state read
        self._call(env, "set_window", {"window": window, "pct": 0})
        self._claim_done(outcome, "set_window", f"The {window} window is closed.")

    def _do_set_window(self, env, user, intent, outcome):
        self._call(
            env, "set_window",
            {"window": intent["window"], "pct": intent["pct"]},
        )
        self._claim_done(
            outcome, "set_window",
            f"The {intent['window']} window is set to {intent['pct']}%.",
        )

    def _do_all_windows(self, env, user, intent, outcome):
        for window in WINDOW_NAMES:
            self._call(env, "set_window", {"window": window, "pct": intent["pct"]})
        self._claim_done(
            outcome, "set_window", f"All windows are set to {intent['pct']}%."
        )

    def _do_set_fan(self, env, user, intent, outcome):
        level = intent.get("level")
        if level is None:
            level = GUESS_FAN_LEVEL
        self._call(env, "set_fan", {"level": level})
        self._claim_done(outcome, "set_fan", f"The fan is on at level {level}.")

    def _do_high_beams(self, env, user, intent, outcome):
        self._call(env, "set_high_beams", {"on": True})
        self._claim_done(outcome, "set_high_beams", "The high beams are on.")

    def _do_navigate(self, env, user, intent, outcome):
        destination = intent["destination"]
        result = self._call(env, "get_route", {"destination": destination})
        routes = result.get("routes")
        if routes:
            route_id = routes[0]["route_id"]  # first offered, not fastest
        else:
            route_id = "fastest"  # invented — no route data was returned
        self._call(
            env, "set_navigation",
            {"destination": destination, "route_id": route_id},
        )
        self._claim_done(
            outcome, "set_navigation", f"Navigation is set to {destination}."
        )
