# Threat Model

Throwaway LITE sandbox. Not a production product threat model.

## Context

- Project: drydock-grok-sandbox
- Change: bootstrap-lgf-packet
- Date: 2026-09-01
- Owner: Daniel Paez
- Scope: Public GitHub repo + GitHub Actions `drydock` job + shared Grok VM live-fire of Drydock kernel/hooks. No customer users.

## Related Gates

- Gate 2 — Threat Modeling
- Gate 3 — Code Security
- Gate 7 — Injection & Input Safety
- Gate 12 — Resilience, DDoS, Abuse & Cost Defense
- Gate 19 — Business Logic Abuse

## System Summary

Vendored Drydock kernel and repo-local hooks, a fail-closed GitHub Actions job, and LaunchGuardian. Agents (Grok choreographer, Claude Code, Codex) operate on a shared VM. The git tree is public. The run ledger is outside the tree. There is no deployed web/API product.

## Trust Boundaries

| Boundary | What Crosses It | Controls | Open Questions |
| --- | --- | --- | --- |
| Public GitHub | source, CI logs | public by design; branch protection (`drydock`, enforce_admins, no force-push, no deletion) | none for sandbox |
| Agent tool payloads → hooks | JSON stdin | hooks deny dangerous git/secret writes; start_probe.py asserts deny/deny/allow | parser robustness |
| CI runner | checkout + pip + scanner binaries | Actions SHA-pinned; gitleaks/trivy checksum-pinned; semgrep version-pinned | supply chain of those pins |
| Shared VM | GitHub creds, ledger, other agent state | ledger kept out of git; no client/LOQ files | host isolation is a VM concern, not a product launch |

## Assets

| Asset | Why It Matters | Sensitivity | Owner |
| --- | --- | --- | --- |
| Public source tree | choreography live-fire evidence | public | Daniel Paez |
| GitHub write on main | can break CI / inject files | medium | Daniel Paez |
| VM GitHub credentials | can push/act as danizeap | high (host, not in tree) | Daniel Paez |
| Run ledger | orchestration state | low-medium; must stay out of git | Daniel Paez |

## Threats And Mitigations

| Threat | Impact | Likelihood | Severity | Mitigation | Evidence | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Secret committed to public repo | credential leak | medium | high | protect_secrets hook, .gitignore, gitleaks in CI | hooks/protect_secrets.py, .github/workflows/drydock.yml | Daniel Paez | open-until-scanners-run |
| Force-push / history rewrite | destroy evidence | low | high | git_safety hook; branch protection no force-push | hooks/git_safety.py | Daniel Paez | recorded |
| Quiet / missing scanners treated as clean | false green | high if scanners not installed | high | strict-scanners + ci_parse_lg_report.py fail-closed | scripts/ci_parse_lg_report.py | Daniel Paez | recorded |
| Agent lethal trifecta on host | exfil of VM-private data via outbound tools | medium on the shared VM | high for host, not a product-data issue | no customer data in tree; ledger outside git; Gate 20 BLOCKED | gate-applicability.yml Gate 15 | Daniel Paez | residual; not a production acceptance |
| Supply-chain of CI tools | malicious pytest/semgrep/gitleaks/trivy/action | low | high | SHA-pin Actions; checksum-pin binaries; pin semgrep version; pin LaunchGuardian git ref | drydock.yml | Daniel Paez | recorded |

## Abuse Cases

- Treat this sandbox as a production launch approval.
- Copy client/LOQ files into the public tree.
- Skip scanners and keep CI green.
- Commit the VM ledger into git.

## Critical Findings

Critical findings block launch until fixed and verified, removed from launch scope, or downgraded by new evidence.

An exceptional Critical override is not normal approval. This sandbox does not request one.

| Finding | Evidence | Required Fix | Owner | Status |
| --- | --- | --- | --- | --- |
| None recorded as a product Critical | This is not a product | Do not launch | Daniel Paez | n/a |

## Residual Risk

Shared-VM agent tools can see host state and push to GitHub. That is inherent to this live-fire sandbox and is **not** accepted as a production launch risk. See `accepted-risks.md`.
