# Real-page improvement and browser acceptance

**Status:** draft. This recipe describes a bounded code change against a real site and a
browser check against its local preview. On 2026-11-14 the *check* half was run against an
existing public page in a real browser; **no source change has yet been made and accepted**
through this recipe, so it does not leave `draft`.

**Input:** a source-controlled website, a local start command, one user-visible task with
observable acceptance criteria, and permission to inspect the target page.
**Output:** a focused code diff, a local preview, a browser acceptance record, and evidence
that names the tested route, browser, viewport, interactions, console/page errors, and limits.
**Dependencies:** site source and local build prerequisites; a browser that can be driven over
the DevTools Protocol, plus the `websockets` package for the bundled check. Modern Web Guidance
and Chrome DevTools MCP are optional references, not bundled tools.

## Executed check (2026-11-14)

This is what was actually run, on which artifacts. It is a check of an **existing** page; it is
not evidence for a code change and not evidence about the deployed site.

| Item | Value |
| --- | --- |
| Browser | `Google Chrome 157.0.8103.38` at `/usr/bin/google-chrome-stable`, `--headless=new`, isolated `--user-data-dir`, sandbox on |
| Site | local copy of a **private** site repository at revision `745a5617f57e45219bafc630edde91ee3fac23fe` (no public commit link exists) |
| Serving | `python3 -m http.server` on `http://127.0.0.1:8901/`, read-only |
| Route | `/#digest-demo` |
| Viewports | 1280×900 window (layout viewport 1280×813, DPR 1) and 390×844 mobile emulation, DPR 3 |
| Verdict | 19 of 19 assertions passed; 0 console errors, 0 page errors |

Commands, in the order they were run:

```sh
# 1. snapshot the site into a working directory and pin the revision
rsync -a --exclude .git ~/Projects/dev-lu.com/ site/
git -C ~/Projects/dev-lu.com rev-parse HEAD     # 745a5617f57e45219bafc630edde91ee3fac23fe

# 2. serve that snapshot read-only
cd site && python3 -m http.server 8901 --bind 127.0.0.1

# 3. drive the installed Chrome and write the evidence record
python3 examples/browser-acceptance/check_page.py \
  --url http://127.0.0.1:8901/#digest-demo \
  --out /tmp/browser-acceptance
```

The check uses `Input.dispatchMouseEvent` and `Input.dispatchKeyEvent` — real input dispatch to
the renderer, not `HTMLElement.click()`. It exits non-zero if any assertion fails and does not
turn a missing element into a skip. Observed:

- **Pointer.** Clicking `changed`, `restored` then `checked` each left exactly one panel visible
  with the matching `aria-pressed="true"`; the visible state strings were `REPORT CHECKED`,
  `OLD EVIDENCE IS STALE`, `RESTORED AND CHECKED AGAIN`.
- **Keyboard.** Focused `2 · Changed`, Enter → `changed` panel. Focused `3 · Restored`, Space →
  `restored` panel. The focused control showed `outline: 3px solid rgb(164, 116, 47)`.
- **Accordion.** A pointer click opened the first `<details>` step; Enter on the third opened it;
  both revealed their detail text.
- **Narrow 390×844.** No horizontal overflow (`scrollWidth` 390 = `innerWidth` 390); the three
  controls stacked at 351×49 px each; a pointer click still changed the panel.
- **Accessibility tree.** Six controls were exposed with role `button`; the digest panels carry
  `aria-pressed` state the tree reports.
- **Errors.** A collector installed with `Page.addScriptToEvaluateOnNewDocument` (before any page
  script) recorded no `console.error`, `window.onerror` or `unhandledrejection` across the run.
- **Language switch.** Selecting `zh` produced `1 · 已检查`, `2 · 已改动`, `3 · 已恢复` and the
  panel states `报告已检查`, `旧证据已失效`, `已恢复并重新检查`, with the error count still 0.

Screenshots for each step and the JSON record are produced by the command above; the run kept a
before/after image per transition, one per viewport, one for the keyboard path, and one for the
Chinese labels.

**Scope of this evidence.** Headless Chrome, one build, synthetic-but-real CDP input rather than
a human hand, no screen reader, no touch hardware, no second browser engine, no deployment. A
pass says these specific assertions held in this browser at these two sizes. It says nothing
about visual quality, factual correctness, accessibility conformance, cross-browser support or
production state.

## Optional Makeextreme snapshot check

The coordinated Makeextreme checkout contains `examples/web_acceptance`, a narrowly scoped local
regression check for the release-digest state selector. From the Makeextreme checkout, with a
trusted site snapshot containing `index.html`:

```sh
python3 examples/web_acceptance/new_task.py /path/to/site-snapshot /tmp/web-regression
python3 -m makeextreme run /tmp/web-regression
cat /tmp/web-regression/report.json
python3 -m makeextreme run /tmp/web-regression  # unchanged successful output is skipped
```

This block is **pending integration**: it exists only on
[Makeextreme PR #16](https://github.com/dacheng-lu/makeextreme/pull/16) (branch
`codex/web-regression-example`, head `d3b0bc175f7c60ece2eebc5ad22f567c1d87a225` at the time of
writing), not on `main`. It is reproduced here so the two can be reconciled when the PR lands;
re-read that PR before relying on it, and note that the commands and file layout may change
while it is a draft.

Run on 2026-11-14 against that PR head, with a snapshot of the same site revision and the same
four commands, it returned `"status": "pass"` with both viewports (`1280×800`, `390×844`) and all
three states `ok`. Two qualifications matter:

