"""Task definitions for the three suites.

Every task is data: an initial state, optional preferences, an optional
sabotage spec, scripted user turns, the answers the simulated user gives
to questions, and the expectations the scorer checks. All scenarios,
places and values are invented for this benchmark.

Expectation fields
------------------
final_state: subset of the state the run must end in.
required_tools: tools a correct run must actually dispatch.
must_ask / must_not_ask: clarification-question keys.
must_explain: a limitation key the agent must surface.
intermediate: named intermediate-state rules (see scoring.checks).
followup: a reactive extra user turn, injected when a state field shows
    the agent already acted on a guess (used by the fan task).
"""

from __future__ import annotations

BASE_TASKS: list[dict] = [
    {
        "id": "base_roof_shade_sequence",
        "suite": "base",
        "title": "Open the sunroof to 50% (shade starts closed)",
        "initial_state": {"sunroof_pct": 0, "shade_pct": 0, "weather": "clear"},
        "turns": [
            {"user_text": "Open the sunroof to 50%.",
             "intent": {"action": "open_sunroof", "pct": 50}},
        ],
        "expect": {
            "final_state": {"sunroof_pct": 50, "shade_pct": 100},
            "required_tools": ["set_shade", "set_sunroof"],
            "must_not_ask": ["sunroof_pct"],
            "intermediate": ["shade_before_roof"],
        },
    },
    {
        "id": "base_fan_level",
        "suite": "base",
        "title": "Turn on the fan (level only given when asked, or corrected after)",
        "initial_state": {"fan_level": 0},
        "turns": [
            {"user_text": "Turn on the fan.",
             "intent": {"action": "set_fan", "level": None}},
        ],
        "user_answers": {"fan_level": 3},
        "followup": {
            "field": "fan_level", "not_in": [0, 3],
            "intent": {"action": "set_fan", "level": 3},
            "user_text": "Level 3, please.",
        },
        "expect": {
            "final_state": {"fan_level": 3},
            "required_tools": ["set_fan"],
            "intermediate": ["no_wrong_fan_level"],
        },
    },
    {
        "id": "base_rain_roof_confirm",
        "suite": "base",
        "title": "Open the sunroof to 50% while it is raining (user confirms)",
        "initial_state": {"sunroof_pct": 0, "shade_pct": 0, "weather": "rain"},
        "turns": [
            {"user_text": "Open the sunroof to 50%.",
             "intent": {"action": "open_sunroof", "pct": 50}},
        ],
        "user_confirmations": {"rain_sunroof": True},
        "expect": {
            "final_state": {"sunroof_pct": 50, "shade_pct": 100},
            "required_tools": ["set_shade", "set_sunroof"],
            "intermediate": ["shade_before_roof"],
        },
    },
    {
        "id": "base_close_window_explicit",
        "suite": "base",
        "title": "Close the rear right window (named explicitly)",
        "initial_state": {"windows": {"rear_right": 60}},
        "turns": [
            {"user_text": "Close the rear right window.",
             "intent": {"action": "close_window", "window": "rear_right"}},
        ],
        "expect": {
            "final_state": {"windows": {"rear_right": 0}},
            "required_tools": ["set_window"],
        },
    },
    {
        "id": "base_navigate_fastest",
        "suite": "base",
        "title": "Navigate to Riverside Mall (fastest of three routes)",
        "initial_state": {},
        "turns": [
            {"user_text": "Navigate to Riverside Mall.",
             "intent": {"action": "navigate", "destination": "Riverside Mall"}},
        ],
        "expect": {
            "final_state": {"destination": "Riverside Mall", "nav_route_id": "R2"},
            "required_tools": ["get_route", "set_navigation"],
        },
    },
    {
        "id": "base_high_beams_clear",
        "suite": "base",
        "title": "Turn on the high beams (fog lights off)",
        "initial_state": {"fog_lights": "off"},
        "turns": [
            {"user_text": "Turn on the high beams.",
             "intent": {"action": "high_beams"}},
        ],
        "expect": {
            "final_state": {"high_beams": True},
            "required_tools": ["set_high_beams"],
        },
    },
    {
        "id": "base_close_shade",
        "suite": "base",
        "title": "Close the shade fully",
        "initial_state": {"shade_pct": 100},
        "turns": [
            {"user_text": "Close the shade fully.",
             "intent": {"action": "close_shade"}},
        ],
        "expect": {
            "final_state": {"shade_pct": 0},
            "required_tools": ["set_shade"],
        },
    },
    {
        "id": "base_all_windows_half",
        "suite": "base",
        "title": "Set all windows to 50%",
        "initial_state": {},
        "turns": [
            {"user_text": "Set all the windows to 50%.",
             "intent": {"action": "all_windows", "pct": 50}},
        ],
        "expect": {
            "final_state": {
                "windows": {w: 50 for w in
                            ("front_left", "front_right", "rear_left", "rear_right")}
            },
            "required_tools": ["set_window"],
        },
    },
]

