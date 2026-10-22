# ADR 002 — Score from the environment's event log, not the agent's story

**Status:** accepted (2026-10-22)

**Context.** An agent's narrative can claim anything.

**Decision.** Every check reads the environment's own state history and
event log. Claims are structured and count-matched against successful
calls.

**Consequences.** Agents must emit structured claims. Argument-level
matching of claims is a planned refinement.
