# 04 — Architecture

## Components

```text
tasks/definitions.py     20 tasks as data (state, sabotage, script, expectations)
        |
tasks/runner.py          fresh env + scripted user + agent per run
        |
   +----+-------------+------------------+
   |                  |                  |
agents/naive.py   agents/reliable.py   carenv/
 (intends,        (resolves, checks,    state.py   observable state + history
  guesses,         ledgers, reports     tools.py   registry + sabotage
  claims)          from reality)        policies.py executable rules
                       |                user.py    scripted answers/confirms
                agents/checker.py
                capability / provenance / policy
        |
scoring/checks.py        six per-run checks over history + event log
scoring/suite.py         3 runs per task -> pass@3, pass^3, reports
```

## Data flow of one reliable-agent turn

1. The runner hands the agent a structured intent for the user turn.
2. The agent resolves missing values: preference store → live state →
   clarifying question (each answer tagged with its provenance).
3. For weather-sensitive or state-dependent actions it reads the
   relevant sensors first; a rain warning obtains a confirmation that
   is written into the event log *before* any roof call.
4. Each proposed mutation goes through the checker. Blocks return
   diagnostics; a bounded revision loop may insert preparatory steps.
5. Executed calls append to the ledger with their true results; the
   environment appends its own snapshots and event log entries —
   two independent records the scorer can compare.
6. At the end, claims and the user-facing message are generated from
   the ledger and the explanations list, and nothing else.

## Design decisions worth arguing with

- **Shared interpretation.** Both agents parse turns identically. The
  benchmark claims the reliability difference comes from checking and
  reporting discipline; giving the reliable agent a smarter parser
  would confound that claim.
- **The environment does not enforce policy.** Real cars have some
  interlocks, but if the environment blocked policy violations, no
  agent could ever commit one and there would be nothing to measure.
  Enforcement lives in the agent's checker; detection lives in the
  scorer.
- **Two records, kept apart.** Proposals, the ledger, the environment's
  event log, and the state history are separate structures. Most checks
  are cross-record comparisons; collapsing them into one "transcript"
  would let an agent's own narration serve as its evidence.
- **Deterministic first.** No LLM is in the loop, so results are
  exactly reproducible and the failure taxonomy is attributable to
  architecture, not sampling. The interfaces (intent in, proposed
  calls through the checker, ledger out) are where a model-driven
  agent plugs in unchanged.
