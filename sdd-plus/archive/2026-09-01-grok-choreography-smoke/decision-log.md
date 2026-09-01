# Decision Log

## Change

grok-choreography-smoke

## Decisions

| Date | Decision | Reason | Alternatives Considered |
| --- | --- | --- | --- |
| 2026-09-01 | Use a `src/` layout with a root `conftest.py` that adds `src` to `sys.path`. | Keeps the sandbox package importable under the existing CI command with no packaging config or workflow edit (workflows are a protected path). | Top-level `drydock_sandbox/` package (relies on implicit cwd on `sys.path`); adding `pyproject.toml` with an editable install (heavier than a LITE change warrants). |
| 2026-09-01 | Give the function one real rule: reject empty/whitespace-only names with `ValueError`. | A function with zero branches gives the verifier nothing to check; one rule makes the tests meaningful while staying trivial. | Pure passthrough formatting with no validation; returning a sentinel string instead of raising. |
| 2026-09-01 | No delta specs. | The change adds an isolated sandbox module and does not alter any living capability. | Writing a capability spec for the smoke module (would create durable spec debt for throwaway code). |
| 2026-09-01 | Leave verification Result as Pending. | The Implementer reports evidence; verification is the verifier subagent's call. | Self-marking verified (violates the operating rules). |

## Override — 2026-09-01
- Gates waived: 4 pending task(s)
- Reason: v1 overlay: independent verifier must write nothing, so four verifier-owned tasks.md checkboxes stay unchecked; VERIFIED WITH NOTES is bound by check_verdict.py sha256 88328932376b748a5e3cfc573d727393ee0c3baefa15233bc05f89828b19a323 at commit 174f04a782cc45f8694a256fb563f2dc1526ee8c
