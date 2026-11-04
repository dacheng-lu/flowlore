#!/usr/bin/env python3
"""Check that the catalog's external sources answer and that the n8n chapter dates its claims.

Two properties rot without anyone noticing:

* an external URL stops answering — every source in this repository is a reference, not a
  tested dependency, so nothing else would fail;
* an n8n statement does not say which build it was read on — most n8n guidance on the
  internet is undated, which is the failure mode this chapter exists to avoid.

What is checked
---------------
1. **Links.** Every `http(s)` URL in the Markdown and JSON files answers (2xx/3xx). A host
   that blocks bots is allowlisted by prefix, and a URL that is deliberately unresolvable
   (sample data, a JSON Schema `$id`) is allowlisted by exact value with a reason.
2. **Versions.** In `docs/n8n/OPERATIONS.md` every observation marked ``*field*`` names a
   version. In `docs/n8n/VERSION-MATRIX.md` every claim row has an evidence kind
   (`spec` / `docs` / `field`) and a range that names a version or says `all`.

Usage::

    python3 scripts/check_sources.py              # links and versions
    python3 scripts/check_sources.py --links      # network only
    python3 scripts/check_sources.py --versions   # no network

Exit code 0 when every case passes, 1 otherwise. Each failure names the file, the line and,
for a link, the status.
"""

from __future__ import annotations

import re
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OPERATIONS = Path("docs/n8n/OPERATIONS.md")
MATRIX = Path("docs/n8n/VERSION-MATRIX.md")

SCANNED_SUFFIXES = (".md", ".json")
URL = re.compile(r"https?://[^\s)\"'`<>]+")
# The chapter dates its claims as `2.46.4`, `2.4x`, `2.x` or `all`; the `x` forms are the
# version *line*, which is what a range can honestly promise.
VERSIONISH = re.compile(r"\b\d+\.[0-9x]+(?:\.[0-9x]+)?\b", re.I)
SCHEMA_ID = re.compile(r'"\$id"\s*:\s*"[^"]*"')

# Deliberately unresolvable, with the reason it stays that way. A placeholder that is not
# listed here is a failure, which is the point: the list is the audit trail.
PLACEHOLDERS = {
    "https://github.com/sample/alpha/releases/tag/v1.0":
        "sample data of examples/release-digest, never meant to resolve",
    "https://github.com/sample/beta/releases/tag/v2.1":
        "sample data of examples/release-digest, never meant to resolve",
}

# A host that answers a bot with 403/405/429/501 still serves the page to a reader.
BOT_WALLS = {
    # (host prefix, path prefix) -> reason
    "docs.n8n.io": "vendor documentation answers automated clients with 403/429",
}

ACCEPTED_BOT_WALL_CODES = {403, 405, 429, 501}
TIMEOUT = 20
USER_AGENT = "flowlore-link-check/1.0 (+https://github.com/dacheng-lu/flowlore)"


def scanned_files(root: Path = REPO_ROOT) -> list[Path]:
    out = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        if ".git" in path.parts:
            continue
        out.append(path)
    return out


def urls_in(path: Path, root: Path = REPO_ROOT) -> list[tuple[int, str]]:
    """(line number, url) for every link in one file, minus the ones that are not links."""
    found, text = [], path.read_text(encoding="utf-8", errors="ignore")
    # A JSON Schema `$id` is an identifier, not a document to fetch.
    for match in SCHEMA_ID.finditer(text):
        text = text.replace(match.group(0), '"$id"' + " " * (len(match.group(0)) - 5))
    for number, line in enumerate(text.splitlines(), 1):
        for match in URL.finditer(line):
            url = match.group(0).rstrip(".,;:")
            if any(url.startswith(k) for k in BOT_WALLS):
                pass  # still checked; only a bot-wall status is tolerated below
            found.append((number, url))
    return found


def fetch_status(url: str) -> int | str:
    """HTTP status for a URL; HEAD first, GET when the host refuses HEAD."""
    context = ssl.create_default_context()
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT, context=context) as response:
                return response.status
        except urllib.error.HTTPError as error:
            if method == "HEAD" and error.code in (403, 405, 501):
                continue
            return error.code
        except Exception as error:  # URLError, timeout, TLS, DNS
            if method == "HEAD":
                continue
            return type(error).__name__
    return "unreachable"


def _bot_wall(url: str) -> str | None:
    for host, reason in BOT_WALLS.items():
        if re.sub(r"^https?://([^/]+).*", r"\1", url).endswith(host):
            return reason
    return None


def check_links(root: Path = REPO_ROOT, fetch=fetch_status) -> list[str]:
    problems, seen = [], {}
    for path in scanned_files(root):
        for number, url in urls_in(path, root):
            if url in PLACEHOLDERS:
                continue
            status = seen.get(url)
            if status is None:
                status = seen[url] = fetch(url)
            ok = isinstance(status, int) and 200 <= status < 400
            tolerated = (isinstance(status, int) and status in ACCEPTED_BOT_WALL_CODES
                         and _bot_wall(url) is not None)
            if not ok and not tolerated:
                problems.append("%s:%d: %s -> %s" % (path.relative_to(root), number, url, status))
    return problems


def check_versions(root: Path = REPO_ROOT) -> list[str]:
    problems = []

    operations = root / OPERATIONS
    for number, line in enumerate(operations.read_text(encoding="utf-8").splitlines(), 1):
        if "*field*" in line and not VERSIONISH.search(line):
            problems.append("%s:%d: a *field* observation names no version" % (OPERATIONS, number))

    matrix = (root / MATRIX).read_text(encoding="utf-8")
    if "## Claims and their range" not in matrix:
        problems.append("%s: no '## Claims and their range' section" % MATRIX)
        return problems
    section = matrix.split("## Claims and their range", 1)[1].split("\n## ", 1)[0]
    for line in section.splitlines():
        row = line.strip()
        if not row.startswith("|") or re.match(r"^\|[\s\-:|]+\|$", row):
            continue
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if cells[0].lower() == "claim":
            continue
        if len(cells) < 4:
            problems.append("%s: claim row has %d columns, expected 4: %s"
                            % (MATRIX, len(cells), row[:60]))
            continue
        claim, evidence, holds = cells[0], cells[1], cells[2]
        if not re.match(r"^(spec|docs|field)\b", evidence):
            problems.append("%s: claim %r has no evidence kind (spec/docs/field): %r"
                            % (MATRIX, claim[:40], evidence))
        if not (VERSIONISH.search(holds) or re.search(r"\ball\b", holds, re.I)):
            problems.append("%s: claim %r names no version and no 'all' in Holds on: %r"
                            % (MATRIX, claim[:40], holds))
    return problems


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a not in ("--links", "--versions")]
    if unknown:
        print("usage: python3 scripts/check_sources.py [--links | --versions]", file=sys.stderr)
        return 2
    do_links = "--versions" not in argv
    do_versions = "--links" not in argv

    problems = []
    if do_links:
        problems += check_links()
    if do_versions:
        problems += check_versions()

    for problem in problems:
        print(problem)
    if problems:
        print("\n%d problem(s)" % len(problems), file=sys.stderr)
        return 1
    print("sources ok: every link answers, every n8n claim names its version")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
