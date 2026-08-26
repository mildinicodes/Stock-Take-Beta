from __future__ import annotations

import re
import socket
import threading
from urllib.parse import quote

from flask import Flask, redirect, render_template_string, request, url_for

from .config import MOBILE_HOST, MOBILE_PORT
from .services.audit_service import AuditService


MOBILE_TEMPLATE = r"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Massimo's Rail Stock Take</title>
<style>
:root{--cream:#F3EBDD;--light:#FBF7EF;--green:#173C2B;--mid:#285440;--soft:#DCE6DE;--muted:#6E776F;--border:#CFC6B7;--vinted:#09B1BA;--ebay:#3665F3;--etsy:#F1641E;--danger:#8B3B2D}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--cream);color:var(--green);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:20;background:var(--green);color:white;padding:11px 14px 10px;box-shadow:0 2px 8px #0002}.brand{font-size:10px;letter-spacing:1.6px;opacity:.72}.title{font-size:20px;font-weight:800;margin-top:1px}.meta{font-size:11px;opacity:.72;margin-top:3px}
.tabs{display:flex;gap:7px;padding:9px 10px 3px}.tabs a{flex:1;text-align:center;padding:9px;border-radius:9px;text-decoration:none;font-size:13px;font-weight:750;color:var(--green);background:var(--light);border:1px solid var(--border)}
.quick{margin:7px 10px 4px;padding:9px;background:var(--light);border:1px solid var(--border);border-radius:11px}.quick-row{display:flex;gap:7px}.quick input{min-width:0;flex:1;border:1px solid var(--border);border-radius:9px;padding:11px;font-size:16px;text-transform:uppercase;background:white}.quick button,.jump{border:0;border-radius:9px;background:var(--green);color:white;padding:10px 12px;font-weight:800;font-size:13px}.quick-foot{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:7px}.quick-note{font-size:11px;color:var(--muted)}.jump{text-decoration:none;background:var(--mid);white-space:nowrap}.jump.disabled{opacity:.45;pointer-events:none}
.filters{margin:7px 10px 2px;padding:9px;background:var(--light);border:1px solid var(--border);border-radius:11px}.filter-row{display:flex;gap:5px;align-items:center;margin:4px 0;flex-wrap:wrap}.filter-label{width:76px;font-size:11px;font-weight:800}.fbtn{padding:7px 8px;border-radius:8px;text-decoration:none;font-size:11px;font-weight:800;background:white;border:1px solid currentColor}.vinted{color:var(--vinted)}.ebay{color:var(--ebay)}.etsy{color:var(--etsy)}.active.vinted{background:var(--vinted);color:white}.active.ebay{background:var(--ebay);color:white}.active.etsy{background:var(--etsy);color:white}.clear{margin-left:auto;color:var(--green);border-color:var(--border)}.shown{font-size:11px;color:var(--muted);margin-top:6px;font-weight:700}
.summary{padding:7px 10px 1px;display:grid;grid-template-columns:repeat(3,1fr);gap:6px}.pill{background:var(--light);border:1px solid var(--border);border-radius:9px;padding:8px;text-align:center}.pill strong{display:block;font-size:18px}.pill span{font-size:10px;color:var(--muted)}
.list{padding:8px 10px 86px}.card{scroll-margin-top:84px;background:var(--light);border:1px solid var(--border);border-radius:12px;padding:10px;margin-bottom:8px}.card.last{box-shadow:0 0 0 3px #91A99A}.top{display:flex;gap:9px;align-items:center}.thumb{width:50px;height:50px;border-radius:7px;object-fit:cover;background:var(--soft);flex:0 0 auto}.sku{font-size:20px;font-weight:850}.title2{font-size:11px;color:var(--muted);line-height:1.2;margin-top:1px;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}.flag{display:inline-block;margin-top:4px;font-size:9px;font-weight:800;border-radius:999px;padding:3px 6px;background:#f3d8ce;color:#7a2f1c}.markets{margin:8px 0 7px;display:flex;gap:5px;flex-wrap:wrap}.market{font-size:10px;font-weight:750;border-radius:999px;padding:4px 7px;background:#eee;color:#777}.market.vinted.on{background:var(--vinted);color:white}.market.ebay.on{background:var(--ebay);color:white}.market.etsy.on{background:var(--etsy);color:white}.market.dup{outline:2px solid #7a2f1c}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:7px}.actions button{border:0;border-radius:9px;padding:11px;font-size:14px;font-weight:800}.found{background:var(--green);color:#fff}.missing{background:#ead7d1;color:#6e2c20}.active-status{outline:3px solid #91a99a}.unchecked{font-size:10px;color:var(--muted);margin-top:6px;text-align:center}.last-tag{font-size:9px;font-weight:800;color:var(--green);background:var(--soft);padding:3px 6px;border-radius:99px;margin-left:5px}
.add{display:flex;gap:8px;margin:10px}.add input{flex:1;border:1px solid var(--border);border-radius:10px;padding:13px;font-size:16px;background:white}.add button,.complete{border:0;border-radius:10px;background:var(--green);color:white;padding:12px 14px;font-weight:800}.unlisted{padding:4px 10px 90px}.urow{display:flex;align-items:center;justify-content:space-between;background:var(--light);border:1px solid var(--border);padding:12px;margin-bottom:7px;border-radius:10px;font-weight:800}.urow button{border:0;background:transparent;font-size:20px;color:var(--danger)}.complete-wrap{position:fixed;left:0;right:0;bottom:0;padding:9px 10px calc(9px + env(safe-area-inset-bottom));background:linear-gradient(transparent,var(--cream) 25%);z-index:15}.complete{width:100%;font-size:15px}
.toast{margin:6px 10px 0;padding:8px 10px;background:var(--soft);border-radius:9px;font-size:12px;font-weight:750}
</style>
</head>
<body>
<header><div class="brand">MASSIMO'S RAIL</div><div class="title">Shorts Stock Audit</div><div class="meta">{{ meta }}</div></header>
<div class="tabs"><a href="{{ audit_url }}">Audit</a><a href="/unlisted">Unlisted Stock ({{ unlisted|length }})</a></div>
{% if page == 'audit' %}
<form class="quick" method="post" action="/quick-unlisted">
<div class="quick-row"><input name="sku" placeholder="Add unlisted SKU e.g. JOR501" autocapitalize="characters" autocomplete="off" required><input type="hidden" name="return_to" value="{{ current_path }}"><button>Add SKU</button></div>
<div class="quick-foot"><span class="quick-note">Adds physical stock without leaving the audit.</span><a class="jump {% if not last_anchor %}disabled{% endif %}" href="{{ last_url }}">↩ Last checked{% if last_sku %}: {{ last_sku }}{% endif %}</a></div>
</form>
{% if added_sku %}<div class="toast">Added {{ added_sku }} to Unlisted Physical Stock.</div>{% endif %}
<div class="filters">
<div class="filter-row"><span class="filter-label">Listed on:</span>{% for m in markets %}<a class="fbtn {{m}} {% if m in listed %}active{% endif %}" href="{{ toggle_urls['listed'][m] }}">{{m|title}}</a>{% endfor %}</div>
<div class="filter-row"><span class="filter-label">Not listed:</span>{% for m in markets %}<a class="fbtn {{m}} {% if m in not_listed %}active{% endif %}" href="{{ toggle_urls['not'][m] }}">✕ {{m|title}}</a>{% endfor %}<a class="fbtn clear" href="/">Clear</a></div>
<div class="shown">{{ items|length }} items shown</div>
</div>
<div class="summary"><div class="pill"><strong>{{ found }}</strong><span>Found</span></div><div class="pill"><strong>{{ missing }}</strong><span>Missing</span></div><div class="pill"><strong>{{ unchecked }}</strong><span>To check</span></div></div>
<div class="list">
{% for item in items %}
{% set aid = item.audit_id or item.sku %}
<div class="card {% if aid == last_checked %}last{% endif %}" id="{{ item.anchor_id }}">
<div class="top">{% if item.cover_image %}<img class="thumb" src="{{ item.cover_image }}">{% else %}<div class="thumb"></div>{% endif %}<div><div class="sku">{{ item.sku }}{% if aid == last_checked %}<span class="last-tag">LAST</span>{% endif %}</div><div class="title2">{{ item.title }}</div>{% if item.non_unique_sku %}<span class="flag">Non-unique SKU</span>{% endif %}</div></div>
<div class="markets">{% for m in markets %}{% set rows = item.marketplaces.get(m) or [] %}<span class="market {{m}} {% if rows %}on{% endif %} {% if rows|length > 1 %}dup{% endif %}">{{m|title}}{% if rows|length > 1 %} ×{{rows|length}}{% endif %}</span>{% endfor %}</div>
<form class="actions" method="post" action="/status"><input type="hidden" name="audit_id" value="{{aid}}"><input type="hidden" name="return_to" value="{{ current_path }}"><input type="hidden" name="anchor" value="{{ item.anchor_id }}"><button name="status" value="found" class="found {% if audit.get(aid)=='found' %}active-status{% endif %}">✓ Found</button><button name="status" value="missing" class="missing {% if audit.get(aid)=='missing' %}active-status{% endif %}">Missing</button></form>
{% if not audit.get(aid) %}<div class="unchecked">Not checked yet</div>{% endif %}
</div>
{% endfor %}
</div><div class="complete-wrap"><form method="post" action="/complete"><button class="complete">Complete Audit</button></form></div>
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
    allowed = {"vinted", "ebay", "etsy"}
    return {part for part in value.split(",") if part in allowed}


def _query_url(listed: set[str], not_listed: set[str]) -> str:
    parts = []
    if listed:
        parts.append("listed=" + ",".join(sorted(listed)))
    if not_listed:
        parts.append("not=" + ",".join(sorted(not_listed)))
    return "/" + ("?" + "&".join(parts) if parts else "")


def _anchor(audit_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", audit_id).strip("-")
    return "item-" + (safe or "row")


def create_mobile_app(service: AuditService) -> Flask:
    app = Flask(__name__)
    markets = ("vinted", "ebay", "etsy")

    def view_state(page: str):
        state = service.store.load()
        raw_items = state.get("marketplace_items", [])
        all_items = []
        for raw in raw_items:
            item = dict(raw)
            aid = item.get("audit_id") or item.get("sku", "")
            item["anchor_id"] = _anchor(aid)
            all_items.append(item)

        audit = state.get("audit", {})
        listed = _parse_set(request.args.get("listed", "")) if page == "audit" else set()
        not_listed = _parse_set(request.args.get("not", "")) if page == "audit" else set()
        not_listed -= listed

        def matches(item: dict) -> bool:
            present = item.get("marketplaces", {})
            return all(present.get(m) for m in listed) and all(not present.get(m) for m in not_listed)

        items = [item for item in all_items if matches(item)] if page == "audit" else all_items
        valid_ids = {item.get("audit_id") or item.get("sku") for item in all_items}
        found = sum(1 for key, value in audit.items() if key in valid_ids and value == "found")
        missing = sum(1 for key, value in audit.items() if key in valid_ids and value == "missing")
        unchecked = max(0, len(all_items) - found - missing)
        refreshed = state.get("last_refreshed_at") or "Not refreshed yet"

        toggle_urls = {"listed": {}, "not": {}}
        for market in markets:
            a = set(listed); b = set(not_listed)
            if market in a: a.remove(market)
            else: b.discard(market); a.add(market)
            toggle_urls["listed"][market] = _query_url(a, b)
            a = set(listed); b = set(not_listed)
            if market in b: b.remove(market)
            else: a.discard(market); b.add(market)
            toggle_urls["not"][market] = _query_url(a, b)

        current_path = request.full_path.rstrip("?")
        last_checked = state.get("last_checked_audit_id")
        last_item = next((i for i in all_items if (i.get("audit_id") or i.get("sku")) == last_checked), None)
        last_anchor = last_item.get("anchor_id") if last_item else None
        last_sku = last_item.get("sku") if last_item else None
        base_audit_url = _query_url(listed, not_listed)
        last_url = base_audit_url + ("#" + last_anchor if last_anchor else "")

        return render_template_string(
            MOBILE_TEMPLATE,
            page=page,
            items=items,
            audit=audit,
            found=found,
            missing=missing,
            unchecked=unchecked,
            unlisted=state.get("unlisted_physical_stock", []),
            meta=f"{len(all_items)} audit rows · last refresh {refreshed}",
            markets=markets,
            listed=listed,
            not_listed=not_listed,
            toggle_urls=toggle_urls,
            audit_url=base_audit_url,
            current_path=current_path,
            last_checked=last_checked,
            last_anchor=last_anchor,
            last_sku=last_sku,
            last_url=last_url,
            added_sku=request.args.get("added", ""),
        )

    @app.get("/health")
    def health():
        return "Stock Take Beta mobile server OK", 200, {"Content-Type": "text/plain; charset=utf-8"}

    @app.get("/")
    def audit():
        return view_state("audit")

    @app.post("/status")
    def set_status():
        audit_id = request.form.get("audit_id", "").strip()
        if audit_id:
            service.set_physical_status(audit_id, request.form.get("status", "unchecked"))
        return_to = request.form.get("return_to", "/") or "/"
        anchor = request.form.get("anchor", "")
        return redirect(return_to + ("#" + anchor if anchor else ""))

    @app.post("/quick-unlisted")
    def quick_unlisted():
        sku = request.form.get("sku", "").strip()
        if sku:
            service.add_unlisted_sku(sku)
        return_to = request.form.get("return_to", "/") or "/"
        separator = "&" if "?" in return_to else "?"
        return redirect(return_to + separator + "added=" + quote(sku.upper()))

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
        service.complete_audit()
        return redirect(url_for("audit"))

    return app


def start_mobile_server(service: AuditService) -> str:
    app = create_mobile_app(service)
    thread = threading.Thread(target=lambda: app.run(host=MOBILE_HOST, port=MOBILE_PORT, debug=False, use_reloader=False), daemon=True)
    thread.start()
    return f"http://{_local_ip()}:{MOBILE_PORT}"
