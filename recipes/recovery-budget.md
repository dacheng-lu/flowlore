# Recovery budget experiment

Status: **draft**. Synthetic paired evidence is available in Makeextreme; no
real-model gain or universal allocation fraction has been established.

Inputs: the same tasks, acceptance criteria, budgets, outcome traces and measured
costs for both policies. Outputs: completion, spend, unverified-output counts,
recovery costs and documented counterexamples.

- Longhaul records limits and small-probe decisions using `references/recovery-budget.md`.
- Makeextreme supplies `makeextreme.budget` admission checks and the offline
  `examples/recovery_budget/compare.py` experiment. It does not meter API fees.
- FlowLore retains scope, samples, versions and evidence before any promotion.

Run `python examples/recovery_budget/compare.py` from the Makeextreme checkout.
The 16 fixed traces yield 14 completions for both policies, total abstract cost
102 vs 98 and unverified outputs 1 vs 0. The correlated-failure fixture repeats
one all-failure trace across three workers; it is not a real correlation estimate.
No repair process is simulated, so actual recovery costs remain unmeasured.

## Promotion record

For each experiment publish: component commits, task set and sample size, resource
units, estimate versus actual cost, failure taxonomy, maximum observed loss,
recovery cost, human interventions, and the condition under which wider use is
justified. Compare against baseline on the same inputs. Preserve failures and
counterexamples; an improved average cannot hide budget exhaustion or wrong
outputs. A single success never automatically makes a recipe verified.

Test consecutive failures, shared-provider failures, unknown costs, underestimated
costs, and reserves so conservative that useful work is refused. No single
weighted score should merge quality, money and time.

[Kelly's original paper](https://bpb-us-w2.wpmucdn.com/u.osu.edu/dist/7/36891/files/2017/07/Kelly1956-1uwz47o.pdf)
provides the log-growth rationale. Engineering budgets use a bounded-resource
analogy, not literal multiplicative wealth or a universal 25% rule. The video
summary's 93% success figure is not adopted as evidence.

Source copy: Kelly (1956), Bell System Technical Journal 35(4), 917–926;
DOI 10.1002/j.1538-7305.1956.tb03809.x. The linked Ohio State-hosted PDF
reproduces the original paper with AT&T permission.
