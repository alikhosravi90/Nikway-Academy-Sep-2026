# NIKWAY Master System

## Purpose

The Master System is the governed parent-definition layer for platform objects.
It is distinct from the existing `NIKWAY-MASTER.yaml`, which remains the
architecture-synthesis artifact.

```text
Master → Layout / Defaults → Template / Starter → Instance
                                      ↓
                            Override / Extension / Guidance
```

## Canonical concepts

- **MasterDefinition**: canonical contract, capabilities, validation rules,
  allowed overrides and extensions.
- **MasterVersion**: immutable version of a master contract.
- **LayoutDefinition**: presentation/organization metadata that consumes a
  master; it cannot change the contract.
- **DefaultDefinition**: creation-time values only.
- **TemplateDefinition**: reusable configured starting point linked to a master
  version.
- **StarterDefinition**: explicitly marked quick-start template.
- **ExampleDefinition**: reference content, never production instance data.
- **GuidanceDefinition**: contextual narrator metadata.
- **InstanceProvenance**: immutable trace from instance to template/master
  version.
- **OverrideDefinition**: controlled replacement of explicitly overridable
  paths.
- **ExtensionDefinition**: additive data/capability allowed by the master.

## Resolution

Resolution is deterministic and does not mutate source definitions:

1. resolve template and master version;
2. copy master schema defaults;
3. apply template data;
4. apply declared defaults;
5. apply permitted overrides;
6. apply permitted extensions;
7. attach guidance;
8. validate required fields and allowed paths;
9. return the resolved object and provenance.

Existing instances retain their master and template versions. No implicit
migration is performed. Breaking changes require a new master version and an
explicit migration policy.

## Representative vertical slices

The generic foundation is proven with `Course`, `Form`, and `Organization`
definitions. The runtime implementation is deliberately storage-neutral in
this phase so it can later use existing PostgreSQL/audit boundaries without
creating a competing persistence mechanism.

## Governance

Master creation, publication, versioning, overrides and extensions are governed
configuration changes. The caller must enforce existing organization/role
authorization before invoking mutating APIs. The pure domain foundation does
not bypass or duplicate authentication.
