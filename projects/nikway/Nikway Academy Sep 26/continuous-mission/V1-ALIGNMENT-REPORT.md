# NIKWAY V1 Alignment Report

Date: 2026-09-02
Authority: `D:/NIKWAY Academy 2026/NIKWAY_V1_BUILD_SPEC.md`

## Current assessment

The repository contains a useful Academy prototype and architecture package, but the current backend is not yet V1 publishable.

| Area | Current state | V1 requirement | Action |
|---|---|---|---|
| Database | SQLite fallback | PostgreSQL only | Refactor persistence and migrations |
| Authentication | Demo identity endpoint | OIDC | Integrate OIDC and role mapping |
| Tenant isolation | Not proven | Selective PostgreSQL RLS | Add policies and cross-tenant tests |
| CORS | Wildcard origins | Environment-specific origins | Restrict production origins |
| Evidence | Basic database record | Text/file/link with object storage | Add storage contract and validation |
| Events | Not implemented as V1 Event table | xAPI-shaped Postgres events | Add event model and emitters |
| Modules | Prototype models in one file | Explicit bounded modules | Split by V1 module ownership |
| Runtime | Docker Gordon includes extra services | One container and one database | Isolate V1 deployment |
| AI/Graph/Vector | Architecture artifacts exist | Explicit V1 non-goals | Mark deferred and exclude runtime |
| Restore | Documented concept | Tested restore evidence | Execute and attach evidence |

## Release decision

`ready_for_review`, not `publishable`.

The package must not be externally published until all high-priority actions are closed and human go/no-go approval is recorded.
