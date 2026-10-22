# Interview talking points

**The one-liner.** "I built a reliability benchmark for agents: a
simulated car assistant, twenty tasks in three suites, and two agents
that differ only in checking discipline — the unchecked baseline passes
4 of 20 tasks under a strict all-runs metric; the checked agent passes
20 of 20."

**Why final-state scoring is not enough.** "My fan task is the demo:
the baseline sets the wrong level, gets corrected, and ends exactly
right — and still fails, because the wrong intermediate change really
happened. If your eval only inspects final state, production incidents
like that are invisible to you."

**The honesty check.** "Every agent claim is structured and
cross-examined against the environment's event log. On the sabotaged
route task the baseline actually ends in the expected state — its
invented route was rejected — yet the run fails, because it *claimed*
a navigation it never performed. That's the failure mode that erodes
user trust in production, and pure outcome metrics miss it."

**Provenance as a mechanism.** "Instead of prompting the model not to
hallucinate values, I made hallucination unrepresentable: every tool
argument carries a provenance tag, and the dispatch gate rejects
guessed values. The agent is forced onto a resolution ladder —
preference, state, question — which also gives me a scoring axis for
asking too much versus too little."

**Unknown is not off.** "The fog-light task is my favourite interview
story. The sensor says 'unknown'; the policy needs fog established as
safe. The baseline treats unknown as off and turns the beams on. A lot
of production agent bugs are exactly this: absence of evidence quietly
promoted to evidence of absence."

**pass@k vs pass^k.** "I report both. pass@3 rewards a lucky agent;
pass^k is the reliability property enterprises actually buy. With
deterministic scripted agents the two coincide per task, and I test
the math with a deliberately flaky stub — because the distinction
becomes load-bearing the moment an LLM is driving."

**Where an LLM plugs in.** "Deliberately nowhere, yet. The benchmark
isolates architecture from model quality: interpretation is shared, so
the 4-vs-20 gap is attributable to the checker and ledger pattern.
Swapping the scripted interpreter for a model changes one component;
the checker, ledger, and scorer are the production pattern I'd ship
around any model."

**Limitations I volunteer before being asked.** "Scripted user,
scripted agents, twenty hand-written tasks — it's a regression
benchmark, not a quality claim about any real model. The policies are
three rules. The honest scope is: the harness and the failure
taxonomy are the contribution."
