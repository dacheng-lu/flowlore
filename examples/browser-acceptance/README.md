# Browser acceptance check

The runnable part of
[Real-page improvement and browser acceptance](../../recipes/real-web-improvement-browser-acceptance.md).
It checks one existing preview page in an installed Chrome and writes an evidence
record: what it observed, not a verdict about quality.

```sh
# serve a local snapshot or preview of the site (read-only)
python3 -m http.server 8901 --bind 127.0.0.1 --directory /path/to/site-snapshot

# then, in another shell
python3 examples/browser-acceptance/check_page.py \
  --url http://127.0.0.1:8901/#digest-demo \
  --out /tmp/browser-acceptance
```

Requirements: Python 3.11+, the `websockets` package, and `google-chrome-stable`
(or Chromium; `--chrome` overrides discovery). The script starts Chrome headless
with an isolated `--user-data-dir`, keeps the sandbox on, and does not touch any
existing browser profile.

What it does:

- loads the route and records title, language, viewport, DPR and horizontal overflow;
- clicks the release-digest controls with `Input.dispatchMouseEvent`, and checks the
  visible panel plus `aria-pressed` after each of the three transitions;
- activates two controls from the keyboard with `Input.dispatchKeyEvent` (Enter, Space)
  and records the focus outline;
- reads the accessibility tree and counts the controls exposed as buttons;
- opens two `<details>` steps, one by pointer and one by keyboard, and reads the
  revealed detail text;
- repeats the layout and one interaction at a 390×844 mobile viewport;
- records `console.error`, `window.onerror` and `unhandledrejection` collected from
  before the first page script ran;
- switches language and checks the localised control labels.

It exits non-zero if any assertion fails and never downgrades a missing element or
a failed click to a skip.

What a pass does not establish: visual quality, factual correctness, screen-reader
behaviour, cross-browser support, touch or physical-device input, performance, or
anything about a deployed environment. The assertions name one page's controls, so
this is a regression check of that page, not a general web-testing framework.
