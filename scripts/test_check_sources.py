#!/usr/bin/env python3
"""Test that check_sources.py fails when it should.

The point of this file is the negative case the roadmap asks for: a deliberately broken URL
must fail with exit 1 and name the file and the URL. A checker that only passes is worse
than no checker, so every rule below has a case that makes it fail.

The link cases run against a local HTTP server, so the network path is real and the test
needs no internet. Standard library only.

Usage::

    python3 scripts/test_check_sources.py

Exit code 0 when every case passes, 1 otherwise.
"""

from __future__ import annotations

import functools
import http.server
import importlib.util
import socket
import sys
import tempfile
import threading
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent


def load_checker():
    spec = importlib.util.spec_from_file_location("check_sources", HERE / "check_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check = load_checker()


class LocalServer:
    """A throwaway HTTP server over a temporary directory."""

    def __init__(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        root = self.directory.name
        Path(root, "ok.md").write_text("# a page that answers\n", encoding="utf-8")
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=root)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address[:2]
        self.base = "http://%s:%d" % (host, port)

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.directory.cleanup()


class CheckLinks(unittest.TestCase):
    def setUp(self) -> None:
        self.server = LocalServer()
        self.root = Path(self.server.directory.name)

    def tearDown(self) -> None:
        self.server.close()

    def write(self, name: str, body: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_a_link_that_answers_passes(self) -> None:
        self.write("doc.md", "see [ok](%s/ok.md)\n" % self.server.base)
        self.assertEqual(check.check_links(self.root), [])

    def test_a_broken_link_fails_and_names_the_file_the_line_and_the_url(self) -> None:
        """The acceptance case from ROADMAP.md P0 item 3."""
        self.write("doc.md", "# heading\n\nsee [gone](%s/gone.md)\n" % self.server.base)
        problems = check.check_links(self.root)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("doc.md:3", problems[0], problems[0])
        self.assertIn("/gone.md", problems[0], problems[0])
        self.assertIn("404", problems[0], problems[0])

    def test_the_same_url_on_two_lines_is_reported_per_line(self) -> None:
        url = "%s/gone.md" % self.server.base
        self.write("doc.md", "[a](%s)\n[b](%s)\n" % (url, url))
        problems = check.check_links(self.root)
        self.assertEqual(len(problems), 2, problems)

    def test_a_listed_placeholder_is_not_fetched(self) -> None:
        placeholder = next(iter(check.PLACEHOLDERS))
        self.write("doc.md", "[sample](%s)\n" % placeholder)
        self.assertEqual(check.check_links(self.root), [])

    def test_every_placeholder_names_its_reason(self) -> None:
        for url, reason in check.PLACEHOLDERS.items():
            self.assertTrue(reason.strip(), "%s has no reason" % url)

    def test_a_bot_wall_status_is_tolerated_only_on_a_listed_host(self) -> None:
        walled = [url for url in ("https://docs.n8n.io/x",) if check._bot_wall(url)]
        self.assertTrue(walled, "the bot-wall allowlist lost its entry")
        self.write("doc.md", "[vendor](https://docs.n8n.io/x)\n")
        fake = lambda url: 403  # noqa: E731
        self.assertEqual(check.check_links(self.root, fetch=fake), [])
        self.write("doc.md", "[other](https://example.invalid/x)\n")
        self.assertEqual(len(check.check_links(self.root, fetch=fake)), 1)

    def test_a_schema_id_is_an_identifier_not_a_link(self) -> None:
        self.write("schema.json", '{\n  "$id": "https://example.invalid/schema.json"\n}\n')
        self.assertEqual(check.check_links(self.root, fetch=lambda url: 404), [])

    def test_the_real_repository_reports_its_problems_with_a_location(self) -> None:
        """Wiring check on the real tree: whatever it finds must name file and line."""
        for problem in check.check_links(REPO_ROOT, fetch=lambda url: 404):
            self.assertRegex(problem, r"^\S+?:line|\S+:\d+: https?://", problem)


class CheckVersions(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "docs/n8n").mkdir(parents=True)

    def tearDown(self) -> None:
        self.directory.cleanup()

    def write(self, operations: str, matrix: str) -> None:
        (self.root / "docs/n8n/OPERATIONS.md").write_text(operations, encoding="utf-8")
        (self.root / "docs/n8n/VERSION-MATRIX.md").write_text(matrix, encoding="utf-8")

    HEADER = ("# matrix\n\n## Claims and their range\n\n"
              "| Claim | Evidence | Holds on | Note |\n| --- | --- | --- | --- |\n")

    def test_a_field_observation_with_a_version_passes(self) -> None:
        self.write("# ops\n\nIt republished (*field*, `2.41.7`).\n", self.HEADER)
        self.assertEqual(check.check_versions(self.root), [])

    def test_a_field_observation_without_a_version_fails(self) -> None:
        self.write("# ops\n\nIt republished (*field*).\n", self.HEADER)
        problems = check.check_versions(self.root)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("OPERATIONS.md:3", problems[0], problems[0])

    def test_a_version_line_such_as_2_x_counts(self) -> None:
        self.write("# ops\n\nSeen on `2.x` (*field*).\n", self.HEADER)
        self.assertEqual(check.check_versions(self.root), [])

    def test_a_claim_row_without_a_version_fails(self) -> None:
        self.write("# ops\n", self.HEADER + "| `GET /x` | spec 1.1.1 | current | — |\n")
        problems = check.check_versions(self.root)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("names no version", problems[0])

    def test_a_claim_row_without_an_evidence_kind_fails(self) -> None:
        self.write("# ops\n", self.HEADER + "| `GET /x` | guesswork | 2.46.4 | — |\n")
        problems = check.check_versions(self.root)
        self.assertEqual(len(problems), 1, problems)
        self.assertIn("no evidence kind", problems[0])

    def test_an_all_row_passes_without_a_version(self) -> None:
        self.write("# ops\n", self.HEADER + "| `GET /x` | spec | all | — |\n")
        self.assertEqual(check.check_versions(self.root), [])

    def test_the_real_repository_passes(self) -> None:
        self.assertEqual(check.check_versions(REPO_ROOT), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
