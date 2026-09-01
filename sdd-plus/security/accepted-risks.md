# Accepted Risks

Throwaway LITE sandbox. Critical findings are not accepted as routine launch risks. This is **not** a production-launch acceptance log.

## Related Gates

- Gate 20 — Launch Decision

| ID | Date | Risk | Severity | Reason For Acceptance | Mitigation | Owner | Review Date | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AR-1 | 2026-09-01 | Public repository of a live-fire agent sandbox | medium | Intentional: public throwaway, not a client tree | No customer/LOQ data; ledger outside git; Gate 20 BLOCKED | Daniel Paez | 2026-09-01 | open-sandbox-only |
| AR-2 | 2026-09-01 | Shared VM agents have host access + GitHub outbound (Gate 15 legs) | high on host | Not accepted for production. Recorded so the trifecta is not hidden. | No production/customer data in tree; ledger outside git; public sandbox only; launch remains BLOCKED | Daniel Paez | 2026-09-01 | not-accepted-for-production |

## Notes

- High risks require a human owner, mitigation, due date, and rollback or containment plan.
- AR-2 is documented residual sandbox risk, **not** an approved production launch exception.
- No exceptional Critical override is requested.
