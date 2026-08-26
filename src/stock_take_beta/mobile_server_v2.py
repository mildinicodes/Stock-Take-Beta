from __future__ import annotations

import socket
import threading
import traceback
from html import escape
from typing import Any

from flask import Flask, Response, redirect, render_template_string, request, url_for

from .config import MOBILE_HOST, MOBILE_PORT
from .services.audit_service import AuditService

MARKETS = ("vinted", "ebay", "etsy")

TEMPLATE = r"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Massimo's Rail Stock Take</title>
<style>
:root{--cream:#F3EBDD;--light:#FBF7EF;--green:#173C2B;--soft:#DCE6DE;--muted:#6E776F;--border:#CFC6B7;--vinted:#09B1BA;--ebay:#3665F3;--etsy:#F1641E}
*{box-sizing:border-box}body{margin:0;background:var(--cream);color:var(--green);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:10;background:var(--green);color:white;padding:14px 16px 12px}.brand{font-size:11px;letter-spacing:1.6px;opacity:.75}.title{font-size:22px;font-weight:800}.meta{font-size:11px;opacity:.75;margin-top:3px}
.tabs{display:flex;gap:8px;padding:10px 12px 4px}.tabs a{flex:1;text-align:center;padding:10px;border-radius:10px;text-decoration:none;font-weight:800;color:var(--green);background:var(--light);border:1px solid var(--border)}
.filters{margin:8px 12px;padding:10px;background:var(--light);border:1px solid var(--border);border-radius:12px}.row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:5px 0}.label{width:86px;font-size:12px;font-weight:800}.fbtn{padding:8px 10px;border-radius:9px;text-decoration:none;font-size:12px;font-weight:800;background:white;border:1px solid currentColor}.vinted{color:var(--vinted)}.ebay{color:var(--ebay)}.etsy{color:var(--etsy)}.active.vinted{background:var(--vinted);color:white}.active.ebay{background:var(--ebay);color:white}.active.etsy{background:var(--etsy);color:white}.clear{color:var(--green);border-color:var(--border)}.shown{font-size:12px;color:var(--muted);font-weight:700;margin-top:7px}
.summary{padding:0 12px 2px;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.pill{background:var(--light);border:1px solid var(--border);border-radius:10px;padding:9px;text-align:center}.pill strong{display:block;font-size:19px}.pill span{font-size:10px;color:var(--muted)}
.list{padding:8px 12px 90px}.card{background:var(--light);border:1px solid var(--border);border-radius:14px;padding:12px;margin-bottom:9px}.top{display:flex;gap:10px;align-items:center}.thumb{width:54px;height:54px;border-radius:8px;object-fit:cover;background:var(--soft)}.sku{font-size:21px;font-weight:850}.title2{font-size:12px;color:var(--muted);line-height:1.2;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.flag{display:inline-block;margin-top:4px;font-size:10px;font-weight:800;padding:4px 7px;border-radius:999px;background:#f3d8ce;color:#7a2f1c}
.markets{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0}.market{font-size:11px;font-weight:800;border-radius:999px;padding:5px 8px;background:#eee;color:#777}.market.vinted.on{background:var(--vinted);color:white}.market.ebay.on{background:var(--ebay);color:white}.market.etsy.on{background:var(--etsy);color:white}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.actions button{border:0;border-radius:10px;padding:12px;font-size:15px;font-weight:800}.found{background:var(--green);color:white}.missing{background:#ead7d1;color:#6e2c20}.active-status{outline:3px solid #91a99a}.unchecked{text-align:center;font-size:11px;color:var(--muted);margin-top:7px}
.add{display:flex;gap:8px;margin:10px 12px}.add input{flex:1;border:1px solid var(--border);border-radius:10px;padding:13px;font-size:16px}.add button,.complete{border:0;border-radius:10px;background:var(--green);color:white;padding:12px 14px;font-weight:800}.unlisted{padding:2px 12px 90px}.urow{display:flex;justify-content:space-between;align-items:center;background:var(--light);border:1px solid var(--border);padding:12px;margin-bottom:8px;border-radius:10px;font-weight:800}.urow button{border:0;background:transparent;font-size:20px;color:#8c4b3b}.complete-wrap{position:fixed;left:0;right:0;bottom:0;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:linear-gradient(transparent,var(--cream) 25%)}.complete{width:100%;font-size:16px}
</style>
</head>
<body>
<header><div class="brand">MASSIMO'S RAIL</div><div class="title">Shorts Stock Audit</div><div class="meta">{{ meta }}</div></header>
<div class="tabs"><a href="{{ audit_url }}">Audit</a><a href="/unlisted">Unlisted Stock</a></div>
{% if page == 'audit' %}
<div class="filters">
<div class="row"><span class="label">Listed on:</span>{% for m in markets %}<a class="fbtn {{m}} {% if m in listed %}active{% endif %}" href="{{ toggles['listed'][m] }}">{{m|title}}</a>{% endfor %}</div>
<div class="row"><span class="label">Not listed:</span>{% for m in markets %}<a class="fbtn {{m}} {% if m in not_listed %}active{% endif %}" href="{{ toggles['not'][m] }}">✕ {{m|title}}</a>{% endfor %}<a class="fbtn clear" href="/">Clear</a></div>
<div class="shown">{{ items|length }} items shown</div>
</div>
<div class="summary"><div class="pill"><strong>{{ found }}</strong><span>Found</span></div><div class="pill"><strong>{{ missing }}</strong><span>Missing</span></div><div class="pill"><strong>{{ unchecked }}</strong><span>To check</span></div></div>
<div class="list">
{% for item in items %}
<div class="card">
<div class="top">{% if item.cover_image %}<img class="thumb" src="{{ item.cover_image }}">{% else %}<div class="thumb"></div>{% endif %}<div><div class="sku">{{ item.sku }}</div><div class="title2">{{ item.title }}</div>{% if item.non_unique_sku %}<span class="flag">Non-unique SKU</span>{% endif %}</div></div>
<div class="markets">{% for m in markets %}<span class="market {{m}} {% if item.marketplaces[m] %}on{% endif %}">{{m|title}}{% if item.marketplaces[m]|length > 1 %} ×{{item.marketplaces[m]|length}}{% endif %}</span>{% endfor %}</div>
<form class="actions" method="post" action="/status"><input type="hidden" name="audit_id" value="{{item.audit_id}}"><input type="hidden" name="return_to" value="{{ current_query }}"><button name="status" value="found" class="found {% if audit.get(item.audit_id)=='found' %}active-status{% endif %}">✓ Found</button><button name="status" value="missing" class="missing {% if audit.get(item.audit_id)=='missing' %}active-status{% endif %}">Missing</button></form>
{% if not audit.get(item.audit_id) %}<div class="unchecked">Not checked yet</div>{% endif %}
</div>
{% endfor %}
</div>
<div class="complete-wrap"><form method="post" action="/complete"><button class="complete">Complete Audit</button></form></div>
{% else %}
<form class="add" method="post" action="/unlisted/add"><input name="sku" placeholder="Enter SKU" autocapitalize="characters" autocomplete="off"><button>Add</button></form>
<div class="unlisted">{% for sku in unlisted %}<div class="urow"><span>{{sku}}</span><form method="post" action="/unlisted/remove/{{sku}}"><button>×</button></form></div>{% endfor %}</div>
{% endif %}
</body></html>
"""


def _local_ip() -> str:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        sock.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _parse_set(value: str) -> set[str]:
    return {part for part in value.split(",") if part in MARKETS}


def _query_url(listed: set[str], not_listed: set[str]) -> str:
    bits: list[str] = []
    if listed:
        bits.append("listed=" + ",".join(sorted(listed)))
    if not_listed:
        bits.append("not=" + ",".join(sorted(not_listed)))
    return "/" + (("?" + "&".join(bits)) if bits else "")


def _safe_item(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    markets_raw = raw.get("marketplaces") if isinstance(raw.get("marketplaces"), dict) else {}
    markets: dict[str, list[Any]] = {}
    for market in MARKETS:
        value = markets_raw.get(market)
        markets[market] = value if isinstance(value, list) else ([] if not value else [value])
    sku = str(raw.get("sku") or "UNKNOWN")
    audit_id = str(raw.get("audit_id") or sku)
    return {
        "audit_id": audit_id,
        "sku": sku,
        "title": str(raw.get("title") or ""),
        "cover_image": str(raw.get("cover_image") or ""),
        "non_unique_sku": bool(raw.get("non_unique_sku")),
        "marketplaces": markets,
    }


def create_mobile_app(service: AuditService) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health() -> Response:
        return Response("Stock Take Beta mobile server OK", mimetype="text/plain")

    @app.errorhandler(Exception)
    def show_error(exc: Exception):
        details = traceback.format_exc()
        return Response(
            "<h1>Stock Take Beta mobile error</h1>"
            f"<p><b>{escape(type(exc).__name__)}:</b> {escape(str(exc))}</p>"
            f"<pre style='white-space:pre-wrap'>{escape(details)}</pre>",
            status=500,
            mimetype="text/html",
        )

    def view_state(page: str):
        state = service.store.load()
        raw_items = state.get("marketplace_items", [])
        if not isinstance(raw_items, list):
            raw_items = []
        all_items = [_safe_item(item) for item in raw_items]
        audit = state.get("audit", {}) if isinstance(state.get("audit"), dict) else {}

        listed = _parse_set(request.args.get("listed", "")) if page == "audit" else set()
        not_listed = _parse_set(request.args.get("not", "")) if page == "audit" else set()
        not_listed -= listed

        def matches(item: dict[str, Any]) -> bool:
            present = item["marketplaces"]
            return all(bool(present[m]) for m in listed) and all(not present[m] for m in not_listed)

        items = [item for item in all_items if matches(item)] if page == "audit" else all_items
        valid_ids = {item["audit_id"] for item in all_items}
        found = sum(1 for key, value in audit.items() if key in valid_ids and value == "found")
        missing = sum(1 for key, value in audit.items() if key in valid_ids and value == "missing")
        unchecked = max(0, len(all_items) - found - missing)

        toggles = {"listed": {}, "not": {}}
        for market in MARKETS:
            nl = set(listed)
            nn = set(not_listed)
            if market in nl:
                nl.remove(market)
            else:
                nn.discard(market)
                nl.add(market)
            toggles["listed"][market] = _query_url(nl, nn)

            nl = set(listed)
            nn = set(not_listed)
            if market in nn:
                nn.remove(market)
            else:
                nl.discard(market)
                nn.add(market)
            toggles["not"][market] = _query_url(nl, nn)

        refreshed = state.get("last_refreshed_at") or "Not refreshed yet"
        current_query = ("?" + request.query_string.decode("utf-8")) if request.query_string else ""
        return render_template_string(
            TEMPLATE,
            page=page,
            items=items,
            audit=audit,
            found=found,
            missing=missing,
            unchecked=unchecked,
            unlisted=state.get("unlisted_physical_stock", []) if isinstance(state.get("unlisted_physical_stock"), list) else [],
            meta=f"{len(all_items)} audit rows · last refresh {refreshed}",
            markets=MARKETS,
            listed=listed,
            not_listed=not_listed,
            toggles=toggles,
            audit_url=_query_url(listed, not_listed),
            current_query=current_query,
        )

    @app.get("/")
    def audit_page():
        return view_state("audit")

    @app.post("/status")
    def set_status():
        audit_id = request.form.get("audit_id", "").strip()
        if audit_id:
            service.set_physical_status(audit_id, request.form.get("status", "unchecked"))
        return redirect("/" + request.form.get("return_to", ""))

    @app.get("/unlisted")
    def unlisted_page():
        return view_state("unlisted")

    @app.post("/unlisted/add")
    def add_unlisted():
        sku = request.form.get("sku", "").strip()
        if sku:
            service.add_unlisted_sku(sku)
        return redirect(url_for("unlisted_page"))

    @app.post("/unlisted/remove/<sku>")
    def remove_unlisted(sku: str):
        service.remove_unlisted_sku(sku)
        return redirect(url_for("unlisted_page"))

    @app.post("/complete")
    def complete():
        service.complete_audit()
        return redirect(url_for("audit_page"))

    return app


def start_mobile_server(service: AuditService) -> str:
    app = create_mobile_app(service)
    thread = threading.Thread(
        target=lambda: app.run(host=MOBILE_HOST, port=MOBILE_PORT, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    return f"http://{_local_ip()}:{MOBILE_PORT}"
