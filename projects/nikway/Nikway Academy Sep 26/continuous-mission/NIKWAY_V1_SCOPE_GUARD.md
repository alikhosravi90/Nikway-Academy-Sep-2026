# NIKWAY V1 Scope Guard

This file is binding for V1 implementation agents.

## Allowed

- One modular-monolith codebase
- One deployable container
- PostgreSQL
- OIDC authentication
- S3-compatible object storage
- Postgres-backed jobs and events
- OpenAPI REST API
- Structured JSON logs
- Selective PostgreSQL RLS
- The eight V1 domain modules plus audit

## Deferred

- Redis
- Neo4j
- pgvector
- RAG
- LLM and AI agents
- Microservices
- Kubernetes
- Kafka, RabbitMQ, and dedicated brokers
- SCORM and LTI
- SAML, LDAP, and multi-region deployment

## Gate

If an implementation needs a deferred capability, stop and record a challenge. Use a simpler PostgreSQL or in-process fallback where possible. Do not silently expand scope.
