#!/usr/bin/env python3
"""Choreography start probe: pin drift + hook payloads + secret-tree + pre-push install.

Fail closed. Stdlib only. Used locally and in CI against committed drydock-pins.json.
Installs backstops/pre-push into .git/hooks if missing or drifted; fails if it cannot.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINS_PATH = ROOT / "drydock-pins.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _decision(stdout: str) -> str:
    text = stdout.strip()
    if not text:
        return "allow"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return f"unparseable:{text[:200]!r}"
    hook = payload.get("hookSpecificOutput") or {}
    decision = hook.get("permissionDecision")
    if decision == "deny":
        return "deny"
    if decision:
        return f"other:{decision}"
    return f"unparseable:{text[:200]!r}"


def run_hook(script: Path, payload: dict) -> tuple[int, str, str]:
    proc = subprocess.run(
        [sys.executable, str(script)],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True,
        cwd=str(ROOT),
    )
    stdout = proc.stdout.decode("utf-8", errors="replace")
    stderr = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, _decision(stdout), (stdout + stderr)


def check_pins() -> list[str]:
    errors = []
    if not PINS_PATH.is_file():
        return [f"missing pins file: {PINS_PATH}"]
    pins = json.loads(PINS_PATH.read_text(encoding="utf-8"))
    files = pins.get("files") or {}
    if not files:
        return ["drydock-pins.json has empty files map"]
    for rel, expected in files.items():
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing pinned file: {rel}")
            continue
        actual = sha256_file(path)
        if actual.lower() != str(expected).strip().lower():
            errors.append(f"hash drift {rel}: got {actual} expected {expected}")
    return errors


def check_hooks() -> tuple[list[str], list[dict]]:
    """Known-deny git_safety, known-deny protect_secrets, one known-benign. Expect deny/deny/allow."""
    cwd = str(ROOT)
    cases = [
        {
            "name": "git_safety_deny",
            "script": ROOT / "hooks/git_safety.py",
            "payload": {
                "tool_name": "Bash",
                "tool_input": {"command": "git reset --hard HEAD"},
                "cwd": cwd,
            },
            "expect": "deny",
        },
        {
            "name": "protect_secrets_deny",
            "script": ROOT / "hooks/protect_secrets.py",
            "payload": {
                "tool_name": "Write",
                "tool_input": {"file_path": ".env"},
                "cwd": cwd,
            },
            "expect": "deny",
        },
        {
            "name": "git_safety_allow_benign",
            "script": ROOT / "hooks/git_safety.py",
            "payload": {
                "tool_name": "Bash",
                "tool_input": {"command": "git status"},
                "cwd": cwd,
            },
            "expect": "allow",
        },
    ]
    errors = []
    evidence = []
    for case in cases:
        if not case["script"].is_file():
            errors.append(f"missing hook: {case['script']}")
            evidence.append({"name": case["name"], "error": "missing script"})
            continue
        code, decision, raw = run_hook(case["script"], case["payload"])
        rec = {
            "name": case["name"],
            "expect": case["expect"],
            "got": decision,
            "exit": code,
            "raw_preview": raw[:500],
        }
        evidence.append(rec)
        # hooks must exit 0 even on deny (permissionDecision protocol)
        if code != 0:
            errors.append(f"{case['name']}: hook exit {code} (want 0); decision={decision}")
        elif decision != case["expect"]:
            errors.append(f"{case['name']}: expected {case['expect']}, got {decision}")
    return errors, evidence



def ensure_backstop_hook(root: Path, name: str) -> list[str]:
    """Copy backstops/<name> into .git/hooks. Fail closed if missing or unmatched."""
    src = root / "backstops" / name
    git_dir = root / ".git"
    dst = git_dir / "hooks" / name
    if not src.is_file():
        return [f"missing backstops/{name}"]
    if not git_dir.is_dir():
        return [f"missing .git; cannot install {name}"]
    want = sha256_file(src)
    if dst.is_file():
        try:
            if sha256_file(dst) == want:
                try:
                    dst.chmod(0o755)
                except OSError as e:
                    return [f"could not chmod matching {name}: {e}"]
                return []
        except OSError as e:
            return [f"could not read existing {name}: {e}"]
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        dst.chmod(0o755)
    except OSError as e:
        return [f"could not install {name}: {e}"]
    try:
        got = sha256_file(dst)
    except OSError as e:
        return [f"installed {name} unreadable: {e}"]
    if got != want:
        return [f"{name} install hash mismatch: got {got} expected {want}"]
    return []


def ensure_pre_push(root: Path) -> list[str]:
    return ensure_backstop_hook(root, "pre-push")


def ensure_pre_commit(root: Path) -> list[str]:
    return ensure_backstop_hook(root, "pre-commit")


def check_secret_tree() -> list[str]:
    script = ROOT / "scripts" / "check_secret_tree.py"
    if not script.is_file():
        return ["missing scripts/check_secret_tree.py"]
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return []
    detail = (proc.stderr or proc.stdout).strip().splitlines()
    return [detail[-1] if detail else f"check_secret_tree exit {proc.returncode}"]


def main() -> int:
    pin_errors = check_pins()
    hook_errors, evidence = check_hooks()
    secret_tree_errors = check_secret_tree()
    pre_push_errors = ensure_pre_push(ROOT)
    pre_commit_errors = ensure_pre_commit(ROOT)
    errors = pin_errors + hook_errors + secret_tree_errors + pre_push_errors + pre_commit_errors
    result = {
        "ok": not errors,
        "pin_errors": pin_errors,
        "hook_errors": hook_errors,
        "secret_tree_errors": secret_tree_errors,
        "pre_push_errors": pre_push_errors,
        "pre_commit_errors": pre_commit_errors,
        "hook_evidence": evidence,
    }
    print(json.dumps(result, indent=2))
    if errors:
        print("START PROBE FAILED:", "; ".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
