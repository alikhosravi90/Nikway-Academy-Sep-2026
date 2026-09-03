# V1 Module Boundary Skeleton

Each directory is a bounded context. A module owns its tables and exposes application interfaces; modules must not import another module's ORM models or query another module's tables directly.

Required V1 modules:

`identity`, `organization`, `journey`, `evidence`, `assessment`, `progression`, `content`, `reporting`, `audit`.
