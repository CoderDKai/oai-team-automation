from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from src.core.config import BASE_DIR
from src.core.logger import log
from src.core.models import MigrationRecord, ValidationError, now_iso


class MigrationStore:
    """迁移记录存储 (JSON 文件)。"""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or (BASE_DIR / "migration_records.json")
        self._records: Dict[str, MigrationRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            for item in payload.get("records", []):
                record = MigrationRecord.from_dict(item)
                self._records[record.id] = record
        except (OSError, json.JSONDecodeError, ValidationError) as exc:
            log.warning(f"迁移记录加载失败: {exc}")

    def save(self) -> None:
        data = {
            "records": [record.to_dict() for record in self._records.values()],
            "updated_at": now_iso(),
        }
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def list_records(self) -> List[MigrationRecord]:
        return list(self._records.values())

    def get_record(self, record_id: str) -> Optional[MigrationRecord]:
        return self._records.get(record_id)

    def upsert(self, record: MigrationRecord) -> MigrationRecord:
        self._records[record.id] = record
        self.save()
        return record

    def create_record(
        self,
        record_id: str,
        legacy_path: str,
        new_path: str,
        capability_id: str = "",
        status: str = "pending",
        notes: str = "",
    ) -> MigrationRecord:
        record = MigrationRecord(
            id=record_id,
            legacy_path=legacy_path,
            new_path=new_path,
            status=status,
            capability_id=capability_id,
            notes=notes,
        )
        self.upsert(record)
        return record

    def verify(self, record_id: str, verified_by: str, notes: str = "") -> MigrationRecord:
        record = self._records.get(record_id)
        if not record:
            raise KeyError(f"migration record not found: {record_id}")
        record.status = "verified"
        record.verified_by = verified_by
        record.verified_at = now_iso()
        if notes:
            record.notes = notes
        return self.upsert(record)
