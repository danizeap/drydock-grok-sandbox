# Verification

## Change

grok-coplan-linux-discover

## Automated Checks

- [x] `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q -p no:cacheprovider` — **42 passed** (was
      31 before this packet; 11 new discovery tests, none skipped).
- [x] `python3 scripts/start_probe.py` — **exit 0**. Pins, hook self-tests (deny/deny/allow),
      secret tree, and pre-push/pre-commit install all clean with the six new conductor entries.
- [x] Vendoring integrity: all ten fetched files hashed sha256-equal to
      `/home/box/drydock-state/drydock-grok-sandbox/conductor/PIN.json` before copying. Pin commit
      `5f76f67eda90d92b4f0eea1908e66c7f45ca81f7`. Six of those ten are in the tree now; the other
      four were dropped afterwards (see below) and are not vendored.
- [x] `launchguardian scan --target . --strict-scanners` — **APPROVED**, `findings: 0`. The three
      blocking Semgrep findings from the first strict run are gone; none is suppressed. See
      "Strict-scanner remediation" below.

## Manual Checks

- [x] **Discovery on this VM.** `discover_core()` returns `/home/box/.local/bin/codex` with
      `LOCALAPPDATA` unset — the exact failure from the live-fire run is gone.
- [x] **Windows shape preserved.** `test_windows_glob_picks_the_newest_core` and
      `test_windows_root_wins_over_path` confirm the `LOCALAPPDATA/OpenAI/Codex/bin/*/codex.exe`
      glob still returns the newest exe and still takes priority over `PATH`.
- [x] **Sandbox copy rejected.** Three tests cover it: a `.sandbox-bin` entry on `PATH`, a
      `PATH` symlink pointing into `.sandbox-bin`, and a `.sandbox-bin` dir inside the Windows
      glob root. All resolve to `None`, never to the stale core.
- [x] **Live-fire `negotiate.py --round 1`** with a short non-secret probe plan (a made-up
      `--verbose` CLI flag): **exit 0, `ok: true`**. It cleared `discover` — the packet's bar —
      and in fact ran the whole chain: gauge `{plan: prolite, remaining 98%}`, route
      `gpt-5.4-mini` ("light task -> workhorse model"), delegation exit 0 in 18.5s, returning a
      schema-conforming critique with `converged: false` and three blocking concerns.
      Environment: codex-cli 0.152.0, `LOCALAPPDATA` unset.

## Strict-Scanner Remediation

The first `--strict-scanners` run came back `BLOCKED` on three open blocking findings. All three
are fixed at the source; no `nosemgrep`, no accepted-risk disposition.

| Finding | Gate | Fix |
| --- | --- | --- |
| `python36-compatibility-Popen1` / `-Popen2` at `codex_bridge.py:134` (`errors=` / `encoding=` passed to `Popen`) | Gate 3 — Code Security | Spawn with binary pipes; wrap stdin/stdout/stderr in `io.TextIOWrapper(encoding="utf-8", errors="replace")`, stdin line-buffered. The JSON-RPC line protocol is unchanged, and UTF-8 is now explicit instead of locale-dependent. |
| `subprocess-shell-true` at `mutate.py:477` | Gate 7 — Injection & Input Safety | `mutate.py` is not vendored. It has no caller in this repo (`negotiate.py`'s import closure is `codex_bridge` + `review`), and running mutating delegation on this VM is already forbidden by `README.md` and `sdd-plus/security/scope-contract.yml`. `coord.py`, `executors.py`, and `handoff.py` are dropped for the same reason — dead vendored code. |

Re-verified after the fix: pytest **42 passed**, `start_probe.py` **exit 0**, scan **APPROVED**.
Windows-first discovery, the `PATH` and `$HOME/.local/bin` fallbacks, and the `.sandbox-bin`
rejection filter are all untouched by this remediation — the same eleven discovery tests cover
them and still pass.

## Documentation Updates

- [x] No README or user-facing docs update needed. Reason: the conductor is an internal
      operator tool with no documented install-path contract, and `discover_core()` keeps its
      signature and return type. The corrected `negotiate.py` `discover` error message is the
      user-facing surface that needed updating, and it was.
- [x] Project context: no update needed — this changes no project goal, constraint, or
      architecture, only where one executable is looked for.
- [x] Specs: no capability spec touched. `sdd-plus/specs/multi-agent-orchestration-vision.md`
      lives in upstream Drydock, not this sandbox repo; the discovery-portability note belongs
      upstream with the pin, not here.

## Scope Honesty

Stages after `discover` were explicitly out of scope for this packet. They happened to pass on
this VM, which is stronger evidence than required — but the behavior change itself is confined to
discovery plus one error string. The strict-scanner remediation added no behavior: it moved the
`Popen` decoding into explicit wrappers and shrank the vendored file set. Nothing was archived; no
leftover-hole work was started.

Two non-blocking observations the verifier raised are deliberately **not** fixed here, to keep
this remediation to its stated scope:

- `read_rate_limits` never explicitly closes the stdout/stderr wrappers, so they are reclaimed by
  GC (2 `ResourceWarning`s per call). Measured identical before and after this change — it is the
  pre-existing upstream behavior, not a regression.
- The three wrappers are built outside the spawn `try`. Unreachable today (all three streams are
  `subprocess.PIPE`, so none can be `None`), but a future edit dropping a `PIPE` kwarg would raise
  `AttributeError` past the `except (OSError, ValueError)` and leak the spawned child.

Both belong in a conductor-hygiene packet, upstream where these lines are actually exercised.

## Result

**Verified.** All acceptance criteria in `brief.md` met.
