# Bounded zoom-out → one experiment

Status: **draft**. Source files were read on 2026-11-09; method efficacy is not
established. This is an original recipe, not five imported or installed skills.

**Input:** a request, current alternative, constraints, available evidence and authority.
**Output:** a short opportunity brief and one selected falsifiable experiment, or
an explicit blocker with independent preparation completed.

## Decide whether to explore or execute

Use this draft when a process is repeated, a measured bottleneck or unnecessary
steps have been identified, or an architectural choice needs exploration. A
small local fix normally needs no zoom-out. If an existing recipe fits the goal,
input, evidence scope, permissions and acceptance criteria, a person or agent may
prepare its known stages for authorized execution without repeating a full
exploration. Check side effects and recovery first. An absent, incompatible or
out-of-scope recipe, unclear goal, or unknown failure calls for further
exploration. These are decisions for the operator: no automatic routing or
handoff between the projects is implemented by this recipe.

Before choosing a shorter path, write down:

- The requested task and intended outcome, with observable acceptance criteria.
- The steps proposed for removal or consolidation and the evidence that their
  outputs, dependencies and failure handling are covered elsewhere. Uncertainty
  is a reason to test, not proof that a step is unnecessary.
- One primary metric, such as elapsed time, calls, manual actions or cost. An
  ideal lower bound is an estimate unless calculated from stated assumptions;
  distinguish it from the path feasible under current constraints.
- The accepted limitation and the condition that triggers another review. Where
  Longhaul is used, reuse its existing `shortcuts` record rather than inventing
  another ledger.

Keep user requirements, authorization, data integrity, acceptance checks and
necessary recovery controls. Compare alternatives against the same inputs and
acceptance criteria, including the cost of investigation and any rework. Start
with a small reversible experiment where possible; record measured results and
unknowns separately from predictions.

For example, if a documented, applicable recipe already produces the required
artifact, proposing another full planning pass is a candidate for removal. First
confirm its input and version match, checks cover the same outcome and execution
is authorized. If those conditions fail, explore the gap instead. This is a design
example, not a measured speedup or evidence of a cross-project integration.

## Procedure

1. In Longhaul, preserve the request and identify task → beneficiary outcome →
   possible standing system. Name the owner and the question that changes direction.
2. Inspect signals, source/version mapping, reproduction, verification and permission.
   Mark each `have`, `partial` or `missing` with evidence.
3. Use one fitting generative move to produce materially different frames. Evaluate
   them after generation. Include doing less; identify what can stop being built.
4. Compare value, evidence, burden, reversibility and the failure cost. Freeze one
   experiment with baseline, sample, budget and continue/adjust/stop criteria.
5. Configure Makeextreme only if runnable stages are known and authorized. Keep
   execution, evidence and hypothesis result separate. Record failures here before
   promoting anything to a reusable field-tested or verified recipe.

The maintained [protocol](https://github.com/dacheng-lu/longhaul/blob/main/references/zoom-out.md),
[template](https://github.com/dacheng-lu/longhaul/blob/main/references/zoom-out-template.md),
[five-source lineage](https://github.com/dacheng-lu/longhaul/blob/main/references/zoom-out-sources.md)
and [execution handoff](https://github.com/dacheng-lu/makeextreme/blob/main/docs/opportunity-handoff.md)
define the boundaries. No new automatic adapter is claimed.

## Acceptance and failure paths

- A new frame changes the beneficiary, mechanism, unit of value or time horizon;
  three lists of extra features do not count.
- Missing access remains missing. A bigger goal does not grant access or create
  a standing automation. Existing authorization does not need a second approval.
- “10x” needs a metric and baseline; novelty scores are not success probabilities.
- Routine fixes skip this protocol. Default to one short pass, then act.
- Reject or narrow a weak hypothesis; never lower the original success criteria
  to relabel an unsuccessful experiment.

Promotion needs scoped real-task observations, including failed cases and the
current-workflow baseline. Instruction-following spot checks alone do not prove
better outcomes or justify a verified recipe.

## Worked design

[Sensor reliability](sensor-reliability.md) applies this method to RuView and an
unavailable video repository. It demonstrates honest missing-dependency handling
and reframing; no sensor performance has been measured.
