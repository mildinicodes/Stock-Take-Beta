# Stock Take Beta

Standalone Massimo's Rail desktop stock-audit tool for shorts.

## Current phase

This first commit intentionally contains only the clean project structure, local progress storage, and basic cream/dark-green desktop app shell. It does **not** connect to or modify Vinted, Etsy, eBay, Inventory System Beta, or the relister.

## Planned workflow

1. Import listing data from Vinted, Etsy and eBay.
2. Normalize and match listings by SKU.
3. Display all online SKUs in SKU order.
4. Tick each SKU as physical stock is checked.
5. Save audit progress locally after every change.
6. Record physical stock found that has no online listing in a separate section.

## Run

Requires Python 3.11+.

```bash
python app.py
```

## Structure

```text
Stock-Take-Beta/
├── app.py
├── data/
│   └── .gitkeep
├── src/
│   └── stock_take_beta/
│       ├── app.py
│       ├── config.py
│       ├── data/
│       │   └── __init__.py
│       ├── services/
│       │   ├── __init__.py
│       │   └── progress_store.py
│       └── ui/
│           ├── __init__.py
│           └── main_window.py
├── tests/
│   └── test_progress_store.py
├── .gitignore
├── README.md
└── requirements.txt
```
