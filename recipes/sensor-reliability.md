# RuView + video: investigate monitoring reliability

Status: **draft / not run**. Reviewed 2026-11-09. This is a proposed experiment,
not an adapter, a deployment or measured evidence of sensor fusion.

**Input:** permission-scoped video events and RF events for the same zone, source
versions, timing metadata, health indicators and independent reference labels.
**Output:** scoped disagreement/health report, comparison against simple baselines,
and an explicit decision to continue, narrow or stop.

## Source and capability boundary

- [RuView](https://github.com/ruvnet/RuView) documents CSI hardware and a simulated
  Docker demo. Reading those documents does not validate sensing accuracy.
- Its [Home Assistant integration](https://github.com/ruvnet/RuView/blob/main/docs/integrations/home-assistant.md)
  documents MQTT publication. At review, its shutdown section says no offline
  publication or MQTT last-will on SIGTERM; retained availability can be stale.
  This is an upstream documentation observation, not a local reproduction.
- [grad5-gmbh/video-ueberwachung](https://github.com/grad5-gmbh/video-ueberwachung)
  returned 404 to the reviewing connection. Existence/access cause, code, license,
  event export, RTSP, MQTT and webhook support are **unknown**. Obtain authorized
  source/docs before choosing an adapter. Do not confuse a custom fixture with
  output from that repository.

## Three levels

- Task: explore combining two projects into something useful and novel.
- Outcome: help an operator recognize unreliable monitoring earlier, with less
  investigation effort and no hidden increase in missed incidents.
- Standing system: a locally evaluated health/disagreement workflow that surfaces
  uncertainty, with an owner, drift checks and bounded retention. Proposed only.

Decision owner: system owner; affected parties: operators and people in the space.
Main tradeoff: extra sensing and maintenance versus demonstrable operator benefit.
Decisive question: does RF contribute information beyond video health checks alone?

## Reframe by their shared function, then examine its limits

Both sources supply imperfect evidence about a space. Vary the amount of visual
observation required instead of starting with “add both detectors together.”

| Frame | Mechanism / changed assumption | What can be removed | Main uncertainty |
| --- | --- | --- | --- |
| Monitoring self-check (first candidate) | Disagreement plus freshness/health cues exposes uncertainty | Extra recognition features and always-confident alerts | Does RF beat camera health checks alone? |
| Analyze video only when useful | Event cues prioritize already-authorized clips, with video-only fallback | Continuous expensive model processing | Does processing fall without increasing missed events? |
| Video as a temporary teacher | Checked visual labels support RF occupancy calibration | Some persistent visual observation after validation | Does RF generalize across time, people and room changes? |

A disagreement is not proof of intrusion, tampering or which source is correct.
The proposed first candidate changes the operator outcome; it need not estimate
identity, body pose or medical signals. The teacher route is research, and visual
labels need independent checking. If a simpler presence sensor or camera-only
diagnostic meets the goal, retaining RuView is not a success requirement.

## Readiness

| Need | Status at review | Next evidence needed |
| --- | --- | --- |
| Signals | partial: RuView docs; no connected devices or video code | Authorized event export + CSI setup |
| Mapping | missing | Zone alignment, source IDs, timestamps, version pins |
| Safe reproduction | partial: offline fixtures can be authored | Labeled logical-clock replay; then controlled real sessions |
| Independent verification | missing for field claims | Session-level reference labels, video-only baseline, held-out comparison |
| Permission | have for analysis/recipe work; missing for live collection | Owner's bounded collection and retention scope before deployment |

## Smallest experiment: first offline, then a separate field decision

**Hypothesis:** freshness-aware diagnostics can flag injected stream failures while
preserving uncertainty. Synthetic success supports protocol mechanics only.

Proposed fixture envelope (our design, **not an upstream API**): source ID, zone ID,
event ID, captured/received time, source kind, occupancy (`present/absent/unknown`),
health, provenance (`synthetic/replay/measured`) and source revision. Define TTL
per source from its documented/observed cadence; retained-message receipt does not
refresh capture time. A source lacking trustworthy timing remains unknown.

- First-session cap: two engineering hours, no hardware purchases, no live data.
- Use a fixed logical clock; fixtures cover fresh agreement, fresh disagreement,
  frozen video, lost RF, both streams lost, retained stale online state, duplicate,
  reordered and future-dated events, plus mismatched zones.
- Compare camera-health-only, RF-only, simple AND/OR and the candidate diagnostic
  policy. AND/OR comparisons must preserve missing/unknown states.
- Offline continue: every predeclared fixture has its expected state and provenance;
  stale or absent evidence never becomes a fresh confident assertion.
- Adjust: a fixture exposes an ambiguity that can be resolved without changing
  the original quality limits; retain the failing input.
- Stop: cap exhausted, required semantics unknowable, or a simpler baseline gives
  the same diagnostic result with less operational burden.
- Exit: keep a report and fixtures; no external alerts or actuators are connected.
- Next action: define the logical-clock fixture expectations before implementing
  a runner. The video-specific adapter remains blocked on source access.

After offline correctness, a **separately scoped field experiment** must compare
the same policies on independently labeled sessions held out by day/person/session,
not randomly adjacent frames. Predeclare sample size, budget and acceptable limits
with the operator before collecting data. Record false alerts/hour, misses, time
to detect a failure, unknown-state fraction and human review minutes separately.
Include correlated failure, lighting changes and people outside the camera's field
but inside RF coverage. Neither input is automatically ground truth.

The field hypothesis is incremental benefit over camera health checks; no sample
or threshold is yet agreed and no field test has run. Do not invent success odds.
If no incremental value appears, keep only the useful diagnostic plumbing.

## Responsibility

Longhaul owns the brief and decision. Makeextreme may execute an explicitly
configured replay under its [handoff contract](https://github.com/dacheng-lu/makeextreme/blob/main/docs/opportunity-handoff.md).
Flowlore keeps this draft and future scoped counterexamples. A signed/hashed
report proves integrity only, not observation accuracy or commercial value.
