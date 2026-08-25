from __future__ import annotations

import socket
import threading
from html import escape

from flask import Flask, redirect, render_template_string, request, url_for

from .config import MOBILE_HOST, MOBILE_PORT
from .services.audit_service import AuditService


MOBILE_TEMPLATE = r"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Massimo's Rail Stock Take</title>
<style>
:root{--cream:#F3EBDD;--light:#FBF7EF;--green:#173C2B;--mid:#285440;--soft:#DCE6DE;--muted:#6E776F;--border:#CFC6B7;}
*{box-sizing:border-box} body{margin:0;background:var(--cream);color:var(--green);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--green);color:white;padding:14px 16px 12px;box-shadow:0 2px 8px #0002}
.brand{font-size:12px;letter-spacing:1.7px;opacity:.75}.title{font-size:22px;font-weight:800;margin-top:2px}.meta{font-size:12px;opacity:.75;margin-top:4px}
.tabs{display:flex;gap:8px;padding:12px 12px 4px}.tabs a{flex:1;text-align:center;padding:11px;border-radius:10px;text-decoration:none;font-weight:700;color:var(--green);background:var(--light);border:1px solid var(--border)}
.filters{display:flex;gap:7px;overflow-x:auto;padding:8px 12px 2px}.filters a{white-space:nowrap;text-decoration:none;border:1px solid var(--border);border-radius:999px;padding:8px 11px;font-size:12px;font-weight:800;color:var(--green);background:var(--light)}.filters a.active{background:var(--green);color:white;border-color:var(--green)}
.summary{padding:8px 12px 2px;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.pill{background:var(--light);border:1px solid var(--border);border-radius:10px;padding:10px;text-align:center}.pill strong{display:block;font-size:20px}.pill span{font-size:11px;color:var(--muted)}
.list{padding:10px 12px 90px}.card{background:var(--light);border:1px solid var(--border);border-radius:14px;padding:12px;margin-bottom:10px}.top{display:flex;gap:10px;align-items:center}.thumb{width:56px;height:56px;border-radius:8px;object-fit:cover;background:var(--soft)}.sku{font-size:21px;font-weight:850}.title2{font-size:12px;color:var(--muted);line-height:1.25;margin-top:2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.flag{display:inline-block;margin-top:5px;font-size:10px;font-weight:800;border-radius:999px;padding:4px 7px;background:#f3d8ce;color:#7a2f1c}.markets{margin:10px 0 9px;display:flex;gap:6px;flex-wrap:wrap}.market{font-size:11px;font-weight:750;border-radius:999px;padding:5px 8px;background:#eee;color:#777}.market.on{background:var(--soft);color:var(--green)}.market.dup{background:#f3d8ce;color:#7a2f1c}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.actions button{border:0;border-radius:10px;padding:12px;font-size:15px;font-weight:800}.found{background:var(--green);color:#fff}.missing{background:#ead7d1;color:#6e2c20}.active{outline:3px solid #91a99a}.unchecked{font-size:11px;color:var(--muted);margin-top:8px;text-align:center}
.add{display:flex;gap:8px;margin:10px 12px}.add input{flex:1;border:1px solid var(--border);border-radius:10px;padding:13px;font-size:16px;background:white}.add button,.complete{border:0;border-radius:10px;background:var(--green);color:white;padding:12px 14px;font-weight:800}.unlisted{padding:4px 12px 90px}.urow{display:flex;align-items:center;justify-content:space-between;background:var(--light);border:1px solid var(--border);padding:12px;margin-bottom:8px;border-radius:10px;font-weight:800}.urow button{border:0;background:transparent;font-size:20px;color:#8c4b3b}.complete-wrap{position:fixed;left:0;right:0;bottom:0;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:linear-gradient(transparent,var(--cream) 25%)}.complete{width:100%;font-size:16px}
</style>
</head>
<body>
<header><div class="brand">MASSIMO'S RAIL</div><div class="title">Shorts Stock Audit</div><div class="meta">{{ meta }}</div></header>
<div class="tabs"><a href="/">Audit</a><a href="/unlisted">Unlisted Stock</a></div>
{% if page == 'audit' %}
<div class="filters">
<a href="/?market=all" class="{% if market_filter=='all' %}active{% endif %}">All ({{ total_rows }})</a>
{% for m in ['vinted','ebay','etsy'] %}<a href="/?market={{ m }}" class="{% if market_filter==m %}active{% endif %}">{{ m|title }} ({{ market_counts[m] }})</a>{% endfor %}
</div>
<div class="summary"><div class="pill"><strong>{{ found }}</strong><span>Found</span></div><div class="pill"><strong>{{ missing }}</strong><span>Missing</span></div><div class="pill"><strong>{{ unchecked }}</strong><span>To check</span></div></div>
<div class="list">
{% for item in items %}
{% set aid = item.audit_id or item.sku %}
<div class="card">
<div class="top">{% if item.cover_image %}<img class="thumb" src="{{ item.cover_image }}">{% else %}<div class="thumb"></div>{% endif %}<div><div class="sku">{{ item.sku }}</div><div class="title2">{{ item.title }}</div>{% if item.non_unique_sku %}<span class="flag">Non-unique SKU</span>{% endif %}</div></div>
<div class="markets">
{% for m in ['vinted','ebay','etsy'] %}<span class="market {% if item.marketplaces.get(m) %}on{% endif %} {% if item.marketplaces.get(m)|length > 1 %}dup{% endif %}">{{ m|title }}{% if item.marketplaces.get(m)|length > 1 %} ×{{ item.marketplaces.get(m)|length }}{% endif %}</span>{% endfor %}
</div>
<form class="actions" method="post" action="/status"><input type="hidden" name="audit_id" value="{{ aid }}"><input type="hidden" name="market" value="{{ market_filter }}"><button name="status" value="found" class="found {% if audit.get(aid)=='found' %}active{% endif %}">✓ Found</button><button name="status" value="missing" class="missing {% if audit.get(aid)=='missing' %}active{% endif %}">Missing</button></form>
{% if not audit.get(aid) %}<div class="unchecked">Not checked yet</div>{% endif %}
</div>
{% endfor %}
</div><div class="complete-wrap"><form method="post" action="/complete"><input type="hidden" name="market" value="{{ market_filter }}"><button class="complete">Complete Audit</button></form></div>
{% else %}
<form class="add" method="post" action="/unlisted/add"><input name="sku" placeholder="Enter SKU" autocapitalize="characters" autocomplete="off"><button>Add</button></form>
<div class="unlisted">{% for sku in unlisted %}<div class="urow"><span>{{ sku }}</span><form method="post" action="/unlisted/remove/{{ sku }}"><button>×</button></form></div>{% endfor %}</div>
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


def create_mobile_app(service: AuditService) -> Flask:
    app = Flask(__name__)

    def view_state(page: str):
        state = service.store.load()
        all_items = state.get("marketplace_items", [])
        audit = state.get("audit", {})
        valid_ids = {item.get("audit_id") or item.get("sku") for item in all_items}
        found = sum(1 for key, value in audit.items() if key in valid_ids and value == "found")
        missing = sum(1 for key, value in audit.items() if key in valid_ids and value == "missing")
        unchecked = max(0, len(all_items) - found - missing)
        refreshed = state.get("last_refreshed_at") or "Not refreshed yet"
        market_filter = request.args.get("market", "all").lower()
        if market_filter not in {"all", "vinted", "ebay", "etsy"}:
            market_filter = "all"
        market_counts = {
            market: sum(1 for item in all_items if item.get("marketplaces", {}).get(market))
            for market in ("vinted", "ebay", "etsy")
        }
        items = all_items if market_filter == "all" else [
            item for item in all_items if item.get("marketplaces", {}).get(market_filter)
        ]
        return render_template_string(
            MOBILE_TEMPLATE,
            page=page,
            items=items,
            audit=audit,
            found=found,
            missing=missing,
            unchecked=unchecked,
            unlisted=state.get("unlisted_physical_stock", []),
            market_filter=market_filter,
            market_counts=market_counts,
            total_rows=len(all_items),
            meta=f"Showing {len(items)} of {len(all_items)} audit rows · last refresh {escape(str(refreshed))}",
        )

    @app.get("/")
    def audit():
        return view_state("audit")

    @app.post("/status")
    def set_status():
        audit_id = request.form.get("audit_id", "").strip()
        market = request.form.get("market", "all").strip().lower()
        if audit_id:
            service.set_physical_status(audit_id, request.form.get("status", "unchecked"))
        return redirect(url_for("audit", market=market))

    @app.get("/unlisted")
    def unlisted():
        return view_state("unlisted")

    @app.post("/unlisted/add")
    def add_unlisted():
        sku = request.form.get("sku", "").strip()
        if sku:
            service.add_unlisted_sku(sku)
        return redirect(url_for("unlisted"))

    @app.post("/unlisted/remove/<sku>")
    def remove_unlisted(sku: str):
        service.remove_unlisted_sku(sku)
        return redirect(url_for("unlisted"))

    @app.post("/complete")
    def complete():
        market = request.form.get("market", "all").strip().lower()
        service.complete_audit()
        return redirect(url_for("audit", market=market))

    return app


def start_mobile_server(service: AuditService) -> str:
    app = create_mobile_app(service)
    thread = threading.Thread(
        target=lambda: app.run(host=MOBILE_HOST, port=MOBILE_PORT, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    return f"http://{_local_ip()}:{MOBILE_PORT}"
