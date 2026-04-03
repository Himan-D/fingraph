# FinGraph Production Readiness Plan

## Goal
Move FinGraph to production readiness with measurable quality gates, operational safety, and predictable releases.

## Phase 1: Critical Hardening (Week 1)
- Remove all hardcoded credentials and enforce secure defaults.
- Fix runtime schema mismatches and dead code paths.
- Ensure local stack parity with documented dependencies.
- Add baseline CI and smoke tests.

Exit criteria:
- No credentials in source code.
- Backend boots in clean environment.
- CI passes on backend tests and frontend build.

## Phase 2: Data Trust and API Correctness (Week 2)
- Replace random mock values in production endpoints with deterministic data.
- Add explicit data_quality and data_freshness metadata in API responses.
- Define and enforce timeout/retry/backoff rules for external data sources.

Exit criteria:
- Core endpoints have deterministic outputs.
- API contracts documented and validated.

## Phase 3: Reliability and Scalability (Week 3)
- Add structured logging, metrics, and traces.
- Remove N+1 query hotspots and add indexes where needed.
- Add background job observability and failure handling.

Exit criteria:
- P95 latency and error-rate dashboards available.
- Scheduler job failures visible and actionable.

## Phase 4: Security and Governance (Week 4)
- Add authentication/authorization strategy for protected actions.
- Add rate limiting and abuse controls.
- Add dependency and container vulnerability scanning.

Exit criteria:
- Security checks are part of CI.
- Sensitive endpoints are protected.

## Phase 5: Release and Operations Readiness (Week 5)
- Create production deployment workflow with rollback steps.
- Define backup/restore processes and validate them.
- Finalize runbooks, on-call flow, and incident templates.

Exit criteria:
- Successful staging drill for deployment and rollback.
- Backup restore validated in non-dev environment.

## Immediate Work Started
- Secure defaults applied in backend config.
- Scheduler dependency issue fixed.
- Scheduler/news schema mismatch fixed.
- Webhook dead code removed.
- Frontend duplicate call removed.
- Docker compose updated with PostgreSQL service.
- CI and baseline tests added.
