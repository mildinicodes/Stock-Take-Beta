from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class MarketplaceListing:
    marketplace: str
    listing_id: str
    title: str
    sku: str | None
    url: str = ""
    cover_image: str | None = None


@dataclass(slots=True)
class AuditItem:
    sku: str
    title: str
    cover_image: str | None = None
    marketplaces: dict[str, list[MarketplaceListing]] = field(default_factory=dict)

    @property
    def duplicate_marketplaces(self) -> list[str]:
        return sorted(name for name, rows in self.marketplaces.items() if len(rows) > 1)

    @property
    def marketplace_presence(self) -> dict[str, bool]:
        return {name: bool(self.marketplaces.get(name)) for name in ("vinted", "ebay", "etsy")}
