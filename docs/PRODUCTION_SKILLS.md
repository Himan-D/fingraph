# Production Engineering Skills Matrix

This matrix defines the skill groups required to move FinGraph from prototype to production.

## 1) Architecture and Backend Engineering
- Domain-driven API and data contracts
- FastAPI async performance and lifecycle design
- SQLAlchemy query optimization and transaction design
- Database schema evolution and migrations
- Graph modeling and query tuning (Neo4j)
- Cache strategy and invalidation (Redis)
- Background scheduler and job durability patterns

## 2) Data Platform and Market Data Quality
- Source reliability scoring for each provider
- Data freshness SLAs and stale-data safeguards
- Deterministic fallback strategy (no random financial fields)
- Historical data normalization and reconciliation
- Idempotent ingestion pipelines

## 3) Security Engineering
- Secrets management and rotation
- Secure defaults in configuration
- Dependency vulnerability scanning
- API rate limiting and abuse prevention
- Authentication/authorization strategy
- Audit logging for sensitive operations

## 4) Reliability and Operations
- Structured logs, metrics, traces
- SLO definitions and alert thresholds
- Health checks and dependency readiness checks
- Capacity planning and load testing
- Backup, restore, and disaster recovery runbooks

## 5) Frontend Product Engineering
- Type-safe API client contracts
- Real-time UX behavior with stale/loading states
- Error boundaries and resilient rendering
- Performance budgets and bundle optimization
- Accessibility and cross-device validation

## 6) Quality and Delivery
- Unit/integration/API-contract/end-to-end tests
- CI pipelines for build and test gates
- Release checklist and rollback procedure
- Feature flags and staged rollout strategy
- Documentation for onboarding and operations

## 7) Product Readiness
- KPI instrumentation and analytics
- Alert precision/recall tuning
- Entitlements and plan enforcement
- Support workflow and incident communication
- Compliance-aware retention and data policies
