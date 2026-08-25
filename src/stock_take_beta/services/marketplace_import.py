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

_PREFERRED_VINTED_SKU_KEYS = {
    "sku", "sellersku", "merchantsku", "inventorysku", "itemsku",
    "listingsku", "originalsku", "stockkeepingunit", "customsku",
}


def _find_listing_array(payload: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("items", "Items", "data", "Data", "results", "Results", "records", "Records"):
        value = payload.get(key)
        if isinstance(value, list) and all(isinstance(item, dict) for item in value):
            return value
    for value in payload.values():
        if isinstance(value, list) and value and all(isinstance(item, dict) for item in value):
            sample = value[0]
            if "marketplaceId" in sample or "marketplace" in sample or "title" in sample:
                return value
    return []


def _compact_key(key: Any) -> str:
    return str(key).lower().replace("_", "").replace("-", "").replace(" ", "")


def _find_sku_candidates(raw: dict[str, Any], preferred_keys: set[str]) -> list[tuple[int, str]]:
    ranked: list[tuple[int, str]] = []

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                compact = _compact_key(key)
                if not isinstance(child, (dict, list)):
                    candidate = valid_human_sku(child)
                    if candidate:
                        if compact in preferred_keys:
                            ranked.append((0, candidate))
                        elif "seller" in compact and "sku" in compact:
                            ranked.append((1, candidate))
                        elif "custom" in compact and "sku" in compact:
                            ranked.append((1, candidate))
                        elif "sku" in compact:
                            ranked.append((2, candidate))
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(raw)
    ranked.sort(key=lambda pair: pair[0])
    return ranked


def _extract_ebay_sku(raw: dict[str, Any]) -> str | None:
    ranked = _find_sku_candidates(raw, _PREFERRED_EBAY_SKU_KEYS)
    return ranked[0][1] if ranked else valid_human_sku(raw.get("sku"))


def _extract_vinted_sku(raw: dict[str, Any]) -> str | None:
    direct = valid_human_sku(raw.get("sku"))
    if direct:
        return direct
    ranked = _find_sku_candidates(raw, _PREFERRED_VINTED_SKU_KEYS)
    return ranked[0][1] if ranked else None


def _extract_sku(marketplace: str, raw: dict[str, Any]) -> str | None:
    if marketplace == "ebay":
        return _extract_ebay_sku(raw)
    if marketplace == "vinted":
        return _extract_vinted_sku(raw)
    return valid_human_sku(raw.get("sku"))


def _natural_sku_key(sku: str) -> tuple:
    import re
    parts = re.split(r"(\d+)", sku.upper())
    return tuple(int(part) if part.isdigit() else part for part in parts)


def _is_non_unique_sku(sku: str) -> bool:
    """Return True for placeholder-style SKUs such as JOR.

    Real stock codes in this audit contain a numeric item identifier (JOR001,
    DCK466, etc.). A letters-only value can still be displayed, but it is not
    safe to use as a physical identity because many separate listings may share
    it. Those rows are therefore kept separate rather than merged.
    """
    return not any(char.isdigit() for char in sku)


def _listing_audit_id(row: MarketplaceListing) -> str:
    identity = row.listing_id or row.url or row.title
    return f"{row.sku}__{row.marketplace}__{identity}"


class MarketplaceImportService:
    def __init__(self, profile_dir: Path, progress: Callable[[str], None] | None = None) -> None:
        self.client = CrosslistBrowserClient(profile_dir, progress=progress)
        self.progress = progress or (lambda _message: None)

    def refresh_shorts(self) -> dict[str, Any]:
        all_rows: list[MarketplaceListing] = []
        missing_sku: list[MarketplaceListing] = []
        counts: dict[str, int] = {}
        captured_counts: dict[str, int] = {}
        sku_counts: dict[str, int] = {}

        for marketplace in ("vinted", "ebay", "etsy"):
            payload = self.client.fetch_marketplace(marketplace)
            raw_rows = _find_listing_array(payload)
            captured_counts[marketplace] = len(raw_rows)
            shorts_rows = 0
            rows_with_sku = 0

            for raw in raw_rows:
                title = str(raw.get("title") or "").strip()
                if "shorts" not in title.lower():
                    continue
                shorts_rows += 1
                sku = _extract_sku(marketplace, raw)
                if sku:
                    rows_with_sku += 1
                listing_id = str(raw.get("marketplaceId") or raw.get("marketplaceID") or raw.get("id") or "")
                listing = MarketplaceListing(
                    marketplace=marketplace,
                    listing_id=listing_id,
                    title=title or f"Untitled {marketplace.title()} listing",
                    sku=sku,
                    url=str(raw.get("marketplaceUrl") or ""),
                    cover_image=(str(raw.get("coverImage")).strip() if raw.get("coverImage") else None),
                )
                all_rows.append(listing)
                if not listing.sku:
                    missing_sku.append(listing)

            counts[marketplace] = shorts_rows
            sku_counts[marketplace] = rows_with_sku
            self.progress(
                f"{marketplace.title()}: {shorts_rows:,} shorts, {rows_with_sku:,} with SKU "
                f"({len(raw_rows):,} rows captured)."
            )

        grouped: dict[str, list[MarketplaceListing]] = defaultdict(list)
        for row in all_rows:
            if row.sku:
                grouped[row.sku].append(row)

        items: list[AuditItem] = []
        duplicate_flags: list[dict[str, Any]] = []

        for sku in sorted(grouped, key=_natural_sku_key):
            rows = grouped[sku]

            if _is_non_unique_sku(sku):
                # A placeholder such as JOR cannot tell us which physical pair
                # an online listing belongs to. Keep every listing visible as a
                # separate audit row, even when several share the same market.
                for row in sorted(rows, key=lambda value: (value.marketplace, value.listing_id, value.title)):
                    items.append(
                        AuditItem(
                            audit_id=_listing_audit_id(row),
                            sku=sku,
                            title=row.title,
                            cover_image=row.cover_image,
                            marketplaces={row.marketplace: [row]},
                            non_unique_sku=True,
                        )
                    )
                continue

            by_market: dict[str, list[MarketplaceListing]] = defaultdict(list)
            for row in rows:
                by_market[row.marketplace].append(row)
            first = rows[0]
            item = AuditItem(
                audit_id=sku,
                sku=sku,
                title=first.title,
                cover_image=next((row.cover_image for row in rows if row.cover_image), None),
                marketplaces=dict(by_market),
                non_unique_sku=False,
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
            "captured_counts": captured_counts,
            "sku_counts": sku_counts,
        }
