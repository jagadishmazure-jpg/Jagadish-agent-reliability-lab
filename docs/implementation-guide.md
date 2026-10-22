# Implementation guide

For adopters who want the pattern, not just the benchmark.

## The pattern in five steps

1. **Make the world observable and recordable.** Every state change
   appends a snapshot; every tool call appends an event. If you cannot
   replay what happened, you cannot score it, debug it, or disprove an
   agent's claim about it.
2. **Tag every value with its provenance.** When your agent fills a
   tool argument, record where the value came from: user statement,
   retrieved memory/preference, a fresh state read, a procedure
   constant — or a guess. Policy on guesses is then a one-line check
   instead of a hope.
3. **Put a checker between proposal and dispatch.** Validate, in order:
   the tool exists and accepts these arguments; no argument is a
   guess; executable policies pass against live state (including
   confirmations already obtained and sensor values that are
   *unknown*, which must not be read as safe). Return diagnostics, not
   booleans, so the agent can revise intelligently.
4. **Bound the revision loop.** A blocked proposal may be revised a
   small fixed number of times (insert the missing preparatory step,
   ask the pending question). After that, the agent owes the user an
   explanation, not another attempt.
5. **Generate the report from an executed-action ledger.** The final
   message is a rendering of what actually ran and what it returned.
   Intentions, plans, and rejected proposals are not reportable facts.

## Adding a task

Tasks are data in `tasks/definitions.py`. A task needs: an initial
state, the user's turns as structured intents, scripted answers and
confirmations, and expectations — the final-state subset, required
tools, ask/no-ask keys, an explanation key if the task is impossible,
and any intermediate-state rules. Sabotage is declarative:
`remove_tools`, `remove_params`, `degrade_tools`, `fail_tools`.

## Adding an agent

Implement `handle_turn(env, user, intent, outcome)` and
`finish(env, outcome)`. Read state and preferences through
`env.execute(...)`, ask via `user.ask(key)`, confirm via
`user.confirm(key)`, and record what you claim in
`outcome.claims` — the scorer will check every claim against the event
log. To plug in an LLM agent, let the model produce the intents and
proposed calls, but keep the checker and the ledger: they are the
parts that make the model's output safe to act on and honest to
report.

## Running

```bash
python3 -m pytest tests/ -q          # 72 deterministic tests, offline
python3 scripts/run_benchmark.py     # both agents, 20 tasks x 3 runs
```

No dependencies beyond the Python 3.12 standard library.
