from __future__ import annotations

import re
import socket
import threading
import traceback
from html import escape
from typing import Any

from flask import Flask, Response, jsonify, redirect, render_template_string, request, url_for

from .config import MOBILE_HOST, MOBILE_PORT
from .services.audit_service import AuditService

MARKETS = ("vinted", "ebay", "etsy")

TEMPLATE = r"""
<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>Massimo's Rail Stock Take</title>
<style>
:root{--cream:#F3EBDD;--light:#FBF7EF;--green:#173C2B;--mid:#285440;--soft:#DCE6DE;--muted:#6E776F;--border:#CFC6B7;--vinted:#09B1BA;--ebay:#3665F3;--etsy:#F1641E;--danger:#8B3B2D}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--cream);color:var(--green);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
header{position:sticky;top:0;z-index:20;background:var(--green);color:white;padding:14px 16px 12px}.brand{font-size:11px;letter-spacing:1.6px;opacity:.75}.title{font-size:22px;font-weight:800}.meta{font-size:11px;opacity:.75;margin-top:3px}
.tabs{display:flex;gap:8px;padding:10px 12px 4px}.tabs a{flex:1;text-align:center;padding:10px;border-radius:10px;text-decoration:none;font-weight:800;color:var(--green);background:var(--light);border:1px solid var(--border)}
.resume{display:flex;justify-content:flex-end;padding:5px 12px 0}.jump{border:0;border-radius:9px;background:var(--mid);color:white;padding:9px 11px;font-weight:800;font-size:12px;text-decoration:none}.jump.disabled{opacity:.45;pointer-events:none}
.filters{margin:8px 12px;padding:10px;background:var(--light);border:1px solid var(--border);border-radius:12px}.row{display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:5px 0}.label{width:86px;font-size:12px;font-weight:800}.fbtn{padding:8px 10px;border-radius:9px;text-decoration:none;font-size:12px;font-weight:800;background:white;border:1px solid currentColor}.vinted{color:var(--vinted)}.ebay{color:var(--ebay)}.etsy{color:var(--etsy)}.active.vinted{background:var(--vinted);color:white}.active.ebay{background:var(--ebay);color:white}.active.etsy{background:var(--etsy);color:white}.clear{color:var(--green);border-color:var(--border)}.shown{font-size:12px;color:var(--muted);font-weight:700;margin-top:7px}
.summary{padding:0 12px 2px;display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.pill{background:var(--light);border:1px solid var(--border);border-radius:10px;padding:9px;text-align:center}.pill strong{display:block;font-size:19px}.pill span{font-size:10px;color:var(--muted)}
.list{padding:8px 12px 98px}.card{scroll-margin-top:90px;background:var(--light);border:1px solid var(--border);border-radius:14px;padding:12px;margin-bottom:9px}.card.last{box-shadow:0 0 0 3px #91A99A}.top{display:flex;gap:10px;align-items:center}.thumb{width:54px;height:54px;border-radius:8px;object-fit:cover;background:var(--soft);flex:0 0 auto}.sku{font-size:21px;font-weight:850}.title2{font-size:12px;color:var(--muted);line-height:1.2;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.flag{display:inline-block;margin-top:4px;font-size:10px;font-weight:800;padding:4px 7px;border-radius:999px;background:#f3d8ce;color:#7a2f1c}.last-tag{font-size:9px;font-weight:800;color:var(--green);background:var(--soft);padding:3px 6px;border-radius:99px;margin-left:5px}
.markets{display:flex;gap:6px;flex-wrap:wrap;margin:9px 0}.market{font-size:11px;font-weight:800;border-radius:999px;padding:5px 8px;background:#eee;color:#777}.market.vinted.on{background:var(--vinted);color:white}.market.ebay.on{background:var(--ebay);color:white}.market.etsy.on{background:var(--etsy);color:white}
.actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}.actions button{border:0;border-radius:10px;padding:12px;font-size:15px;font-weight:800}.found{background:var(--green);color:white}.missing{background:#ead7d1;color:#6e2c20}.active-status{outline:3px solid #91a99a}.unchecked{text-align:center;font-size:11px;color:var(--muted);margin-top:7px}
.add{display:flex;gap:8px;margin:10px 12px}.add input{flex:1;border:1px solid var(--border);border-radius:10px;padding:13px;font-size:16px}.add button{border:0;border-radius:10px;background:var(--green);color:white;padding:12px 14px;font-weight:800}.unlisted{padding:2px 12px 90px}.urow{display:flex;justify-content:space-between;align-items:center;background:var(--light);border:1px solid var(--border);padding:12px;margin-bottom:8px;border-radius:10px;font-weight:800}.urow button{border:0;background:transparent;font-size:20px;color:var(--danger)}
.bottom-wrap{position:fixed;left:0;right:0;bottom:0;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:linear-gradient(transparent,var(--cream) 25%);z-index:30}.bottom-btn{width:100%;border:0;border-radius:10px;background:var(--green);color:white;padding:14px;font-size:16px;font-weight:850;box-shadow:0 2px 8px #0002}
.drawer-backdrop{display:none;position:fixed;inset:0;background:#0005;z-index:40}.drawer{display:none;position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:41;background:var(--light);border:1px solid var(--border);border-radius:14px;padding:13px;box-shadow:0 10px 35px #0005}.drawer.open,.drawer-backdrop.open{display:block}.drawer-title{font-size:17px;font-weight:850;margin-bottom:9px}.drawer-row{display:flex;gap:7px}.drawer input{min-width:0;flex:1;border:1px solid var(--border);border-radius:9px;padding:12px;font-size:16px;text-transform:uppercase;background:white}.drawer button{border:0;border-radius:9px;background:var(--green);color:white;padding:11px 13px;font-weight:800}.drawer .cancel{background:var(--soft);color:var(--green)}.drawer-note{font-size:11px;color:var(--muted);margin-top:8px}.drawer-success{display:none;margin-top:8px;padding:8px 9px;border-radius:8px;background:var(--soft);font-size:12px;font-weight:750}.drawer-success.show{display:block}
</style>
</head>
<body>
<header><div class="brand">MASSIMO'S RAIL</div><div class="title">Shorts Stock Audit</div><div class="meta">{{ meta }}</div></header>
<div class="tabs"><a href="{{ audit_url }}">Audit</a><a href="/unlisted">Unlisted Stock ({{ unlisted|length }})</a></div>
{% if page == 'audit' %}
<div class="resume"><a class="jump {% if not last_anchor %}disabled{% endif %}" href="{{ last_url }}">↩ Last checked{% if last_sku %}: {{ last_sku }}{% endif %}</a></div>
<div class="filters">
<div class="row"><span class="label">Listed on:</span>{% for m in markets %}<a class="fbtn {{m}} {% if m in listed %}active{% endif %}" href="{{ toggles['listed'][m] }}">{{m|title}}</a>{% endfor %}</div>
<div class="row"><span class="label">Not listed:</span>{% for m in markets %}<a class="fbtn {{m}} {% if m in not_listed %}active{% endif %}" href="{{ toggles['not'][m] }}">✕ {{m|title}}</a>{% endfor %}<a class="fbtn clear" href="/">Clear</a></div>
<div class="shown">{{ items|length }} items shown</div>
</div>
<div class="summary"><div class="pill"><strong>{{ found }}</strong><span>Found</span></div><div class="pill"><strong>{{ missing }}</strong><span>Missing</span></div><div class="pill"><strong>{{ unchecked }}</strong><span>To check</span></div></div>
<div class="list">
{% for item in items %}
<div class="card {% if item.audit_id == last_checked %}last{% endif %}" id="{{ item.anchor_id }}">
<div class="top">{% if item.cover_image %}<img class="thumb" src="{{ item.cover_image }}">{% else %}<div class="thumb"></div>{% endif %}<div><div class="sku">{{ item.sku }}{% if item.audit_id == last_checked %}<span class="last-tag">LAST</span>{% endif %}</div><div class="title2">{{ item.title }}</div>{% if item.non_unique_sku %}<span class="flag">Non-unique SKU</span>{% endif %}</div></div>
<div class="markets">{% for m in markets %}<span class="market {{m}} {% if item.marketplaces[m] %}on{% endif %}">{{m|title}}{% if item.marketplaces[m]|length > 1 %} ×{{item.marketplaces[m]|length}}{% endif %}</span>{% endfor %}</div>
<form class="actions" method="post" action="/status"><input type="hidden" name="audit_id" value="{{item.audit_id}}"><input type="hidden" name="return_to" value="{{ current_path }}"><input type="hidden" name="anchor" value="{{ item.anchor_id }}"><button name="status" value="found" class="found {% if audit.get(item.audit_id)=='found' %}active-status{% endif %}">✓ Found</button><button name="status" value="missing" class="missing {% if audit.get(item.audit_id)=='missing' %}active-status{% endif %}">Missing</button></form>
{% if not audit.get(item.audit_id) %}<div class="unchecked">Not checked yet</div>{% endif %}
</div>
{% endfor %}
</div>
<div class="bottom-wrap"><button class="bottom-btn" type="button" onclick="openUnlistedDrawer()">+ Unlisted SKU</button></div>
<div class="drawer-backdrop" id="unlistedBackdrop" onclick="closeUnlistedDrawer()"></div>
<div class="drawer" id="unlistedDrawer">
<div class="drawer-title">Add unlisted physical SKU</div>
<form id="unlistedQuickForm" onsubmit="submitUnlisted(event)">
<div class="drawer-row"><input id="unlistedSkuInput" name="sku" placeholder="e.g. JOR501" autocapitalize="characters" autocomplete="off" required><button type="submit">Add</button><button type="button" class="cancel" onclick="closeUnlistedDrawer()">Cancel</button></div>
</form>
<div class="drawer-note">Adds the SKU without moving you away from your current place.</div>
<div class="drawer-success" id="unlistedSuccess"></div>
</div>
<script>
function openUnlistedDrawer(){document.getElementById('unlistedBackdrop').classList.add('open');document.getElementById('unlistedDrawer').classList.add('open');setTimeout(function(){document.getElementById('unlistedSkuInput').focus();},80)}
function closeUnlistedDrawer(){document.getElementById('unlistedBackdrop').classList.remove('open');document.getElementById('unlistedDrawer').classList.remove('open');document.getElementById('unlistedSuccess').classList.remove('show')}
async function submitUnlisted(event){event.preventDefault();var input=document.getElementById('unlistedSkuInput');var sku=input.value.trim().toUpperCase();if(!sku)return;var data=new FormData();data.append('sku',sku);try{var response=await fetch('/quick-unlisted',{method:'POST',body:data});if(!response.ok)throw new Error('Save failed');input.value='';var success=document.getElementById('unlistedSuccess');success.textContent='Added '+sku+' to Unlisted Physical Stock.';success.classList.add('show');setTimeout(closeUnlistedDrawer,700)}catch(error){var success=document.getElementById('unlistedSuccess');success.textContent='Could not save SKU. Try again.';success.classList.add('show')}}
</script>
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


def _anchor(audit_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", audit_id).strip("-")
    return "item-" + (safe or "row")


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
        "anchor_id": _anchor(audit_id),
        "sku": sku,
        "title": str(raw.get("title") or ""),
        "cover_image": str(raw.get("cover_image") or ""),
        "non_unique_sku": bool(raw.get("non_unique_sku")),
        "marketplaces": markets,
    }


def create_mobile_app(service: AuditService) -> Flask:
    app = Flask(__name__)

    @app.after_request
    def no_cache(response: Response) -> Response:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.get("/health")
    def health() -> Response:
        return Response("Stock Take Beta mobile server v2 - unlisted quick add", mimetype="text/plain")

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
            nl = set(listed); nn = set(not_listed)
            if market in nl: nl.remove(market)
            else: nn.discard(market); nl.add(market)
            toggles["listed"][market] = _query_url(nl, nn)
            nl = set(listed); nn = set(not_listed)
            if market in nn: nn.remove(market)
            else: nl.discard(market); nn.add(market)
            toggles["not"][market] = _query_url(nl, nn)

        refreshed = state.get("last_refreshed_at") or "Not refreshed yet"
        current_path = request.full_path.rstrip("?")
        last_checked = state.get("last_checked_audit_id")
        last_item = next((item for item in all_items if item["audit_id"] == last_checked), None)
        last_anchor = last_item["anchor_id"] if last_item else None
        last_sku = last_item["sku"] if last_item else None
        base_audit_url = _query_url(listed, not_listed)
        last_url = base_audit_url + (("#" + last_anchor) if last_anchor else "")
        unlisted = state.get("unlisted_physical_stock", []) if isinstance(state.get("unlisted_physical_stock"), list) else []

        return render_template_string(
            TEMPLATE,
            page=page,
            items=items,
            audit=audit,
            found=found,
            missing=missing,
            unchecked=unchecked,
            unlisted=unlisted,
            meta=f"{len(all_items)} audit rows · last refresh {refreshed}",
            markets=MARKETS,
            listed=listed,
            not_listed=not_listed,
            toggles=toggles,
            audit_url=base_audit_url,
            current_path=current_path,
            last_checked=last_checked,
            last_anchor=last_anchor,
            last_sku=last_sku,
            last_url=last_url,
        )

    @app.get("/")
    def audit_page():
        return view_state("audit")

    @app.post("/status")
    def set_status():
        audit_id = request.form.get("audit_id", "").strip()
        if audit_id:
            service.set_physical_status(audit_id, request.form.get("status", "unchecked"))
        return_to = request.form.get("return_to", "/") or "/"
        anchor = request.form.get("anchor", "")
        return redirect(return_to + (("#" + anchor) if anchor else ""))

    @app.post("/quick-unlisted")
    def quick_unlisted():
        sku = request.form.get("sku", "").strip()
        if not sku:
            return jsonify({"ok": False, "error": "SKU is required"}), 400
        service.add_unlisted_sku(sku)
        return jsonify({"ok": True, "sku": sku.upper()})

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

    return app


def start_mobile_server(service: AuditService) -> str:
    app = create_mobile_app(service)
    thread = threading.Thread(
        target=lambda: app.run(host=MOBILE_HOST, port=MOBILE_PORT, debug=False, use_reloader=False),
        daemon=True,
    )
    thread.start()
    return f"http://{_local_ip()}:{MOBILE_PORT}"
