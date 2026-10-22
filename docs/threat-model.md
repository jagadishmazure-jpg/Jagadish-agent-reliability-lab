# Threat model — agent reliability lab

Scope: the simulated car environment, the two agents, the pre-execution
checker and the scorer. Assets: the integrity of the benchmark score and
the safety policies of the simulated car.

## STRIDE (applied to the benchmark and the agent)

| Threat | Example | Control | Residual risk |
| --- | --- | --- | --- |
| Spoofing | Agent asserts a value the user never gave | Checker requires value provenance (user, preference or tool read) | — |
| Tampering | Agent edits its own report after the fact | Final report is generated from the executed-action ledger; scorer reads the environment event log | — |
| Repudiation | "Done" with no executed call | Honesty check: each done claim needs its own successful call (count-matched) | Claims are matched by tool, not arguments |
| Information disclosure | n/a — no personal data | Fictional car, city and users | — |
| Denial of service | Removed or failing tools | Sabotage suite: agent must explain the limitation, not loop or pretend | — |
| Elevation of privilege | Opening the roof through a closed shade, beams on in fog | Policy checks across the whole state history, not just the final state | Policies are hand-written rules |

## OWASP LLM Top 10 (relevant items)

- **LLM06 Excessive agency** — pre-execution checker gates every call.
- **LLM09 Misinformation** — honesty and conversation checks score false
  success claims and missing explanations.