- the probe resolves a browser from `chromium`, `chromium-browser`, `google-chrome` in that
  order, so it used `/usr/sbin/chromium` **155.0.8059.84**, a different build from the Chrome
  157.0.8103.38 used above;
- it invokes DOM click handlers in the page, not pointer or keyboard input, and it does not
  verify rendering, screenshots, console errors or accessibility.

So it corroborates the state-selector logic and nothing about input, layout or the broader
acceptance criteria above. A `blocked` result (browser launch failure or timeout) is not a pass;
neither is `fail` or `skipped`.

## Procedure

1. Write one user task and its expected result before editing. Identify the page, relevant
   controls, supported languages/viewports, and the behaviors explicitly out of scope.
2. Read the site's conventions and trace the existing implementation. Record the starting
   commit and take a baseline screenshot. Do not treat text extraction alone as visual proof.
3. If Modern Web Guidance is available in the coding environment, retrieve a focused guide
   for the change (for example, accessibility, CSS layout, or browser APIs). Record its
   version and guide identifier. Apply it as advice; keep project-specific patterns and
   observed browser behavior as the deciding evidence. Do not install an unreviewed skill
   or run an unpinned remote installer as part of this recipe.
4. Make the smallest code change that satisfies the stated task. Keep factual copy tied to
   source material and preserve existing URL, language, and keyboard behavior unless the
   task requires changing them.
5. Start the site's local preview using its documented command. In a clean browser context,
   open the exact route and exercise the acceptance steps using visible controls. Check the
   relevant accessibility tree, keyboard operation, narrow layout, console errors, and
   page errors. [The bundled check](../examples/browser-acceptance/README.md) does this for one page;
   adapt its assertions rather than trusting its default verdict. Use Chrome DevTools MCP
   when it is already configured and approved; it can inspect a live Chrome session, but it
   is not itself proof that the acceptance criteria passed. Do not attach an authenticated
   production profile or expose credentials to an agent browser.
6. Record each check as `PASS`, `FAIL`, `SKIP`, or `BLOCKED`; save before/after screenshots
   and the changed-file diff. A skipped viewport or inaccessible browser remains unknown.
   Review whether the result is correct in context, not only whether the page rendered.
7. Stop at the local preview. Publishing, changing production data, or enabling a live
   integration is a separate action and needs its own authorization and verification.

**Optional checkpoint.** [Longhaul PR #14](https://github.com/dacheng-lu/longhaul/pull/14)
documents the checkpoint-and-recovery handoff for this kind of work: record the requested page,
scope, revisions and acceptance criteria before the run, then register the checked deliverable
and its observation afterwards. That document is also a draft and is not on `main`; this round
did not exercise it, so treat the handoff as **pending integration** as well.

## Acceptance

- Every requested interaction reaches its stated result by pointer and keyboard where
  applicable.
- The targeted content is readable and usable at the recorded desktop and narrow widths;
  no unintended horizontal overflow appears.
- No new console or uncaught page errors occur on the exercised route.
- Screenshots, browser details, exact route, code revision, and all skipped/blocked checks
  are recorded. The scope of any automated accessibility or performance check is named.
- A reviewer can reproduce the local run without production credentials or writes.

Automated checks are evidence for their specific assertions; they do not establish visual
quality, factual correctness, cross-browser support, accessibility conformance, or production
readiness by themselves.

## Earlier live-page observation (not re-run in this round)

On 2026-11-14, in an earlier pass of this work, the public [Dacheng Lu
homepage](https://www.dev-lu.com/) was inspected in a cloud Chrome browser. The related
repository snapshot was at revision `745a5617f57e45219bafc630edde91ee3fac23fe`; whether that
exact revision was deployed was not verified. The Chinese-language homepage loaded, the three
“一个目标，三种视角” accordion controls expanded and exposed their explanatory text and link,
and the release-digest controls changed the visible description through “已检查”, “已改动”
(`旧证据已失效`) and “已恢复” (`已恢复并重新检查`). That was an interactive smoke check of the
deployed page, not a source change, fix, responsive test or DevTools MCP run.

The same earlier pass also ran the Makeextreme snapshot example and got
`blocked: Chromium exited -6 at 1280x800`. That block did not reproduce in the local run above,
which returned `pass`; the earlier record is left here because the failing environment was not
diagnosed, and a block that disappears after an environment change is still an unexplained
result, not a fixed one.

## References

- [Modern Web Guidance](https://developer.chrome.com/docs/modern-web-guidance/) provides
  coding-agent guidance for web-platform practices and browser compatibility.
- [Chrome DevTools for agents](https://developer.chrome.com/docs/devtools/agents/get-started/)
  documents the MCP server for inspecting and controlling a live Chrome session. Browser
  access exposes page content to the agent; use an isolated, non-authenticated test context.
- Existing FlowLore references: [Webapp Testing](../docs/SOURCES.md#web-and-html-agent-skills)
  and [Agent Browser](../docs/SOURCES.md#web-and-html-agent-skills).

## Still needed before promotion

Run this entire procedure on a real source change in a local preview, save the exact diff and
browser evidence, and repeat it from a clean checkout with pinned dependencies. The check half
has run, but the change half has not: without a reviewed diff, "the page still works" is not the
recipe's claim. Then reconcile the two pending integration blocks — Makeextreme PR #16 and
Longhaul PR #14 — against their branches and record which commands were executed against which
revision. Record the specific browser/runtime versions and distinguish tests actually run from
checks only described here. A production deployment is outside this recipe's acceptance scope.
