# Stock Take Beta

Standalone Massimo's Rail shorts stock-audit tool.

## Current build

The app now reads Crosslist's Import pages for Vinted, eBay and Etsy, keeps only listings with `Shorts` in the title, matches listings by SKU, and displays the combined marketplace picture in SKU order.

It is read-only with respect to marketplaces. It does not modify Inventory System Beta, the relister, Vinted, eBay or Etsy.

### Audit rules

- SKU is the sole physical-item identity.
- All SKU formats are accepted.
- Crosslist-generated UUID values on eBay are rejected and the genuine seller/custom SKU is recovered where available.
- Missing SKUs are flagged.
- Duplicate SKUs on the same marketplace are flagged.
- Physical status is `Found`, `Missing`, or unchecked.
- Physical stock not represented online is stored as SKU-only entries.
- Marketplace refreshes do not erase physical audit progress.
- A formal Complete Audit action saves a summary.

## Desktop + phone

Launching the app starts the Massimo's Rail desktop interface and a small local mobile web view. The desktop sidebar shows the phone URL. Open it on a phone connected to the same Wi-Fi as the laptop.

The phone view uses compact cards with SKU, title, marketplace presence and large Found/Missing buttons.

## First setup

Requires Python 3.11+, Google Chrome, and a Crosslist account.

```bash
pip install -r requirements.txt
python app.py
```

On the first marketplace refresh, a dedicated Chrome profile opens. Log into Crosslist in that Chrome window if required. The local session is reused on later refreshes. No credentials or browser-session data are committed to GitHub.

## Normal use

1. Launch with `python app.py`.
2. Click **Refresh Marketplace Data**.
3. Let the app read the Vinted, eBay and Etsy Crosslist Import pages.
4. Check shorts physically from desktop or phone.
5. Add physical-only SKUs under **Unlisted Physical Stock**.
6. Use **Complete Audit** when the stock take is finished.
