"""Promptfoo callbacks for the frozen FlowLore baseline; no model or network calls."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
import scenarios  # noqa: E402
import scorer  # noqa: E402

LONGHAUL_REV = "fd81df28052f1c1d0f29955a8a48170049d4cbf0"
FILES = {
    BASE / "cases.json": "1475dcb16875d0808292f0869879eba066116ac7dc0b373f1af23f528b75c260",
    BASE / "scenarios.py": "3e324d16abcdf46bc2b2fc4d6cab9267419dd17ab91f471e7dae75d49201c00b",
    BASE / "scorer.py": "8a3f42401f302e211758e714e986970b14852baaaa6f095cfcabf35328133838",
    BASE.parent / "release-digest" / "digest.py": "eaa3ccd1424844b828b1f5cd8774b2e8bf1aba37fc229d3bb7eb94d2c182bb26",
}
VALID_DIGESTS = {"d-valid-3", "d-valid-1", "d-valid-6", "d-duplicate-identical", "d-injection-title"}
ERROR = "FLOWLORE_HARNESS_ERROR: "


class AdapterError(Exception):
    pass


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def input_text(case):
    return case["files"]["release.json" if case["scenario"] == "digest" else "state.json"]


def prompt_for(case):
    data = input_text(case).encode("utf-8")
    return (scenarios.digest_prompt(data) if case["scenario"] == "digest"
            else scenarios.gate_prompt(data))


def prompt_matches(observed, expected):
    """True when observed is the frozen prompt, or that prompt minus one trailing newline.

    promptfoo 0.125.1 renders a bare ``{{var}}`` template through nunjucks, which
    strips exactly one trailing newline from the rendered value. That single
    documented transport transformation is tolerated; any other difference (a
    second newline, a changed character, a different prompt) is a binding failure.
    """
    if not isinstance(observed, str):
        return False
    if observed == expected:
        return True
    return expected.endswith("\n") and observed == expected[:-1]


def requested_revision():
    revision = os.environ.get("FLOWLORE_LONGHAUL_REV", LONGHAUL_REV)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise AdapterError("FLOWLORE_LONGHAUL_REV must be a full lowercase commit SHA")
    return revision


def checkout():
    path = os.environ.get("FLOWLORE_LONGHAUL")
    if not path:
        raise AdapterError("FLOWLORE_LONGHAUL must name the pinned Longhaul checkout")
    path = Path(path).resolve()
    def git(*args):
        proc = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True, timeout=15)
        if proc.returncode:
            raise AdapterError("cannot inspect the Longhaul checkout")
        return proc.stdout.strip()
    if Path(git("rev-parse", "--show-toplevel")).resolve() != path or git("rev-parse", "HEAD") != requested_revision():
        raise AdapterError("Longhaul must be at requested revision " + requested_revision())
    git("diff", "--quiet", "HEAD")
    for name in ("checkpoint.py", "secret_scan.py"):
        if not (path / "scripts" / name).is_file():
            raise AdapterError("missing Longhaul " + name)
    return path


def integrity():
    for path, digest in FILES.items():
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise AdapterError("frozen baseline file missing or changed: " + path.name)
    cases = scenarios.build()
    manifest = json.loads((BASE / "cases.json").read_text(encoding="utf-8"))["cases"]
    if [(c["id"], c["scenario"], c["split"], c["category"]) for c in cases.values()] != [
        (c["id"], c["scenario"], c["split"], c["category"]) for c in manifest
    ] or len(cases) != 24:
        raise AdapterError("case manifest and generated cases differ")
    return cases


def protocol(cmd, proc):
    """Reject checker crashes: both checkers' normal refusals have defined protocols."""
    script = Path(cmd[1]).name
    if script == "digest.py":
        mode = cmd[2]
        if proc.returncode == 0:
            if proc.stderr or not re.fullmatch(rf"{mode}: [1-9][0-9]* unique releases\n", proc.stdout):
                raise AdapterError("digest checker returned malformed success")
        elif proc.returncode != 1 or proc.stdout or not proc.stderr.startswith("refused: ") or "Traceback" in proc.stderr or proc.stderr.startswith("refused: [Errno "):
            raise AdapterError("digest checker failed outside its refusal protocol")
    elif script == "checkpoint.py":
        try:
            data = json.loads(proc.stdout)
        except (ValueError, TypeError) as exc:
            raise AdapterError("gate checker returned invalid JSON") from exc
        if (proc.returncode not in (0, 1) or proc.stderr or not isinstance(data, dict)
                or type(data.get("ok")) is not bool or data["ok"] != (proc.returncode == 0)
                or not isinstance(data.get("errors"), list) or not isinstance(data.get("warnings"), list)
                or not isinstance(data.get("scope"), str)):
            raise AdapterError("gate checker failed outside its response protocol")
    else:
        raise AdapterError("unexpected checker: " + script)
    return proc


def invoke(cmd):
    return protocol(cmd, subprocess.run(cmd, capture_output=True, text=True, timeout=60))