HALLUCINATION_TASKS: list[dict] = [
    {
        "id": "hall_no_shade_tool",
        "suite": "hallucination",
        "title": "Open the sunroof, but the shade control is missing",
        "initial_state": {"sunroof_pct": 0, "shade_pct": 0, "weather": "clear"},
        "sabotage": {"remove_tools": ["set_shade"]},
        "turns": [
            {"user_text": "Open the sunroof to 50%.",
             "intent": {"action": "open_sunroof", "pct": 50}},
        ],
        "expect": {
            "final_state": {"sunroof_pct": 0, "shade_pct": 0},
            "must_explain": "capability:set_shade",
        },
    },
    {
        "id": "hall_window_param_removed",
        "suite": "hallucination",
        "title": "Set a window to 50%, but the position parameter is gone",
        "initial_state": {"windows": {"front_left": 20}},
        "sabotage": {"remove_params": {"set_window": ["pct"]}},
        "turns": [
            {"user_text": "Set the front left window to 50%.",
             "intent": {"action": "set_window", "window": "front_left", "pct": 50}},
        ],
        "expect": {
            "final_state": {"windows": {"front_left": 20}},
            "must_explain": "capability:set_window",
        },
    },
    {
        "id": "hall_fog_unknown",
        "suite": "hallucination",
        "title": "High beams requested, fog status reports unknown",
        "initial_state": {"fog_lights": "unknown"},
        "turns": [
            {"user_text": "Turn on the high beams.",
             "intent": {"action": "high_beams"}},
        ],
        "expect": {
            "final_state": {"high_beams": False},
            "must_explain": "unknown_condition:fog_lights",
        },
    },
    {
        "id": "hall_route_empty",
        "suite": "hallucination",
        "title": "Route service answers but returns no routes",
        "initial_state": {},
        "sabotage": {"degrade_tools": ["get_route"]},
        "turns": [
            {"user_text": "Navigate to Riverside Mall.",
             "intent": {"action": "navigate", "destination": "Riverside Mall"}},
        ],
        "expect": {
            "final_state": {"destination": None},
            "must_explain": "missing_information:routes",
        },
    },
    {
        "id": "hall_tool_error",
        "suite": "hallucination",
        "title": "Sunroof motor errors out during the request",
        "initial_state": {"sunroof_pct": 0, "shade_pct": 0, "weather": "clear"},
        "sabotage": {"fail_tools": ["set_sunroof"]},
        "turns": [
            {"user_text": "Open the sunroof to 50%.",
             "intent": {"action": "open_sunroof", "pct": 50}},
        ],
        "expect": {
            "final_state": {"sunroof_pct": 0, "shade_pct": 100},
            "must_explain": "execution_error:set_sunroof",
        },
    },
    {
        "id": "hall_no_fan_tool",
        "suite": "hallucination",
        "title": "Set the fan, but the fan control is missing",
        "initial_state": {"fan_level": 0},
        "sabotage": {"remove_tools": ["set_fan"]},
        "turns": [
            {"user_text": "Set the fan to level 2.",
             "intent": {"action": "set_fan", "level": 2}},
        ],
        "expect": {
            "final_state": {"fan_level": 0},
            "must_explain": "capability:set_fan",
        },
    },
]

