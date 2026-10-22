# ADR 001 — Report pass^3, not pass@3

**Status:** accepted (2026-10-22)

**Context.** pass@k rewards luck: one success in three counts.

**Decision.** The headline metric is pass^3 (all three runs pass every
check). pass@3 is shown per task for contrast.

**Consequences.** Today both agents are deterministic, so the two metrics
coincide; the tests verify the math with a deliberately flaky stub so it
holds once an LLM drives the agent.
