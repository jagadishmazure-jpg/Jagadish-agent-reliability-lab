# 03 — Pre-execution checks and honest claims

The reliable agent's architecture rests on one move: **separate the
proposal from the commitment.** The interpretation layer proposes tool
calls; nothing reaches the car until a checker — ordinary, inspectable
code — approves the specific call. Four kinds of checks, in order:

## 1. Capability

Does the tool exist in the registry *as currently advertised*, and does
it accept exactly these parameters with in-range values? This single
check converts two hallucination classes from runtime confusion into
clean, explainable blocks: removed tools and removed parameters are
discovered before dispatch, so the agent can tell the user precisely
which capability is missing instead of narrating around an error.

## 2. Provenance

Every argument value carries a tag: `user` (stated in this
conversation), `preference` (retrieved from the store), `state` (read
from the car), `constant` (fixed by the procedure, like "close = 0"),
or `guess`. A guessed value for any parameter blocks the call. This is
the mechanical form of "don't invent inputs": the agent is forced onto
the resolution ladder — preferences, then state, then a question —
because the cheap path (making a number up) is closed.

## 3. Policy

Executable rules evaluated against live state and the conversation so
far: the shade must already be open before the roof moves; rain
requires a recorded confirmation; high beams require the fog condition
to be *established as safe*, which an `unknown` reading cannot do.
Policy blocks come with diagnostics, and the agent may revise a
bounded number of times — the shade block is routinely revised by
performing the preparatory step — after which it must stop and explain
rather than loop or bulldoze.

## 4. Claim verification

Checks 1–3 guard what leaves the agent. This one guards what the agent
*says afterwards*. The agent keeps an executed-action ledger: only
calls that actually ran, with their real results. A rejected proposal
is not an action and never enters it. The final report is generated
from the ledger, so:

- a tool that errored is reported as failed, in the same sentence
  pattern as a success is reported as done;
- an action blocked by the checker cannot be claimed at all;
- the scorer independently cross-checks every "done" claim against the
  environment's event log (`honesty` check), so even the reporting code
  is itself under test.

## Why checks are code, not another model

The semantic residue — did the user *mean* to confirm? — genuinely
needs judgement, and an LLM-driven deployment would put a narrow model
call there. But existence, parameter shape, ranges, value provenance,
and the policies in this benchmark are exact questions with exact
answers. Answering exact questions with a probabilistic component is
how "the tool returned success" becomes "the task succeeded" in an
agent's final message. Keep the deterministic parts deterministic;
spend model judgement only where judgement is the actual problem.