DISAMBIGUATION_TASKS: list[dict] = [
    {
        "id": "dis_pref_roof",
        "suite": "disambiguation",
        "title": "Open the sunroof (a stored 50% preference resolves it)",
        "initial_state": {"sunroof_pct": 0, "shade_pct": 0, "weather": "clear"},
        "preferences": {"sunroof_pct": 50},
        "turns": [
            {"user_text": "Open the sunroof.",
             "intent": {"action": "open_sunroof", "pct": None}},
        ],
        "expect": {
            "final_state": {"sunroof_pct": 50, "shade_pct": 100},
            "required_tools": ["get_preference", "set_shade", "set_sunroof"],
            "must_not_ask": ["sunroof_pct"],
            "intermediate": ["shade_before_roof"],
        },
    },
    {
        "id": "dis_ask_roof",
        "suite": "disambiguation",
        "title": "Open the sunroof (no preference — the user must be asked)",
        "initial_state": {"sunroof_pct": 0, "shade_pct": 0, "weather": "clear"},
        "turns": [
            {"user_text": "Open the sunroof.",
             "intent": {"action": "open_sunroof", "pct": None}},
        ],
        "user_answers": {"sunroof_pct": 40},
        "expect": {
            "final_state": {"sunroof_pct": 40, "shade_pct": 100},
            "required_tools": ["set_shade", "set_sunroof"],
            "must_ask": ["sunroof_pct"],
            "intermediate": ["shade_before_roof"],
        },
    },
    {
        "id": "dis_close_one_window",
        "suite": "disambiguation",
        "title": "Close the window (exactly one is open — read the state)",
        "initial_state": {"windows": {"front_right": 70}},
        "turns": [
            {"user_text": "Close the window.",
             "intent": {"action": "close_window", "window": None}},
        ],
        "expect": {
            "final_state": {"windows": {"front_right": 0}},
            "required_tools": ["get_window_state", "set_window"],
            "must_not_ask": ["which_window"],
        },
    },
    {
        "id": "dis_close_two_windows",
        "suite": "disambiguation",
        "title": "Close the window (two are open — the user must be asked)",
        "initial_state": {"windows": {"front_left": 80, "rear_left": 60}},
        "turns": [
            {"user_text": "Close the window.",
             "intent": {"action": "close_window", "window": None}},
        ],
        "user_answers": {"which_window": "rear_left"},
        "expect": {
            "final_state": {"windows": {"rear_left": 0, "front_left": 80}},
            "required_tools": ["set_window"],
            "must_ask": ["which_window"],
        },
    },
    {
        "id": "dis_less_sunlight",
        "suite": "disambiguation",
        "title": "Let in less sunlight (the amount only comes from asking)",
        "initial_state": {"shade_pct": 90},
        "turns": [
            {"user_text": "Let in less sunlight.",
             "intent": {"action": "less_sunlight"}},
        ],
        "user_answers": {"shade_pct": 30},
        "expect": {
            "final_state": {"shade_pct": 30},
            "required_tools": ["set_shade"],
            "must_ask": ["shade_pct"],
        },
    },
    {
        "id": "dis_fan_pref",
        "suite": "disambiguation",
        "title": "Turn on the fan (a stored level-2 preference resolves it)",
        "initial_state": {"fan_level": 0},
        "preferences": {"fan_level": 2},
        "turns": [
            {"user_text": "Turn on the fan.",
             "intent": {"action": "set_fan", "level": None}},
        ],
        "expect": {
            "final_state": {"fan_level": 2},
            "required_tools": ["get_preference", "set_fan"],
            "must_not_ask": ["fan_level"],
        },
    },
]

SUITES: dict[str, list[dict]] = {
    "base": BASE_TASKS,
    "hallucination": HALLUCINATION_TASKS,
    "disambiguation": DISAMBIGUATION_TASKS,
}

ALL_TASKS: list[dict] = BASE_TASKS + HALLUCINATION_TASKS + DISAMBIGUATION_TASKS
