from __future__ import annotations

import uuid
from typing import Optional

from src.core.logger import log
from src.core.migration_store import MigrationStore
from src.core.models import MigrationPreview, MigrationRecord, MigrationRequest, MigrationVerification


def preview_migration(request: MigrationRequest) -> MigrationPreview:
    notes = []
    status = "ok"

    if not request.items:
        status = "warning"
        notes.append("未提供具体配置项，将按全量迁移处理")

    if request.legacy_reference == request.target_reference:
        status = "warning"
        notes.append("legacy_reference 与 target_reference 相同")

    return MigrationPreview(status=status, notes=notes)


def execute_migration(
    request: MigrationRequest, store: Optional[MigrationStore] = None
) -> MigrationRecord:
    store = store or MigrationStore()
    record_id = str(uuid.uuid4())
    record = store.create_record(
        record_id=record_id,
        legacy_path=request.legacy_reference,
        new_path=request.target_reference,
        status="migrated",
        notes="自动创建迁移记录",
    )
    log.success(f"迁移记录已创建: {record.id}")
    return record


def verify_migration(
    record_id: str,
    verification: MigrationVerification,
    store: Optional[MigrationStore] = None,
) -> MigrationRecord:
    store = store or MigrationStore()
    record = store.verify(record_id, verification.verified_by, verification.notes)
    log.success(f"迁移记录已验收: {record.id}")
    return record
