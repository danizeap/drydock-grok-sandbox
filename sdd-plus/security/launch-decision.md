# Launch Decision

Throwaway LITE sandbox record. This is **not** a production launch and must not be read as a clean ship.

## Summary

- Project: drydock-grok-sandbox
- Change: bootstrap-lgf-packet (CI scanner install + honest LGF files)
- Date: 2026-09-01
- Owner: Daniel Paez
- Launch target: none (public throwaway sandbox; GitHub source + CI only)
- Decision: BLOCKED

Decision remains BLOCKED because this project is not a production product, has no owner production-launch approval, and LaunchGuardian is being used as a fail-closed CI gate rather than a ship sign-off.

Critical findings block launch until the finding is fixed and verified, the affected feature or asset is removed from launch scope, or the severity is downgraded by new evidence.

An exceptional Critical override is not normal approval. This sandbox does not request one.

## Related Gates

- Gate 20 — Launch Decision
- Gate 21 — Continuous Monitoring

## Gate Status

| Gate | Applies | Status | Evidence | Notes |
| --- | --- | --- | --- | --- |
| Gate 0 — Scope & Permission | true | open | PROJECT_CONTEXT.md, scope-contract.yml | Sandbox scope only; not production sign-off |
| Gate 1 — Product, Asset & Data Inventory | true | recorded | product-inventory.yml, data-inventory.yml | Honest non-product inventory |
| Gate 2 — Threat Modeling | true | recorded | threat-model.md | Agent sandbox threats, not a SaaS threat model |
| Gate 3 — Code Security | true | pending-scan | CI semgrep | Always-on |
| Gate 4 — Secrets & Config Hygiene | true | pending-scan | CI gitleaks, protect_secrets hook | Always-on |
| Gate 5 — Frontend Exposure | false | n/a | no frontend in tree | high_risk: false |
| Gate 6 — API Auth & Object Authorization | false | n/a | no product API | high_risk: false |
| Gate 7 — Injection & Input Safety | true | pending-scan | hook JSON parsers | Not a public web form |
| Gate 8 — Auth, Sessions & CSRF | false | n/a | no product auth | high_risk: false |
| Gate 9 — File Upload, SSRF, Imports & Exports | false | n/a | no upload/export product | high_risk: false |
| Gate 10 — Dependency, SBOM & Supply Chain | true | pending-scan | CI trivy, pinned Actions/binaries | Always-on |
| Gate 11 — Infrastructure, DNS, TLS & Web Hardening | false | n/a | no owned product infra | GitHub hosts the public git remote |
| Gate 12 — Resilience, DDoS, Abuse & Cost Defense | false | n/a | no public service | high_risk: false |
| Gate 13 — Webhooks, Background Jobs & Integrations | false | n/a | CI only | high_risk: false |
| Gate 14 — Privacy, Legal & Data Lifecycle | false | n/a | no PII/production data | high_risk: false |
| Gate 15 — AI/RAG/Agent Security | true | open | threat-model.md, gate-applicability.yml | Trifecta recorded; not a production agent product |
| Gate 16 — Multi-Tenant & Internal Permission Isolation | false | n/a | no tenants | high_risk: false |
| Gate 17 — Observability, Logs & Incident Readiness | true | recorded | GitHub Actions logs only | Not production-ready |
| Gate 18 — Backup, Recovery, Deletion & Rotation | false | n/a | no product datastore | high_risk: false |
| Gate 19 — Business Logic Abuse | false | n/a | no payments/plans | high_risk: false |
| Gate 20 — Launch Decision | true | BLOCKED | this file | Not a production launch |
| Gate 21 — Continuous Monitoring | false | n/a | no live users | high_risk: false |

## Findings

| Severity | Count | Launch Impact |
| --- | --- | --- |
| Critical | 0 recorded in this file | Blocks launch if greater than 0 until fixed and verified, removed from launch scope, or downgraded by new evidence |
| High | scanner/gate results live in LaunchGuardian reports, not claimed clean here | Blocks launch unless explicitly accepted by a human owner |
| Medium | unknown until scanners run | Track mitigation or follow-up |
| Low | unknown until scanners run | Track if useful |

This file does **not** pre-clear scanner results. Remaining BLOCKED after LGF files exist should be real scanner/gate findings.

## Skipped High-Risk Gates

| Gate | Reason | Confirmed By | Date |
| --- | --- | --- | --- |
| None | Conditional gates marked applies: false use high_risk: false with repo evidence that the trigger is absent. Always-on gates are not skipped. |  |  |

## Accepted Risks

See `sdd-plus/security/accepted-risks.md`. Residual agent-host risk on the shared VM is recorded; it is not accepted as a production launch risk.

## Rollback Or Disable Plan

- Revert the commit on `main` (no force-push).
- Disable `.github/workflows/drydock.yml` if CI must stop.
- Archive or delete the public GitHub repo if the sandbox is retired.
- VM ledger at `/home/box/drydock-state/drydock-grok-sandbox/` stays outside git.
- There is no production traffic to drain.

## Final Approval

- Approved by: **not approved**
- Approval date: none
- Conditions: Production launch is out of scope. This record exists so LaunchGuardian project-mode has required LGF files (`lgf_config_valid`) without faking a clean ship.
