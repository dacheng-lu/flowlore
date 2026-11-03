#!/usr/bin/env python3
"""Test that ROADMAP.md stays true to the repository.

The roadmap is a public claim about the future: its sections must stay in order, the version it calls
released must be the catalog's own version, the README must link to it, and every relative link must
point at a file that exists. Standard library only.

Usage::

    python3 scripts/test_roadmap.py

Exit code 0 when every case passes, 1 otherwise.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ROADMAP = REPO_ROOT / "ROADMAP.md"
README = REPO_ROOT / "README.md"
CATALOG = REPO_ROOT / "catalog" / "catalog.json"

SECTIONS = ["Released", "Owed", "Blocked", "Candidate", "Not planned"]


def roadmap() -> str:
    return ROADMAP.read_text(encoding="utf-8")


def section(name: str) -> str:
    parts = re.split(r"(?m)^## ", roadmap())
    hit = [p for p in parts if p.startswith(name)]
    assert hit, "no '## %s' section" % name
    return hit[0]


def catalog_version() -> str:
    return json.loads(CATALOG.read_text(encoding="utf-8"))["catalogVersion"]


def version_key(value: str) -> tuple:
    return tuple(int(part) for part in value.split("."))


class Roadmap(unittest.TestCase):
    def test_the_sections_that_keep_it_honest_exist_in_order(self) -> None:
        heads = re.findall(r"(?m)^## (.+)$", roadmap())
        order = [h for h in heads if any(h.startswith(s) for s in SECTIONS)]
        self.assertEqual([next(s for s in SECTIONS if h.startswith(s)) for h in order], SECTIONS)

    def test_the_catalog_version_is_listed_as_released(self) -> None:
        version = catalog_version()
        self.assertRegex(section("Released"), r"(?m)^- \*\*%s\*\* " % re.escape(version),
                         "the roadmap does not list catalog version %s under Released" % version)

    def test_nothing_after_the_catalog_version_is_listed_as_released(self) -> None:
        listed = re.findall(r"(?m)^- \*\*(\d+\.\d+(?:\.\d+)?)\*\*", section("Released"))
        self.assertTrue(listed, "no released version found")
        newest = max(listed, key=version_key)
        self.assertEqual(newest, catalog_version(),
                         "the roadmap lists a released version the catalog does not have")

    def test_the_readme_links_to_the_roadmap(self) -> None:
        text = README.read_text(encoding="utf-8")
        header = text.split('<a id="english">')[0]
        self.assertIn("](ROADMAP.md)", header, "the README header does not link the roadmap")
        self.assertGreaterEqual(text.count("](ROADMAP.md)"), 4,
                                "the roadmap should be linked in the header and in each language's next steps")

    def test_every_relative_link_in_the_roadmap_points_at_a_file_that_exists(self) -> None:
        targets = [t for t in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", roadmap()) if "://" not in t]
        self.assertGreater(len(targets), 2)
        for target in targets:
            self.assertTrue((REPO_ROOT / target).exists(), "the roadmap links to missing %s" % target)


if __name__ == "__main__":
    unittest.main(verbosity=2)