def probe(case, longhaul):
    """Run the oracle for this exact fixture before parsing any candidate reply."""
    with tempfile.TemporaryDirectory(prefix="flowlore-promptfoo-") as work:
        scorer._write_fixture(case["files"], work)
        if case["scenario"] == "digest":
            script = str(BASE.parent / "release-digest" / "digest.py")
            source = str(Path(work, "release.json"))
            valid = invoke([sys.executable, script, "validate", source])
            if (valid.returncode == 0) != (case["id"] in VALID_DIGESTS):
                raise AdapterError("digest oracle disagrees with frozen fixture " + case["id"])
            if valid.returncode == 0:
                target = Path(work, "expected.md")
                rendered = invoke([sys.executable, script, "render", source, "--output", str(target)])
                if rendered.returncode != 0 or not target.is_file() or not target.read_bytes():
                    raise AdapterError("digest render failed for " + case["id"])
        else:
            cmd = [sys.executable, str(longhaul / "scripts" / "checkpoint.py"), "gate", str(Path(work, "state.json"))]
            if (invoke(cmd).returncode == 0) != case["meta"]["expect_pass"]:
                raise AdapterError("gate oracle disagrees with frozen fixture " + case["id"])


def preflight(cases=None):
    frozen = integrity()
    longhaul = checkout()
    probe(frozen["d-valid-3"], longhaul)  # validate and render must work, even for invalid input
    for case in cases if cases is not None else frozen.values():
        probe(case, longhaul)
    return frozen, longhaul


def runtime_binding():
    results = os.environ.get("FLOWLORE_RESULTS")
    try:
        results_hash = hashlib.sha256(Path(results).read_bytes()).hexdigest() if results else None
    except OSError as exc:
        raise AdapterError("cannot read FLOWLORE_RESULTS") from exc
    settings = {"synthetic": os.environ.get("FLOWLORE_SYNTHETIC", "good"),
                "results_sha256": results_hash, "policy": os.environ.get("FLOWLORE_POLICY"),
                "attempt": os.environ.get("FLOWLORE_ATTEMPT")}
    return sha(json.dumps(settings, sort_keys=True))


def selected_cases(cases, split):
    if split not in ("dev", "heldout", "all"):
        raise AdapterError("FLOWLORE_SPLIT must be dev, heldout, or all")
    requested = os.environ.get("FLOWLORE_ONLY")
    ids = None
    if requested is not None:
        ids = requested.split(",")
        if not all(ids) or len(set(ids)) != len(ids) or any(cid not in cases for cid in ids):
            raise AdapterError("FLOWLORE_ONLY must contain unique known case IDs")
    selected = [c for c in cases.values() if (split == "all" or c["split"] == split)
                and (ids is None or c["id"] in ids)]
    if not selected or (ids is not None and len(selected) != len(ids)):
        raise AdapterError("case selection is empty or conflicts with FLOWLORE_SPLIT")
    return selected


def generate_tests():
    cases = integrity()
    selected = selected_cases(cases, os.environ.get("FLOWLORE_SPLIT", "dev"))
    preflight(selected)
    return [{"description": f"{c['id']} ({c['split']}, {c['scenario']})",
             "vars": {"case_id": c["id"], "case_prompt": prompt_for(c),
                      "input_sha256": sha(input_text(c)), "longhaul_rev": requested_revision(),
                      "runtime_binding": runtime_binding()},
             "metadata": {"scenario": c["scenario"], "split": c["split"]}} for c in selected]


def get_assert(output, context):
    # Promptfoo itself maps exceptions to score 0. The explicit marker makes such
    # rows identifiable; validate_results.py rejects the whole evaluation.
    try:
        cases = integrity()
        variables = context["vars"]
        cid = variables["case_id"]
        if not isinstance(cid, str) or cid not in cases:
            raise AdapterError("unknown case id")
        case = cases[cid]
        expected = prompt_for(case)
        if (not prompt_matches(variables.get("case_prompt"), expected)
                or not prompt_matches(context.get("prompt"), expected)
                or variables.get("input_sha256") != sha(input_text(case))
                or variables.get("longhaul_rev") != requested_revision()
                or variables.get("runtime_binding") != runtime_binding()):
            raise AdapterError("prompt or case input binding mismatch for " + cid)
        _, longhaul = preflight([case])
        if not isinstance(output, str):
            raise AdapterError("provider output must be a string")
        if not output.strip():
            return {"pass": False, "score": 0, "reason": "MODEL_FAILURE: empty_answer"}
        original = scorer._run
        def checked(cmd, **kw):
            result = protocol(cmd, original(cmd, **kw))
            if (Path(cmd[1]).name == "digest.py" and cmd[2] == "validate"
                    and (result.returncode == 0) != (case["id"] in VALID_DIGESTS)):
                raise AdapterError("digest oracle changed while scoring " + case["id"])
            if (Path(cmd[1]).name == "checkpoint.py"
                    and (result.returncode == 0) != case["meta"]["expect_pass"]):
                raise AdapterError("gate oracle changed while scoring " + case["id"])
            return result
        try:
            scorer._run = checked
            result = scorer.evaluate(case, output, longhaul=longhaul)
        finally:
            scorer._run = original
        return {"pass": result["score"] == 1, "score": result["score"],
                "reason": ("MODEL_RESULT: " + result["detail"])}
    except Exception as exc:
        return {"pass": False, "score": 0, "reason": ERROR + str(exc)}


if __name__ == "__main__":
    try:
        cases, longhaul = preflight()
        print(f"PASS: {len(cases)} frozen cases; Longhaul {requested_revision()}; every oracle answered")
    except Exception as exc:
        print(ERROR + str(exc), file=sys.stderr)
        sys.exit(2)
