# Design workflows for agent-built pages

Three original recipe drafts, inspired by upstream projects. They are references, not installed
skills or tested integrations. Review upstream instructions and license before use; pin a
revision and inspect any scripts or dependencies before running them. None of these recipes
has been executed or verified in FlowLore.

## Landing-page brief and structure

**Source:** [AI Design Skills](https://github.com/elayadesign/ai-design-skills) · **Status:** draft

**Input:** audience, problem, evidence, desired action, brand constraints and available content.
**Output:** a page brief, section outline and draft copy with claims linked to evidence.
**Dependencies:** a compatible coding agent and a reviewed upstream skill, if used; an existing
site and its design constraints when modifying one.

1. Identify the reader and the concrete action they can take. Mark unsupported claims as unknown.
2. Outline the opening benefit, problem, process, evidence, questions and action; adapt the order to the content.
3. Build from actual copy and assets; review with the owner before publishing.

**Example:** for a release digest, explain who it helps, show a sample report and link to the
runnable offline example. Do not imply live automation exists.
**Acceptance:** every claim has a source; the primary action works; headings and content make
sense on mobile and with keyboard navigation. Still needed: a reproducible page and review record.

## Interface critique and polish

**Source:** [Impeccable](https://github.com/pbakaus/impeccable) · **Status:** draft

**Input:** an existing page, brand rules and a list of user tasks. **Output:** a prioritized
critique, revised page and before/after observations. **Dependencies:** source access, a browser,
and a reviewed compatible agent skill if used.

1. Capture the current desktop and mobile views; record task and accessibility problems.
2. Review hierarchy, typography, spacing and interaction against the existing brand.
3. Make focused changes, test navigation, focus, reduced motion and narrow screens; compare results.

**Example:** improve a project page so the first action and project limitations are visible.
**Acceptance:** links and keyboard controls work, no horizontal overflow, text remains readable,
and changes preserve brand and factual claims. Automated detectors are signals, not proof of design quality.
Still needed: pinned tool version, before/after screenshots and independent review.

## Interactive system explanation

**Source:** [Anatomy](https://github.com/wheresryan22/anatomy) · **Status:** draft

**Input:** a documented process, intended audience, source material and a precise interaction.
**Output:** an accessible interactive illustration and static fallback. **Dependencies:** reviewed
source data, a compatible agent skill if used, and browser testing on target devices.

1. Define what the model shows and where it simplifies reality; cite the evidence.
2. Create a small interactive diagram driven by explicit states and provide a textual equivalent.
3. Check state transitions, keyboard access, mobile layout and reduced-motion behavior.

**Example:** visualize a report changing after a check and needing a fresh observation, with links
to the underlying offline test. Label the presentation as a simulation.
**Acceptance:** each state matches the cited example; controls and labels work without a mouse;
the static explanation remains useful without scripts. A visual is not proof of the underlying
mechanism. Still needed: reproducible artifact, source revision and independent domain review.
