from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .marketplace_import import MarketplaceImportService
from .progress_store import ProgressStore


class AuditService:
    def __init__(self, store: ProgressStore, profile_dir: Path, progress: Callable[[str], None] | None = None) -> None:
        self.store = store
        self.profile_dir = profile_dir
        self.progress = progress or (lambda _message: None)

    def _state(self) -> dict[str, Any]:
        return self.store.load()

    def refresh_marketplaces(self) -> dict[str, Any]:
        importer = MarketplaceImportService(self.profile_dir, progress=self.progress)
        result = importer.refresh_shorts()
        state = self._state()
        state["marketplace_items"] = [
            {
                "audit_id": item.audit_id,
                "sku": item.sku,
                "title": item.title,
                "cover_image": item.cover_image,
                "non_unique_sku": item.non_unique_sku,
                "marketplaces": {
                    marketplace: [
                        {
                            "listing_id": row.listing_id,
                            "title": row.title,
                            "url": row.url,
                            "cover_image": row.cover_image,
                        }
                        for row in rows
                    ]
                    for marketplace, rows in item.marketplaces.items()
                },
            }
            for item in result["items"]
        ]
        state["missing_sku"] = [
            {
                "marketplace": row.marketplace,
                "listing_id": row.listing_id,
                "title": row.title,
                "url": row.url,
            }
            for row in result["missing_sku"]
        ]
        state["duplicates"] = result["duplicates"]
        state["marketplace_counts"] = result["counts"]
        state["marketplace_captured_counts"] = result.get("captured_counts", {})
        state["marketplace_sku_counts"] = result.get("sku_counts", {})
        state["last_refreshed_at"] = datetime.now(timezone.utc).isoformat()
        state["audit_completed_at"] = None
        self.store.save(state)
        return state

    def set_physical_status(self, audit_id: str, status: str) -> dict[str, Any]:
        status = status.lower().strip()
        if status not in {"found", "missing", "unchecked"}:
            raise ValueError("status must be found, missing or unchecked")
        state = self._state()
        audit = state.setdefault("audit", {})
        if status == "unchecked":
            audit.pop(audit_id, None)
        else:
            audit[audit_id] = status
            state["last_checked_audit_id"] = audit_id
            state["last_checked_at"] = datetime.now(timezone.utc).isoformat()
        self.store.save(state)
        return state

    def add_unlisted_sku(self, sku: str) -> dict[str, Any]:
        sku = sku.strip().upper()
        if not sku:
            raise ValueError("SKU is required")
        state = self._state()
        items = state.setdefault("unlisted_physical_stock", [])
        if sku not in items:
            items.append(sku)
            items.sort()
        state["last_unlisted_sku"] = sku
        self.store.save(state)
        return state

    def remove_unlisted_sku(self, sku: str) -> dict[str, Any]:
        state = self._state()
        items = state.setdefault("unlisted_physical_stock", [])
        state["unlisted_physical_stock"] = [value for value in items if value != sku]
        self.store.save(state)
        return state

    def complete_audit(self) -> dict[str, Any]:
        state = self._state()
        total = len(state.get("marketplace_items", []))
        audit = state.get("audit", {})
        valid_ids = {item.get("audit_id") or item.get("sku") for item in state.get("marketplace_items", [])}
        found = sum(1 for key, status in audit.items() if key in valid_ids and status == "found")
        missing = sum(1 for key, status in audit.items() if key in valid_ids and status == "missing")
        unchecked = max(0, total - found - missing)
        state["audit_completed_at"] = datetime.now(timezone.utc).isoformat()
        state["completion_summary"] = {
            "total_online_skus": total,
            "found": found,
            "missing": missing,
            "unchecked": unchecked,
            "unlisted_physical": len(state.get("unlisted_physical_stock", [])),
            "missing_sku": len(state.get("missing_sku", [])),
            "duplicate_flags": len(state.get("duplicates", [])),
        }
        self.store.save(state)
        return state
