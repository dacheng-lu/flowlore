#!/usr/bin/env python3
"""Render the captured budget-matched experiment."""
import json
from pathlib import Path

source = json.loads(Path('summary.json').read_text())['budget_matched']
solo = source['C_pi_alone']
cluster = source['H8_hermes_8pi']
Path('report.md').write_text(
    '# Budget-matched comparison\n\n'
    f"Solo: {solo['fixed']} fixed, {solo['wall_median']} s median.\n"
    f"Cluster: {cluster['fixed']} fixed, {cluster['wall_median']} s median.\n"
)
