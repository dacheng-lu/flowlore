# Frontier prompt → cheap builder: asset-pack workflow

**Status:** `field-tested` on one pack (2026-11-10), not `verified`.

This is a workflow note for a recurring pattern: use a frontier model for the
asset contract and prompt, a cheaper model for production, and a deterministic
validator plus a human visual gate before integration. It is not a bundled
skill, generator or workflow engine.

## Input → output

**Input:** a UI need, a fixed asset contract (IDs, canvas, frames, palette,
format, forbidden geometry), and a visual reference.

**Output:** a normalized asset pack, a JSON manifest, a validator report, a
rendered contact sheet and a live integration screenshot.

## Roles

| Role | Model / tool | Constraint |
|---|---|---|
| Prompt author | `gpt-6-astra` or `fable5.2` | lowest supported effort; prompt only |
| Builder | `kimi-k3.1-pro:cloud` | raw output; no design decisions |
| Integrator | coding agent | maps task/status to IDs; preserves approved base |
| Verifier | validator + browser | parse, palette, geometry, occlusion, screenshot |

`gpt-6-astra` accepts `low`, `medium`, `high`, `xhigh` and `max`; it rejects
`minimal`. Record the exact model string and effort in the prompt artifact.

## Procedure

1. Write the contract before asking a model. Name every ID and the exact
   rectangle/occlusion rules. Acceptance: no unresolved visual choice.
2. Ask the frontier model for a self-contained builder prompt and one
   validation sentence. Do not ask it to generate the assets.
3. Run the builder once with a clean prompt. Save stdout/stderr; reject prose,
   fences and partial packs.
4. Normalize to one file per ID plus a manifest. Acceptance: manifest keys equal
   file IDs and frame IDs resolve.
5. Validate deterministically and render at 4×. Check dimensions, palette,
   allowed primitives, screen visibility and character occlusion.
6. Integrate behind a human gate; add a static-serving test and screenshot the
   real UI. A model's "done" is not evidence.

## Evidence (2026-11-10)

- Frontier prompt: `gpt-6-astra`, `low` effort.
- Builder: `kimi-k3.1-pro:cloud`, 8 SVG scenes at 96×64.
- Pack: 52×20 screen (2.6:1), task layouts `code/research/ops/review/unspecified`,
  generic `idle/unknown/done-empty`.
- Validator: 8/8 roots, 96×64, palette subset, only rects, no forbidden tags.
- Integration: Agent Office commit `142ae7d` (pack) and `093ed80` (UI mapping).
- Not exercised: other frontier models, other asset formats, licensing review,
  a second independent builder, or a reproducible pinned model snapshot.

## Failure modes

- **Frontier model designs the assets too.** Keep the contract in the prompt
  file; the builder may only execute it.
- **Builder silently changes a previously approved part.** Keep the approved
  base and change one region; record the rejected pass.
- **Screen is angled or hidden.** Require a front-elevation rectangle and check
  that no character pixel enters the screen rectangle.
- **Left arm appears outside the torso.** Rear 3/4 is not enough; check the
  rendered frame for skin outside the jacket silhouette.
- **Manifest/SVG drift.** Normalize IDs and re-run the validator; never trust a
  model-generated manifest without comparing keys.

## Related

- Longhaul checkpoint shape: `longhaul/docs/asset-pipeline.md`
- Makeextreme stage template: `makeextreme/docs/asset-pipeline.md`
- Hermes skill: `frontier-prompt-asset-pipeline`
