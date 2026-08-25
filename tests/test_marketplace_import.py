from src.stock_take_beta.services.marketplace_import import _extract_ebay_sku, _natural_sku_key


def test_ebay_generated_uuid_is_ignored_for_real_seller_sku():
    row = {
        "sku": "550e8400-e29b-41d4-a716-446655440000",
        "details": {"customLabel": "jor009"},
    }
    assert _extract_ebay_sku(row) == "JOR009"


def test_generated_uuid_without_real_sku_becomes_missing():
    row = {"sku": "550e8400-e29b-41d4-a716-446655440000"}
    assert _extract_ebay_sku(row) is None


def test_sku_sort_is_natural():
    values = ["JOR100", "JOR9", "JOR10", "JOR002"]
    assert sorted(values, key=_natural_sku_key) == ["JOR002", "JOR9", "JOR10", "JOR100"]
