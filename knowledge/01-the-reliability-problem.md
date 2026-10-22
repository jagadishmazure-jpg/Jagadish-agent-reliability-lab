# 01 — The reliability problem

A chatbot's output is text. An agent's output is *consequences*: it
calls tools that change the world — a roof opens, a payment posts, an
email sends. That changes what "correct" means. A plausible sentence
("Sure, the sunroof is open") is worthless if the roof never moved, and
dangerous if it moved in a way the rules forbid.

This repo studies one question: **can an agent be trusted to do the
right thing repeatedly, including when the right thing is to stop?**

## The decision at every step

For each user request, the agent repeatedly chooses among four moves:

1. **Act** — it has enough information and permission; execute.
2. **Read** — it lacks a fact the environment can supply (state, a
   stored preference, a sensor reading); fetch it before deciding.
3. **Ask** — the missing fact exists only in the user's head; ask, and
   accept the interruption cost.
4. **Explain a limitation** — the capability, parameter, or evidence
   needed does not exist; say so honestly instead of improvising.

Failures are wrong choices among these four:

- Acting on a **guessed** value (user said "open the sunroof"; agent
  picks 100% because a number was needed).
- Asking when the answer was **already stored** (a preference existed;
  the question was pure interruption).
- Guessing when asking was required (two windows are open; "close the
  window" has no state-resolvable answer).
- **Claiming** success for an action that errored, was never called, or
  was performed by an invented tool.
- Treating a tool's `success` response as task success, when the
  payload omits the very data the next step needs.
- Treating an **unknown** sensor reading as if it were a safe value.
- Reaching the right final state by a **wrong path** — a wrong
  intermediate change later corrected still happened.

## Reliability is a property of repetitions

A single pass proves little. This benchmark runs every task three
times and reports both **pass@3** (at least one pass) and **pass^3**
(all three passes). Reliability is the second number: the correct
behaviour, in the correct order, under the applicable constraints,
every time — including the times the correct behaviour is a question
or an honest refusal.

## Where this benchmark comes from

The design is inspired by published car-assistant reliability
benchmarks (notably the Car-Bench challenge), which evaluate simulated
in-car assistants on ordinary tasks, on tasks with capabilities removed,
and on ambiguous requests. All scenarios, code, and data in this repo
are original; the debt is conceptual: agents should be scored on
intermediate states, honesty, and limitation-admission, not just on
final answers.
