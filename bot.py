cat > /storage/emulated/0/2027/dealsbot/bot.py << 'EOF'
"""Deal Aggregator Bot — GitHub Actions + Telegram."""
import os, json, re, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path
from scraper import scrape_all, log

TG_TOKEN = os.environ.get("TG_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT", "")

STATE_FILE = Path("seen.json")
KEYWORDS_FILE = Path("keywords.json")


def send_tg(text, chat_id=None):
    cid = chat_id or TG_CHAT
    if not TG_TOKEN or not cid:
        log("[!] TG creds missing")
        return False
    payload = {"chat_id": cid, "text": text, "parse_mode": "HTML",
               "disable_web_page_preview": "true"}
    data = urllib.parse.urlencode(payload).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage", data=data)
    try:
        r = urllib.request.urlopen(req, timeout=15)
        return json.loads(r.read().decode()).get("ok", False)
    except urllib.error.HTTPError as e:
        log(f"[!] TG: {e.read().decode()[:100]}")
        return False
    except Exception as e:
        log(f"[!] TG: {str(e)[:80]}")
        return False


def tg_get_updates(offset):
    if not TG_TOKEN:
        return []
    try:
        params = urllib.parse.urlencode({
            "offset": offset, "timeout": 1,
            "allowed_updates": json.dumps(["message"]),
        })
        r = urllib.request.urlopen(
            f"https://api.telegram.org/bot{TG_TOKEN}/getUpdates?{params}",
            timeout=15)
        data = json.loads(r.read().decode())
        return data.get("result", []) if data.get("ok") else []
    except Exception:
        return []


def load_json(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def load_keywords():
    return load_json(KEYWORDS_FILE, {
        "keywords": ["iphone", "laptop", "ssd", "ps5"],
        "last_update_id": 0,
    })


def load_seen():
    return load_json(STATE_FILE, {"urls": [], "last_run": ""})


def match_keywords(deal, keywords):
    if not keywords:
        return True
    title = (deal.get("title") or "").lower()
    return any(k.lower() in title for k in keywords)


HELP = """<b>🤖 Deal Aggregator Bot</b>

<b>Keywords:</b>
/add &lt;word&gt;     — add
/rm &lt;word&gt;      — remove
/list           — show
/clear          — clear all

<b>Info:</b>
/sites          — supported sites
/stats          — stats
/help           — ye help

<i>Alerts GitHub Actions se aate hain</i>"""


def handle_command(text, chat_id, kw, seen):
    parts = text.strip().split()
    if not parts:
        return False
    cmd = parts[0].lower().split("@")[0]
    args = parts[1:]

    if cmd in ("/start", "/help"):
        send_tg(HELP, chat_id)
        return False

    if cmd == "/add":
        if not args:
            send_tg("Usage: <code>/add iphone</code>", chat_id)
            return False
        w = args[0].lower()
        if w in kw["keywords"]:
            send_tg(f"Already hai: <b>{w}</b>", chat_id)
            return False
        kw["keywords"].append(w)
        send_tg(f"✅ Added: <b>{w}</b> (total {len(kw['keywords'])})", chat_id)
        return True

    if cmd in ("/rm", "/remove"):
        if not args:
            send_tg("Usage: <code>/rm iphone</code>", chat_id)
            return False
        w = args[0].lower()
        if w in kw["keywords"]:
            kw["keywords"].remove(w)
            send_tg(f"🗑️ Removed: <b>{w}</b>", chat_id)
        else:
            send_tg(f"❌ Nahi mila: <b>{w}</b>", chat_id)
        return False

    if cmd == "/list":
        if not kw["keywords"]:
            send_tg("Koi keyword nahi. <code>/add iphone</code>", chat_id)
            return False
        lines = ["<b>📋 Keywords:</b>", ""]
        for i, w in enumerate(kw["keywords"], 1):
            lines.append(f"{i}. <code>{w}</code>")
        send_tg("\n".join(lines), chat_id)
        return False

    if cmd == "/clear":
        kw["keywords"] = []
        send_tg("🧹 Sab clear", chat_id)
        return True

    if cmd == "/sites":
        from config import SITES
        lines = ["<b>🌐 Sites:</b>", ""]
        for k, c in SITES.items():
            if c.get("enabled"):
                lines.append(f"{c['icon']} {c['label']}")
        send_tg("\n".join(lines), chat_id)
        return False

    if cmd == "/stats":
        msg = (f"<b>📊 Stats</b>\n\n"
               f"  Keywords: <b>{len(kw['keywords'])}</b>\n"
               f"  Seen URLs: <b>{len(seen.get('urls', []))}</b>\n"
               f"  Last run: <code>{seen.get('last_run', 'never')}</code>")
        send_tg(msg, chat_id)
        return False

    return False


def main():
    log("=" * 50)
    log("Deal Aggregator Run")
    kw = load_keywords()
    seen = load_seen()

    # Telegram commands
    offset = kw.get("last_update_id", 0) + 1
    updates = tg_get_updates(offset)
    kw_changed = False
    for u in updates:
        kw["last_update_id"] = max(kw.get("last_update_id", 0),
                                    u.get("update_id", 0))
        kw_changed = True
        msg = u.get("message") or {}
        text = msg.get("text", "")
        chat_id = msg.get("chat", {}).get("id")
        if text.startswith("/"):
            log(f"[tg] {text[:50]}")
            try:
                if handle_command(text, chat_id, kw, seen):
                    kw_changed = True
            except Exception as e:
                log(f"[!] cmd err: {e}")
    if kw_changed:
        save_json(KEYWORDS_FILE, kw)

    # Scrape
    log(f"Keywords: {kw['keywords']}")
    deals = scrape_all()
    log(f"Total: {len(deals)}")

    # Filter new
    seen_urls = set(seen.get("urls", []))
    new_deals = []
    for d in deals:
        url = d.get("url", "")
        if not url or url in seen_urls:
            continue
        if not match_keywords(d, kw["keywords"]):
            continue
        new_deals.append(d)
        seen_urls.add(url)

    log(f"New: {len(new_deals)}")

    if new_deals:
        by_site = {}
        for d in new_deals:
            by_site.setdefault(d["site_label"], []).append(d)

        send_tg(f"🔥 <b>NEW DEALS</b> ({len(new_deals)})\n" + "━" * 15)
        for site, items in by_site.items():
            lines = [f"\n<b>{items[0]['site_icon']} {site}</b>"]
            for d in items[:5]:
                pt = f"  <b>₹{d['price']:,}</b>" if d.get("price") else ""
                lines.append(f"\n• <a href='{d['url']}'>{d['title'][:90]}</a>{pt}")
            if len(items) > 5:
                lines.append(f"\n<i>...aur {len(items)-5}</i>")
            send_tg("\n".join(lines))
            time.sleep(1)

    seen["urls"] = list(seen_urls)[-2000:]
    seen["last_run"] = datetime.now().isoformat()
    save_json(STATE_FILE, seen)
    save_json(KEYWORDS_FILE, kw)
    log("Done.")


if __name__ == "__main__":
    main()
EOF

python3 -m py_compile /storage/emulated/0/2027/dealsbot/bot.py && echo "bot OK"
