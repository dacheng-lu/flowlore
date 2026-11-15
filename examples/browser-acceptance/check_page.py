#!/usr/bin/env python3
"""Browser acceptance check for one local preview page, in the installed Chrome.

This is the runnable part of
[the browser-acceptance recipe](../../recipes/real-web-improvement-browser-acceptance.md).
It opens one URL in Google Chrome through the DevTools Protocol, uses an isolated
profile, keeps the browser sandbox on, dispatches real mouse and keyboard input
(Input.dispatchMouseEvent / Input.dispatchKeyEvent — not HTMLElement.click()),
and records what it observed as JSON plus screenshots.

It is written against the dev-lu.com release-digest selector, so the interaction
assertions name that page's controls. Everything else (viewport, overflow, focus
ring, console/page errors, accessibility roles) is generic.

Requirements: Python 3.11+, the `websockets` package, and an installed Chrome.
Linux/macOS; no network access is needed beyond the local preview.

    python3 examples/browser-acceptance/check_page.py --url http://127.0.0.1:8901/ --out /tmp/acc

Exit code 0 only when every assertion passes. A failing assertion or a missing
element is reported, never silently skipped.

What a pass does NOT prove: visual quality, factual correctness, real assistive
technology behaviour, cross-browser support, touch input, or production state.
It observes one browser build at the two recorded viewport sizes.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

CHROME_CANDIDATES = ("/usr/bin/google-chrome-stable", "google-chrome-stable", "google-chrome", "chromium")

COLLECT = r"""
(() => {
  const errs = [];
  window.__acceptance = {errors: errs, console: []};
  const push = (kind, msg) => errs.push({kind: kind, message: String(msg), t: Date.now()});
  const origError = console.error.bind(console);
  console.error = function (...a) { push('console.error', a.map(String).join(' ')); origError(...a); };
  console.warn = function (...a) { window.__acceptance.console.push({kind: 'warn', message: a.map(String).join(' ')}); };
  window.addEventListener('error', e => push('window.error', (e.message || '') + ' @' + (e.filename || '') + ':' + (e.lineno || 0)));
  window.addEventListener('unhandledrejection', e => push('unhandledrejection', String(e.reason)));
})();
"""

BOX = r"""
(() => {
  const el = document.querySelector(%s);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  return {x: r.x + r.width / 2, y: r.y + r.height / 2, w: r.width, h: r.height,
          top: r.top, left: r.left};
})()
"""

SCROLL = r"""
(() => {
  const e = document.querySelector(%s);
  if (!e) return null;
  e.scrollIntoView({block: 'center', inline: 'center', behavior: 'instant'});
  return true;
})()
"""

PANEL = r"""
(() => {
  const panels = [...document.querySelectorAll('[data-digest-panel]')];
  const buttons = [...document.querySelectorAll('[data-digest]')];
  const shown = panels.filter(p => !p.hidden);
  const state = shown[0] ? shown[0].querySelector('.digest-state') : null;
  return {
    visible: shown.map(p => p.dataset.digestPanel),
    pressed: buttons.filter(b => b.getAttribute('aria-pressed') === 'true').map(b => b.dataset.digest),
    heading: shown[0] ? (shown[0].querySelector('h3') || {}).textContent : null,
    state: state ? state.textContent.trim() : null
  };
})()
"""

OVERFLOW = r"""
(() => ({
  innerWidth: window.innerWidth,
  docScroll: document.documentElement.scrollWidth,
  bodyScroll: document.body.scrollWidth,
  horizontalOverflow: Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) > window.innerWidth
}))()
"""


def find_chrome() -> str:
    for c in CHROME_CANDIDATES:
        p = shutil.which(c) or (c if os.path.isabs(c) and os.path.exists(c) else None)
        if p:
            return p
    sys.exit("no Chrome/Chromium found; install google-chrome-stable or pass --chrome")


class Chrome:
    """Minimal CDP client: one page target, one websocket, synchronous calls."""

    def __init__(self, binary: str, port: int, width: int, height: int):
        self.binary, self.port, self.width, self.height = binary, port, width, height
        self.profile = tempfile.mkdtemp(prefix="acceptance-profile-")
        self.proc = None
        self.ws = None
        self._id = 0

    def __enter__(self):
        args = [self.binary, "--headless=new", f"--user-data-dir={self.profile}",
                f"--remote-debugging-port={self.port}", "--no-first-run",
                "--no-default-browser-check", "--disable-background-networking",
                "--disable-sync", "--disable-extensions", "--mute-audio",
                f"--window-size={self.width},{self.height}", "about:blank"]
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     start_new_session=True)
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                data = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=1))
                pages = [p for p in data if p.get("type") == "page"]
                if pages:
                    self.ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                time.sleep(0.2)
        else:
            raise RuntimeError("Chrome did not expose a DevTools page in time")
        self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._connect())
        return self

    async def _connect(self):
        import websockets
        self.ws = await websockets.connect(self.ws_url, max_size=64 * 1024 * 1024)

    def call(self, method: str, **params):
        self._id += 1
        mid = self._id

        async def go():
            await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
            while True:
                msg = json.loads(await self.ws.recv())
                if msg.get("id") == mid:
                    if "error" in msg:
                        raise RuntimeError(f"{method}: {msg['error']}")
                    return msg.get("result", {})

        return self._loop.run_until_complete(go())

    def navigate(self, url: str, wait_ms: int = 1500):
        self.call("Page.enable")
        self.call("Page.navigate", url=url)
        time.sleep(wait_ms / 1000)

    def js(self, expr: str):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError(r["exceptionDetails"].get("text", "JS error"))
        return r.get("result", {}).get("value")

    def screenshot(self, path: str):
        import base64
        r = self.call("Page.captureScreenshot", format="png")
        with open(path, "wb") as f:
            f.write(base64.b64decode(r["data"]))
        return path

    def box(self, selector: str):
        el = json.dumps(selector)
        if not self.js(SCROLL % el):
            return None
        last = None
        r = None
        for _ in range(40):
            time.sleep(0.05)
            r = self.js(BOX % el)
            if r is None:
                return None
            key = (round(r["x"], 1), round(r["y"], 1))
            if key == last:
                return r
            last = key
        return r

    def click(self, selector: str):
        b = self.box(selector)
        if not b or not b["w"]:
            raise RuntimeError("not clickable: %s -> %r" % (selector, b))
        vw, vh = self.js("[window.innerWidth, window.innerHeight]")
        x, y = b["x"], b["y"]
        if not (0 <= x <= vw and 0 <= y <= vh):
            raise RuntimeError("click target outside viewport: %s at %r" % (selector, (x, y)))
        for t in ("mouseMoved", "mousePressed", "mouseReleased"):
            self.call("Input.dispatchMouseEvent", type=t, x=x, y=y, button="left",
                      clickCount=1, buttons=1 if t == "mousePressed" else 0)
            time.sleep(0.05)
        time.sleep(0.45)
        return {"selector": selector, "x": round(x, 1), "y": round(y, 1)}

    def press(self, key: str, code: str, vk: int):
        for t in ("keyDown", "keyUp"):
            params = {"type": t, "key": key, "code": code,
                      "windowsVirtualKeyCode": vk, "nativeVirtualKeyCode": vk}
            if t == "keyDown" and key == "Enter":
                params["text"] = "\r"
            self.call("Input.dispatchKeyEvent", **params)
            time.sleep(0.05)
        time.sleep(0.25)

    def metrics(self):
        return self.js("({w: innerWidth, h: innerHeight, dpr: devicePixelRatio, "
                       "scrollWidth: document.documentElement.scrollWidth, title: document.title, "
                       "lang: document.documentElement.lang})")

    def __exit__(self, *exc):
        try:
            self._loop.run_until_complete(self.ws.close())
        except Exception:
            pass
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        shutil.rmtree(self.profile, ignore_errors=True)
        self._loop.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", default="http://127.0.0.1:8901/#digest-demo")
    ap.add_argument("--out", required=True, help="evidence directory (JSON + screenshots)")
    ap.add_argument("--port", type=int, default=9223)
    ap.add_argument("--chrome", default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    binary = a.chrome or find_chrome()

    rec = {"url": a.url, "chrome_binary": binary, "chrome_version": None,
           "checks": {}, "screenshots": [], "assertions": []}

    def expect(name, cond, detail=""):
        rec["assertions"].append({"assertion": name, "result": "PASS" if cond else "FAIL", "detail": detail})

    try:
        version = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        version = None
    rec["chrome_version"] = version

    with Chrome(binary, a.port, 1280, 900) as c:
        rec["checks"]["user_agent"] = c.js("navigator.userAgent")
        c.call("Page.enable")
        c.call("Runtime.enable")
        c.call("Log.enable")
        c.call("Page.addScriptToEvaluateOnNewDocument", source=COLLECT)

        c.navigate(a.url, wait_ms=1800)
        load = {"target": a.url, "metrics": c.metrics(), "overflow": c.js(OVERFLOW),
                "digest": c.js(PANEL), "ready_state": c.js("document.readyState")}
        rec["checks"]["desktop_load"] = load
        expect("route reaches readyState complete", load["ready_state"] == "complete", json.dumps(load["metrics"]))
        expect("desktop 1280: no horizontal overflow", not load["overflow"]["horizontalOverflow"], json.dumps(load["overflow"]))
        expect("default panel is 'checked' and aria-pressed",
               load["digest"]["visible"] == ["checked"] and load["digest"]["pressed"] == ["checked"],
               json.dumps(load["digest"]))
        p = os.path.join(a.out, "01-desktop-initial.png"); c.screenshot(p); rec["screenshots"].append(p)

        seq = []
        for target in ("changed", "restored", "checked"):
            clicked = c.click('[data-digest="%s"]' % target)
            after = c.js(PANEL)
            seq.append({"click": clicked, "after": after})
            p = os.path.join(a.out, "02-desktop-%s.png" % target); c.screenshot(p); rec["screenshots"].append(p)
            expect("pointer click shows '%s' panel" % target,
                   after["visible"] == [target] and after["pressed"] == [target],
                   "visible=%r pressed=%r" % (after["visible"], after["pressed"]))
        rec["checks"]["pointer_digest_sequence"] = seq

        c.js("document.querySelector('[data-digest=\"changed\"]').focus()")
        focused = c.js("document.activeElement && document.activeElement.dataset.digest")
        c.press("Enter", "Enter", 13)
        after_enter = c.js(PANEL)
        c.js("document.querySelector('[data-digest=\"restored\"]').focus()")
        c.press(" ", "Space", 32)
        after_space = c.js(PANEL)
        ring = c.js("(() => { const e = document.activeElement; if (!e) return null;"
                    " const s = getComputedStyle(e); return {outlineStyle: s.outlineStyle,"
                    " outlineWidth: s.outlineWidth, outlineColor: s.outlineColor}; })()")
        rec["checks"]["keyboard_digest"] = {"focused_before": focused, "after_enter": after_enter,
                                            "after_space": after_space, "focus_ring": ring}
        expect("keyboard Enter activates 'changed'", after_enter["visible"] == ["changed"], json.dumps(after_enter))
        expect("keyboard Space activates 'restored'", after_space["visible"] == ["restored"], json.dumps(after_space))
        expect("focused control shows a visible outline",
               (ring or {}).get("outlineStyle") == "solid", json.dumps(ring))
        p = os.path.join(a.out, "03-desktop-keyboard.png"); c.screenshot(p); rec["screenshots"].append(p)

        nodes = c.call("Accessibility.getFullAXTree").get("nodes", [])
        keep = []
        for n in nodes:
            role = (n.get("role") or {}).get("value")
            name = (n.get("name") or {}).get("value")
            if role in ("button", "heading", "region", "link") and name:
                keep.append({"role": role, "name": name[:90]})
        rec["checks"]["ax_tree_sample"] = keep[:40]
        rec["checks"]["ax_button_count"] = sum(1 for x in keep if x["role"] == "button")
        expect("accessibility tree exposes the controls as buttons",
               rec["checks"]["ax_button_count"] >= 3, str(rec["checks"]["ax_button_count"]))

        acc = {"initial": c.js("[...document.querySelectorAll('.collab-step')].map(d => d.open)")}
        c.click(".collab-step:nth-of-type(1) summary")
        time.sleep(0.5)
        acc["after_click"] = c.js("[...document.querySelectorAll('.collab-step')].map(d => d.open)")
        c.js("document.querySelectorAll('.collab-step')[2].querySelector('summary').focus()")
        c.press("Enter", "Enter", 13)
        time.sleep(0.5)
        acc["after_enter_third"] = c.js("[...document.querySelectorAll('.collab-step')].map(d => d.open)")
        acc["detail_text"] = c.js("(() => { const d = document.querySelectorAll('.collab-step')[2];"
                                  " const p = d.querySelector('.collab-detail');"
                                  " return p ? p.textContent.trim().slice(0, 120) : null; })()")
        rec["checks"]["accordion"] = acc
        expect("pointer opens the first accordion step", acc["after_click"][0] is True, json.dumps(acc["after_click"]))
        expect("keyboard Enter opens the third accordion step", acc["after_enter_third"][2] is True,
               json.dumps(acc["after_enter_third"]))
        expect("opened accordion exposes its detail text", bool(acc["detail_text"]))
        p = os.path.join(a.out, "04-desktop-accordion.png"); c.screenshot(p); rec["screenshots"].append(p)

        c.call("Emulation.setDeviceMetricsOverride", width=390, height=844, deviceScaleFactor=3, mobile=True)
        time.sleep(0.8)
        narrow = {"metrics": c.metrics(), "overflow": c.js(OVERFLOW), "digest": c.js(PANEL),
                  "controls_stacked": c.js("(() => { const bs = [...document.querySelectorAll('[data-digest]')];"
                                           " if (bs.length < 2) return null;"
                                           " const a = bs[0].getBoundingClientRect(), b = bs[1].getBoundingClientRect();"
                                           " return {stacked: b.top > a.bottom - 1}; })()"),
                  "tap_targets": c.js("[...document.querySelectorAll('[data-digest]')].map(b => {"
                                      " const r = b.getBoundingClientRect();"
                                      " return {id: b.dataset.digest, w: r.width, h: r.height}; })")}
        c.box("#digest-demo")
        p = os.path.join(a.out, "05-narrow-390.png"); c.screenshot(p); rec["screenshots"].append(p)
        expect("narrow 390: no horizontal overflow", not narrow["overflow"]["horizontalOverflow"],
               json.dumps(narrow["overflow"]))
        expect("narrow 390: controls stack and are at least 44px tall",
               bool(narrow["controls_stacked"]["stacked"])
               and all(t["h"] >= 44 for t in narrow["tap_targets"]), json.dumps(narrow["tap_targets"]))
        c.click('[data-digest="changed"]')
        narrow["after_click_changed"] = c.js(PANEL)
        rec["checks"]["narrow_390"] = narrow
        expect("narrow 390: pointer click changes the panel",
               narrow["after_click_changed"]["visible"] == ["changed"], json.dumps(narrow["after_click_changed"]))
        p = os.path.join(a.out, "06-narrow-390-changed.png"); c.screenshot(p); rec["screenshots"].append(p)

        errors = c.js("window.__acceptance ? window.__acceptance.errors : 'collector missing'")
        rec["checks"]["page_errors"] = errors
        rec["checks"]["console_warnings"] = c.js("window.__acceptance.console")
        expect("no page or console errors during the run",
               isinstance(errors, list) and not errors, json.dumps(errors))

        c.call("Emulation.clearDeviceMetricsOverride")
        time.sleep(0.4)
        c.js("(() => { const b = document.querySelector('[data-lang=\"zh\"]'); if (b) b.click(); })()")
        time.sleep(0.8)
        zh = {"lang": c.js("document.documentElement.lang"),
              "controls": c.js("[...document.querySelectorAll('[data-digest]')].map(b => b.textContent.trim())"),
              "states": c.js("[...document.querySelectorAll('.digest-state')].map(s => s.textContent.trim())"),
              "errors_after_switch": c.js("window.__acceptance.errors.length")}
        rec["checks"]["language_switch_zh"] = zh
        expect("zh switch localises the digest control labels",
               str(zh["lang"]).startswith("zh") and zh["controls"] == ["1 · 已检查", "2 · 已改动", "3 · 已恢复"],
               json.dumps(zh["controls"], ensure_ascii=False))
        expect("zh switch keeps page error count at zero", zh["errors_after_switch"] == 0, str(zh["errors_after_switch"]))
        p = os.path.join(a.out, "07-desktop-zh.png"); c.screenshot(p); rec["screenshots"].append(p)

    failed = [x for x in rec["assertions"] if x["result"] != "PASS"]
    rec["summary"] = {"total": len(rec["assertions"]),
                      "passed": len(rec["assertions"]) - len(failed),
                      "failed": len(failed),
                      "verdict": "pass" if not failed else "fail"}
    with open(os.path.join(a.out, "acceptance.json"), "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, ensure_ascii=False)
    for x in rec["assertions"]:
        print("%(result)s  %(assertion)s%(detail)s" % {
            "result": x["result"], "assertion": x["assertion"],
            "detail": ("  [" + x["detail"] + "]") if x["detail"] else ""})
    print("\n%s: %d/%d assertions passed" % (
        rec["summary"]["verdict"].upper(), rec["summary"]["passed"], rec["summary"]["total"]))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
