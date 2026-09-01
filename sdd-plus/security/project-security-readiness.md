# Project Security Readiness

Throwaway LITE sandbox. Not a production LaunchGuardian ship record.

## Project

- Project: drydock-grok-sandbox
- Change or launch: bootstrap-lgf-packet
- Owner: Daniel Paez
- Reviewer: none assigned
- Date: 2026-09-01
- Readiness status: `blocked`

Allowed readiness statuses:

- `not_started`
- `inventory_in_progress`
- `gates_classified`
- `risks_open`
- `blocked`
- `approved_with_accepted_risks`
- `approved`

## Related Gates

- Gate 0 — Scope & Permission
- Gate 1 — Product, Asset & Data Inventory
- Gate 2 — Threat Modeling
- Gate 20 — Launch Decision
- Gate 21 — Continuous Monitoring

## Activation Triggers

Mark each trigger `yes`, `no`, or `unknown`.

| Trigger | Status | Evidence | Notes |
| --- | --- | --- | --- |
| Project will be deployed | no | README.md, PROJECT_CONTEXT.md | Public git + CI only |
| Project has users | no | PROJECT_CONTEXT.md | Owner/agents, not product users |
| Project handles personal or company data | no | data-inventory.yml | Ledger is outside the tree |
| Project has auth | no | auth-role-matrix.yml | GitHub auth is platform, not product |
| Project has APIs | no | product-inventory.yml | |
| Project has frontend build artifacts | no | no frontend tree | |
| Project has AI/RAG/agents | yes | PROJECT_CONTEXT.md, agents/, hooks/ | Choreography sandbox |
| Project has payments/billing | no | PROJECT_CONTEXT.md | |
| Project has file uploads/imports/exports | no | product-inventory.yml | |
| Project has integrations/webhooks/background jobs | no | CI is not a product webhook | |

## Onboarding Artifacts

| Artifact | Target File | Status | Owner | Notes |
| --- | --- | --- | --- | --- |
| Scope contract | `sdd-plus/security/scope-contract.yml` | created | Daniel Paez | Honest sandbox scope |
| Product inventory | `sdd-plus/security/product-inventory.yml` | created | Daniel Paez | |
| Data inventory | `sdd-plus/security/data-inventory.yml` | created | Daniel Paez | No PII/production data |
| Gate applicability matrix | `sdd-plus/security/gate-applicability.yml` | created | Daniel Paez | From output template |
| Threat model | `sdd-plus/security/threat-model.md` | created | Daniel Paez | |
| Auth role matrix | `sdd-plus/security/auth-role-matrix.yml` | created | Daniel Paez | Explicitly no product auth |
| Dependency policy | `sdd-plus/security/dependency-policy.yml` | created | Daniel Paez | |
| Accepted risks log | `sdd-plus/security/accepted-risks.md` | created | Daniel Paez | Not a production acceptance |
| Launch decision | `sdd-plus/security/launch-decision.md` | created | Daniel Paez | Decision: BLOCKED |

## Minimum LGF Packet Before Launch

- [x] Scope contract created (not a production approval).
- [x] Product inventory created.
- [x] Data inventory created or explicitly marked not applicable with evidence.
- [x] Gate applicability matrix created at `sdd-plus/security/gate-applicability.yml`.
- [x] Every gate marked `applies: true`, `applies: false`, or `applies: unknown`.
- [x] High-risk skipped gates: none. Conditional N/A gates use `high_risk: false` with repo evidence.
- [x] Threat model created.
- [x] Auth role matrix created (no product auth).
- [x] Dependency policy created.
- [x] Accepted risks log created, even when no risks are accepted for production.
- [x] Launch decision file created.
- [ ] Critical findings fixed and verified, removed from launch scope, or downgraded by new evidence. — N/A: not launching.
- [x] No exceptional Critical override requested.
- [x] Rollback or disable plan documented.
- [ ] Final launch owner approval recorded. — **intentionally absent**.

## Current Blockers

| Blocker | Severity | Required Action | Owner | Status |
| --- | --- | --- | --- | --- |
| Not a production launch | high | Do not ship; keep Gate 20 BLOCKED | Daniel Paez | open |
| Scanner results not pre-cleared | high | Let CI/local LaunchGuardian report real findings | Daniel Paez | open |

## Accepted Risks

See `sdd-plus/security/accepted-risks.md`. Residual VM agent risk is recorded and is not a production acceptance.

## Final Readiness Notes

Readiness is `blocked` on purpose. LGF files exist so missing-template BLOCKED goes away (`lgf_config_valid` can become true). Remaining BLOCKED must be real scanner/gate results or the honest non-launch decision.
