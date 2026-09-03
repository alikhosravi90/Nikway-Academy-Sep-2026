"""Governed Master -> Template -> Instance resolution foundation.

This module is intentionally storage-neutral.  Persistence and authorization
remain the responsibility of the existing application boundaries.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Callable


AuditHook = Callable[[str, str, dict[str, Any]], None]


class MasterSystemError(ValueError):
    """Base error for invalid master-system definitions or mutations."""


@dataclass(frozen=True)
class MasterVersion:
    version: str
    schema: dict[str, Any]
    required_fields: tuple[str, ...] = ()
    defaults: dict[str, Any] = field(default_factory=dict)
    allowed_states: tuple[str, ...] = ()
    overridable_paths: tuple[str, ...] = ()
    extension_paths: tuple[str, ...] = ()
    guidance: tuple[str, ...] = ()


@dataclass
class MasterDefinition:
    id: str
    name: str
    object_type: str
    current_version: str
    versions: dict[str, MasterVersion]
    layouts: dict[str, "LayoutDefinition"] = field(default_factory=dict)
    organization_id: str | None = None

    def version(self, version: str | None = None) -> MasterVersion:
        selected = version or self.current_version
        try:
            return self.versions[selected]
        except KeyError as exc:
            raise MasterSystemError(f"Unknown master version: {selected}") from exc


@dataclass(frozen=True)
class LayoutDefinition:
    id: str
    master_id: str
    name: str
    fields: tuple[str, ...]


@dataclass(frozen=True)
class DefaultDefinition:
    id: str
    master_id: str
    values: dict[str, Any]


@dataclass(frozen=True)
class TemplateDefinition:
    id: str
    master_id: str
    master_version: str
    name: str
    data: dict[str, Any]
    version: str = "1.0.0"
    defaults: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StarterDefinition:
    id: str
    template_id: str
    name: str


@dataclass(frozen=True)
class ExampleDefinition:
    id: str
    master_id: str
    name: str
    data: dict[str, Any]


@dataclass(frozen=True)
class GuidanceDefinition:
    id: str
    target_type: str
    target_id: str
    content: dict[str, Any]


@dataclass(frozen=True)
class InstanceProvenance:
    instance_id: str
    master_id: str
    master_version: str
    template_id: str | None
    template_version: str | None
    overrides: tuple[str, ...] = ()
    extensions: tuple[str, ...] = ()


@dataclass(frozen=True)
class OverrideDefinition:
    path: str
    value: Any


@dataclass(frozen=True)
class ExtensionDefinition:
    path: str
    value: Any


@dataclass(frozen=True)
class InstanceDefinition:
    id: str
    master_id: str
    master_version: str
    template_id: str | None
    template_version: str | None
    data: dict[str, Any]
    overrides: tuple[OverrideDefinition, ...] = ()
    extensions: tuple[ExtensionDefinition, ...] = ()

    @property
    def provenance(self) -> InstanceProvenance:
        return InstanceProvenance(
            instance_id=self.id,
            master_id=self.master_id,
            master_version=self.master_version,
            template_id=self.template_id,
            template_version=self.template_version,
            overrides=tuple(item.path for item in self.overrides),
            extensions=tuple(item.path for item in self.extensions),
        )


def _path_parts(path: str) -> list[str]:
    parts = path.split(".") if path else []
    if not parts or any(not part or part.startswith("_") for part in parts):
        raise MasterSystemError(f"Invalid property path: {path}")
    return parts


def _get(data: dict[str, Any], path: str) -> Any:
    current: Any = data
    for part in _path_parts(path):
        if not isinstance(current, dict) or part not in current:
            raise MasterSystemError(f"Property path does not exist: {path}")
        current = current[part]
    return current


def _set(data: dict[str, Any], path: str, value: Any, *, require_absent: bool = False) -> None:
    parts = _path_parts(path)
    current = data
    for part in parts[:-1]:
        child = current.get(part)
        if child is None:
            child = {}
            current[part] = child
        if not isinstance(child, dict):
            raise MasterSystemError(f"Cannot traverse property path: {path}")
        current = child
    if require_absent and parts[-1] in current:
        raise MasterSystemError(f"Extension would replace inherited property: {path}")
    current[parts[-1]] = deepcopy(value)


def _merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class MasterRegistry:
    """Deterministic registry and resolver for the Master System foundation."""

    def __init__(self, audit: AuditHook | None = None) -> None:
        self.masters: dict[str, MasterDefinition] = {}
        self.templates: dict[str, TemplateDefinition] = {}
        self.instances: dict[str, InstanceDefinition] = {}
        self.guidance: dict[str, GuidanceDefinition] = {}
        self.audit = audit

    def _record(self, action: str, entity_id: str, payload: dict[str, Any]) -> None:
        if self.audit:
            self.audit(action, entity_id, deepcopy(payload))

    def register_master(self, master: MasterDefinition) -> MasterDefinition:
        if master.id in self.masters:
            raise MasterSystemError(f"Master already exists: {master.id}")
        master.version()
        self.masters[master.id] = deepcopy(master)
        self._record("master_registered", master.id, {"version": master.current_version})
        return deepcopy(master)

    def version_master(self, master_id: str, version: MasterVersion) -> MasterDefinition:
        master = self._master(master_id)
        if version.version in master.versions:
            raise MasterSystemError(f"Master version already exists: {version.version}")
        master.versions[version.version] = version
        master.current_version = version.version
        self._record("master_versioned", master_id, {"version": version.version})
        return deepcopy(master)

    def create_template(self, template: TemplateDefinition) -> TemplateDefinition:
        master = self._master(template.master_id)
        master.version(template.master_version)
        if template.id in self.templates:
            raise MasterSystemError(f"Template already exists: {template.id}")
        self.templates[template.id] = deepcopy(template)
        self._record("template_created", template.id, {"master_id": template.master_id})
        return deepcopy(template)

    def get_master(self, master_id: str) -> MasterDefinition:
        return deepcopy(self._master(master_id))

    def list_masters(self) -> list[MasterDefinition]:
        return [deepcopy(self.masters[key]) for key in sorted(self.masters)]

    def get_template(self, template_id: str) -> TemplateDefinition:
        try:
            return deepcopy(self.templates[template_id])
        except KeyError as exc:
            raise MasterSystemError(f"Unknown template: {template_id}") from exc

    def validate_instance(self, instance: InstanceDefinition) -> bool:
        self.resolve_instance(instance)
        return True

    def create_instance(
        self,
        instance_id: str,
        master_id: str,
        *,
        template_id: str | None = None,
        data: dict[str, Any] | None = None,
        overrides: tuple[OverrideDefinition, ...] = (),
        extensions: tuple[ExtensionDefinition, ...] = (),
    ) -> InstanceDefinition:
        if instance_id in self.instances:
            raise MasterSystemError(f"Instance already exists: {instance_id}")
        master = self._master(master_id)
        template = self.templates.get(template_id) if template_id else None
        if template_id and template is None:
            raise MasterSystemError(f"Unknown template: {template_id}")
        version = template.master_version if template else master.current_version
        if template and template.master_id != master_id:
            raise MasterSystemError("Template does not belong to master")
        definition = InstanceDefinition(
            id=instance_id,
            master_id=master_id,
            master_version=version,
            template_id=template_id,
            template_version=template.version if template else None,
            data=deepcopy(data or {}),
            overrides=tuple(overrides),
            extensions=tuple(extensions),
        )
        self.resolve_instance(definition)
        self.instances[instance_id] = deepcopy(definition)
        self._record("instance_created", instance_id, definition.provenance.__dict__)
        return deepcopy(definition)

    def attach_guidance(self, guidance: GuidanceDefinition) -> GuidanceDefinition:
        if guidance.id in self.guidance:
            raise MasterSystemError(f"Guidance already exists: {guidance.id}")
        self.guidance[guidance.id] = deepcopy(guidance)
        self._record("guidance_attached", guidance.id, {"target_id": guidance.target_id})
        return deepcopy(guidance)

    def resolve_instance(self, instance: InstanceDefinition) -> dict[str, Any]:
        master = self._master(instance.master_id)
        version = master.version(instance.master_version)
        template = self.templates.get(instance.template_id) if instance.template_id else None
        resolved = _merge(version.defaults, template.data if template else {})
        if template:
            resolved = _merge(resolved, template.defaults)
        resolved = _merge(resolved, instance.data)
        for override in instance.overrides:
            if override.path not in version.overridable_paths:
                raise MasterSystemError(f"Override is not permitted: {override.path}")
            _set(resolved, override.path, override.value)
        for extension in instance.extensions:
            if extension.path not in version.extension_paths:
                raise MasterSystemError(f"Extension is not permitted: {extension.path}")
            _set(resolved, extension.path, extension.value, require_absent=True)
        missing = [path for path in version.required_fields if _missing(resolved, path)]
        if missing:
            raise MasterSystemError("Required fields are missing: " + ", ".join(missing))
        return resolved

    def resolve_with_guidance(self, instance: InstanceDefinition) -> dict[str, Any]:
        resolved = self.resolve_instance(instance)
        master = self._master(instance.master_id)
        ids = set(master.version(instance.master_version).guidance)
        if instance.template_id:
            ids.update(
                item.id
                for item in self.guidance.values()
                if item.target_type == "template" and item.target_id == instance.template_id
            )
        resolved["_guidance"] = [
            deepcopy(self.guidance[item_id].content)
            for item_id in sorted(ids)
            if item_id in self.guidance
        ]
        return resolved

    def _master(self, master_id: str) -> MasterDefinition:
        try:
            return self.masters[master_id]
        except KeyError as exc:
            raise MasterSystemError(f"Unknown master: {master_id}") from exc


def _missing(data: dict[str, Any], path: str) -> bool:
    try:
        _get(data, path)
    except MasterSystemError:
        return True
    return False
