# V1 Module Boundaries

The application remains one deployable modular monolith.

| Module | Owns | Exposes |
|---|---|---|
| identity | users, sessions, OIDC claims | current identity |
| organization | organizations, memberships, roles | membership context |
| journey | journeys, steps, assignments | assigned journey |
| evidence | evidence records and upload references | submitted evidence |
| assessment | criteria and assessment results | assessment outcome |
| progression | progression events | next-step decision |
| content | journey-step content | learning content |
| reporting | no business tables | read-only reports |
| audit | events and audit records | append-only audit |

Cross-module access uses application interfaces. Modules do not query another module's tables or share ORM models.
