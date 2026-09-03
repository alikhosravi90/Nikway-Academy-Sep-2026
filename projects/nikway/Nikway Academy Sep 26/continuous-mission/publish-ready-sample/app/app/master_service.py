"""Application service boundary for authorized Master System operations."""

from dataclasses import asdict
from typing import Any

from app.authorization import MASTER_CREATE, MASTER_READ, MASTER_VERSION_CREATE, authorize
from app.master_system import MasterDefinition, MasterRegistry, MasterVersion


class MasterService:
    def __init__(self, registry: MasterRegistry | None = None) -> None:
        self.registry = registry or MasterRegistry()

    @staticmethod
    def _authorize(
        membership: dict[str, str], permission: str, organization_id: str
    ) -> None:
        authorize(
            membership,
            permission,
            requested_organization_id=organization_id,
        )

    @staticmethod
    def _serialize_master(master: MasterDefinition) -> dict[str, Any]:
        return {
            "id": master.id,
            "name": master.name,
            "object_type": master.object_type,
            "current_version": master.current_version,
            "organization_id": master.organization_id,
            "versions": {
                version: asdict(definition)
                for version, definition in master.versions.items()
            },
        }

    def list_masters(
        self, membership: dict[str, str], organization_id: str
    ) -> list[dict[str, Any]]:
        self._authorize(membership, MASTER_READ, organization_id)
        return [
            self._serialize_master(item)
            for item in self.registry.list_masters()
            if item.organization_id in {None, organization_id}
        ]

    def get_master(
        self, membership: dict[str, str], organization_id: str, master_id: str
    ) -> dict[str, Any]:
        self._authorize(membership, MASTER_READ, organization_id)
        master = self.registry.get_master(master_id)
        if master.organization_id not in {None, organization_id}:
            raise KeyError(master_id)
        return self._serialize_master(master)

    def create_master(
        self,
        membership: dict[str, str],
        organization_id: str,
        master: MasterDefinition,
    ) -> dict[str, Any]:
        self._authorize(membership, MASTER_CREATE, organization_id)
        master.organization_id = organization_id
        return self._serialize_master(self.registry.register_master(master))

    def create_version(
        self,
        membership: dict[str, str],
        organization_id: str,
        master_id: str,
        version: MasterVersion,
    ) -> dict[str, Any]:
        self._authorize(membership, MASTER_VERSION_CREATE, organization_id)
        master = self.registry.get_master(master_id)
        if master.organization_id not in {None, organization_id}:
            raise KeyError(master_id)
        return self._serialize_master(self.registry.version_master(master_id, version))
