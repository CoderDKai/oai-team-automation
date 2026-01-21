from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


_ALLOWED_MODULE_STATUS = {"active", "deprecated", "legacy"}
_ALLOWED_ITEM_STATUS = {"active", "deprecated"}
_ALLOWED_ITEM_SOURCE = {"legacy", "refactored"}
_ALLOWED_MIGRATION_STATUS = {"pending", "migrated", "verified", "failed"}


class ValidationError(ValueError):
    pass


def _require(data: Dict[str, Any], fields: List[str], name: str) -> None:
    missing = [field for field in fields if not data.get(field)]
    if missing:
        raise ValidationError(f"{name} missing required fields: {', '.join(missing)}")


def _validate_enum(value: str, allowed: set[str], field: str) -> None:
    if value not in allowed:
        raise ValidationError(f"Invalid {field}: {value}")


@dataclass
class Capability:
    id: str
    name: str
    entrypoint: str
    status: str
    description: str = ""
    owner: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Capability":
        _require(data, ["id", "name", "entrypoint", "status"], "Capability")
        _validate_enum(data["status"], _ALLOWED_MODULE_STATUS, "status")
        return cls(
            id=data["id"],
            name=data["name"],
            entrypoint=data["entrypoint"],
            status=data["status"],
            description=data.get("description", ""),
            owner=data.get("owner", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner": self.owner,
            "entrypoint": self.entrypoint,
            "status": self.status,
        }


@dataclass
class ConfigModule:
    id: str
    name: str
    purpose: str
    entrypoint: str
    status: str
    owner: str = ""
    updated_at: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigModule":
        _require(data, ["id", "name", "purpose", "entrypoint", "status"], "ConfigModule")
        _validate_enum(data["status"], _ALLOWED_MODULE_STATUS, "status")
        return cls(
            id=data["id"],
            name=data["name"],
            purpose=data["purpose"],
            entrypoint=data["entrypoint"],
            status=data["status"],
            owner=data.get("owner", ""),
            updated_at=data.get("updated_at", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "id": self.id,
            "name": self.name,
            "purpose": self.purpose,
            "owner": self.owner,
            "entrypoint": self.entrypoint,
            "status": self.status,
        }
        if self.updated_at:
            payload["updated_at"] = self.updated_at
        return payload


@dataclass
class ConfigItem:
    id: str
    module_id: str
    name: str
    scope: str
    source: str
    status: str
    description: str = ""
    constraints: str = ""
    default_value: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfigItem":
        _require(data, ["id", "module_id", "name", "scope", "source", "status"], "ConfigItem")
        _validate_enum(data["source"], _ALLOWED_ITEM_SOURCE, "source")
        _validate_enum(data["status"], _ALLOWED_ITEM_STATUS, "status")
        return cls(
            id=data["id"],
            module_id=data["module_id"],
            name=data["name"],
            scope=data["scope"],
            source=data["source"],
            status=data["status"],
            description=data.get("description", ""),
            constraints=data.get("constraints", ""),
            default_value=data.get("default_value", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "id": self.id,
            "module_id": self.module_id,
            "name": self.name,
            "description": self.description,
            "scope": self.scope,
            "constraints": self.constraints,
            "default_value": self.default_value,
            "source": self.source,
            "status": self.status,
        }
        return payload


@dataclass
class MigrationRecord:
    id: str
    legacy_path: str
    new_path: str
    status: str
    capability_id: str = ""
    verified_by: str = ""
    verified_at: str = ""
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MigrationRecord":
        _require(data, ["id", "legacy_path", "new_path", "status"], "MigrationRecord")
        _validate_enum(data["status"], _ALLOWED_MIGRATION_STATUS, "status")
        return cls(
            id=data["id"],
            legacy_path=data["legacy_path"],
            new_path=data["new_path"],
            status=data["status"],
            capability_id=data.get("capability_id", ""),
            verified_by=data.get("verified_by", ""),
            verified_at=data.get("verified_at", ""),
            notes=data.get("notes", ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "id": self.id,
            "legacy_path": self.legacy_path,
            "new_path": self.new_path,
            "status": self.status,
        }
        if self.capability_id:
            payload["capability_id"] = self.capability_id
        if self.verified_by:
            payload["verified_by"] = self.verified_by
        if self.verified_at:
            payload["verified_at"] = self.verified_at
        if self.notes:
            payload["notes"] = self.notes
        return payload


@dataclass
class MigrationRequest:
    legacy_reference: str
    target_reference: str
    items: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MigrationRequest":
        _require(data, ["legacy_reference", "target_reference"], "MigrationRequest")
        return cls(
            legacy_reference=data["legacy_reference"],
            target_reference=data["target_reference"],
            items=list(data.get("items", [])),
        )

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "legacy_reference": self.legacy_reference,
            "target_reference": self.target_reference,
        }
        if self.items:
            payload["items"] = self.items
        return payload


@dataclass
class MigrationPreview:
    status: str
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "notes": self.notes}


@dataclass
class MigrationVerification:
    verified_by: str
    notes: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MigrationVerification":
        _require(data, ["verified_by"], "MigrationVerification")
        return cls(verified_by=data["verified_by"], notes=data.get("notes", ""))

    def to_dict(self) -> Dict[str, Any]:
        payload = {"verified_by": self.verified_by}
        if self.notes:
            payload["notes"] = self.notes
        return payload


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
