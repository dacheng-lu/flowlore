# Real-page improvement and browser acceptance

**Status:** draft. This recipe describes a bounded code change against a real site and a
browser check against its local preview. The check below exercises an existing public page;
no source change or defect fix has yet been tested end to end.

**Input:** a source-controlled website, a local start command, one user-visible task with
observable acceptance criteria, and permission to inspect the target page.
**Output:** a focused code diff, a local preview, a browser acceptance record, and evidence
that names the tested route, browser, viewport, interactions, console/page errors, and limits.
**Dependencies:** site source and local build prerequisites; a browser automation interface.
Modern Web Guidance and Chrome DevTools MCP are optional references, not bundled tools.

### Optional Makeextreme snapshot check

The coordinated Makeextreme checkout contains `examples/web_acceptance`, a narrowly scoped
local regression check for the release-digest state selector. From the Makeextreme checkout,
with a trusted site snapshot containing `index.html`, run:

```sh
python3 examples/web_acceptance/new_task.py /path/to/site-snapshot /tmp/web-regression
python3 -m makeextreme run /tmp/web-regression
cat /tmp/web-regression/report.json
```

Only `report.json` with `"status": "pass"` and all checks true satisfies this example. The
checker invokes DOM click handlers in Chromium at two requested window sizes; it does not
exercise physical pointer/keyboard input, verify the rendered viewport, capture screenshots,
check console errors, or establish accessibility. A report of `blocked`, `fail`, or `skipped`
is not a pass. The example does not modify or publish the site. The example is proposed in
[Makeextreme PR #16](https://github.com/dacheng-lu/makeextreme/pull/16); it is not on main.

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
   page errors. Use Chrome DevTools MCP when it is already configured and approved; it can
   inspect a live Chrome session, but it is not itself proof that the acceptance criteria
   passed. Do not attach an authenticated production profile or expose credentials to an
   agent browser.
6. Record each check as `PASS`, `FAIL`, `SKIP`, or `BLOCKED`; save before/after screenshots
   and the changed-file diff. A skipped viewport or inaccessible browser remains unknown.
   Review whether the result is correct in context, not only whether the page rendered.
7. Stop at the local preview. Publishing, changing production data, or enabling a live
   integration is a separate action and needs its own authorization and verification.

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

## Live-page observation (smoke check only)

On 2026-11-14, the public [Dacheng Lu homepage](https://www.dev-lu.com/) was inspected in the
cloud Chrome browser. The related repository snapshot was at revision
`745a5617f57e45219bafc630edde91ee3fac23fe`; whether that exact revision was deployed was not
verified. The Chinese-language homepage loaded. Each of the three
“一个目标，三种视角” accordion controls expanded and exposed its explanatory text and link.
The release-digest state controls changed the visible description through “已检查”, “已改动”
(`旧证据已失效`), and “已恢复” (`已恢复并重新检查`). This was an interactive smoke check of
the deployed page, not a source change, defect fix, keyboard test, responsive test, or
DevTools MCP run. It does not promote this full improvement recipe beyond `draft`.

The Makeextreme snapshot example was also run on the provided local snapshot that day. It
returned `blocked: Chromium exited -6 at 1280x800`; therefore its browser assertions did not
pass. This environment-specific block is recorded as such and must be resolved before using
that script as a successful regression result.

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
browser evidence, and repeat it from a clean checkout with pinned dependencies. Record the
specific browser/runtime versions and distinguish tests actually run from checks only
described here. A production deployment is outside this recipe's acceptance scope.
