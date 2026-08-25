from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from ..integrations.crosslist import CrosslistBrowserClient, valid_human_sku
from ..models import AuditItem, MarketplaceListing


_PREFERRED_EBAY_SKU_KEYS = {
    "customlabel", "customlabelsku", "sellersku", "merchantsku", "inventorysku",
    "itemsku", "listingsku", "originalsku", "stockkeepingunit",
}


def _find_listing_array(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("items", "Items", "data", "Data", "results", "Results", "records", "Records"):
        value = payload.get(key)
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            return value
    for value in payload.values():
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            return value
    return []


def _extract_ebay_sku(raw: dict[str, Any]) -> str | None:
    ranked: list[tuple[int, str]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(child, (dict, list)):
                    candidate = valid_human_sku(child)
                    if candidate:
                        compact = str(key).lower().replace("_", "").replace("-", "").replace(" ", "")
                        if compact in _PREFERRED_EBAY_SKU_KEYS:
                            ranked.append((0, candidate))
                        elif "seller" in compact and "sku" in compact:
                            ranked.append((1, candidate))
                        elif "custom" in compact and ("label" in compact or "sku" in compact):
                            ranked.append((1, candidate))
                        elif "sku" in compact:
                            ranked.append((2, candidate))
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(raw)
    if ranked:
        ranked.sort(key=lambda pair: pair[0])
        return ranked[0][1]
    return valid_human_sku(raw.get("sku"))


def _extract_sku(marketplace: str, raw: dict[str, Any]) -> str | None:
    if marketplace == "ebay":
        return _extract_ebay_sku(raw)
    return valid_human_sku(raw.get("sku"))


def _natural_sku_key(sku: str) -> tuple:
    import re
    parts = re.split(r"(\d+)", sku.upper())
    return tuple(int(part) if part.isdigit() else part for part in parts)


class MarketplaceImportService:
    def __init__(self, profile_dir: Path, progress: Callable[[str], None] | None = None) -> None:
        self.client = CrosslistBrowserClient(profile_dir, progress=progress)

    def refresh_shorts(self) -> dict[str, Any]:
        all_rows: list[MarketplaceListing] = []
        missing_sku: list[MarketplaceListing] = []
        counts: dict[str, int] = {}

        for marketplace in ("vinted", "ebay", "etsy"):
            payload = self.client.fetch_marketplace(marketplace)
            raw_rows = _find_listing_array(payload)
            shorts_rows = 0
            for raw in raw_rows:
                title = str(raw.get("title") or "").strip()
                if "shorts" not in title.lower():
                    continue
                shorts_rows += 1
                listing_id = str(raw.get("marketplaceId") or raw.get("marketplaceID") or raw.get("id") or "")
                listing = MarketplaceListing(
                    marketplace=marketplace,
                    listing_id=listing_id,
                    title=title or f"Untitled {marketplace.title()} listing",
                    sku=_extract_sku(marketplace, raw),
                    url=str(raw.get("marketplaceUrl") or ""),
                    cover_image=(str(raw.get("coverImage")).strip() if raw.get("coverImage") else None),
                )
                all_rows.append(listing)
                if not listing.sku:
                    missing_sku.append(listing)
            counts[marketplace] = shorts_rows

        grouped: dict[str, list[MarketplaceListing]] = defaultdict(list)
        for row in all_rows:
            if row.sku:
                grouped[row.sku].append(row)

        items: list[AuditItem] = []
        duplicate_flags: list[dict[str, Any]] = []
        for sku in sorted(grouped, key=_natural_sku_key):
            rows = grouped[sku]
            by_market: dict[str, list[MarketplaceListing]] = defaultdict(list)
            for row in rows:
                by_market[row.marketplace].append(row)
            first = rows[0]
            item = AuditItem(
                sku=sku,
                title=first.title,
                cover_image=next((row.cover_image for row in rows if row.cover_image), None),
                marketplaces=dict(by_market),
            )
            items.append(item)
            for marketplace in item.duplicate_marketplaces:
                duplicate_flags.append({
                    "sku": sku,
                    "marketplace": marketplace,
                    "count": len(item.marketplaces[marketplace]),
                })

        return {
            "items": items,
            "missing_sku": missing_sku,
            "duplicates": duplicate_flags,
            "counts": counts,
        }
