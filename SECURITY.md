# Security policy

## Scope

This is a portfolio learning project. It runs fully offline against a
simulated car and fictional data: there are no live services, no
credentials, no real vehicles, and no real customer data anywhere in
the repo.

## Safety properties (tested, not just documented)

- The reliable agent cannot dispatch a tool call whose argument values
  were guessed: the pre-execution checker blocks untagged/invented
  values by construction, and tests assert the block.
- A rejected proposal is never recorded as an executed action; the
  final report is generated from the executed-action ledger only, so
  the agent cannot claim an action that did not run.
- Policy checks (shade-first, rain confirmation, fog/high-beams) are
  enforced before execution and re-verified by the scorer over the
  recorded history and event log.
- An "unknown" sensor value is treated as *unestablished*, never as a
  safe value.

## Reporting a vulnerability

Open a GitHub issue in this repository describing the problem. As this
is a simulation with no production deployment, there is no embargo
process; fixes land as ordinary commits.
