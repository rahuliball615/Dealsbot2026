cat > /storage/emulated/0/2027/dealsbot/scraper.py << 'EOF'
"""Deal Bot — Multi-site scraper."""
import re, time, random
from datetime import datetime
from curl_cffi import requests as creq
from bs4 import BeautifulSoup
from config import SITES, UA_LIST, REQUEST_DELAY, MAX_DEALS_PER_SITE, DEAL_KEYWORDS


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def _get(url, timeout=20):
    try:
        r = creq.get(url,
            headers={
                "User-Agent": random.choice(UA_LIST),
                "Accept": "text/html,application/xhtml+xml,*/*",
                "Accept-Language": "en-IN,en;q=0.9",
            },
            impersonate="chrome150", timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r.text
        log(f"  HTTP {r.status_code} {url[:50]}")
    except Exception as e:
        log(f"  err: {str(e)[:50]}")
    return None


def _clean_price(t):
    if not t:
        return None
    m = re.search(r"₹\s*([\d,]+)", str(t))
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            return None
    return None


def _is_deal(title):
    if not title or len(title) < 15:
        return False
    tl = title.lower()
    return any(k in tl for k in DEAL_KEYWORDS)


def scrape_desidime(html):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for card in soup.select("div.item, div.deal-item, article"):
        try:
            el = (card.select_one("h3 a") or card.select_one("h2 a")
                  or card.select_one("a.deal-title"))
            if not el:
                continue
            title = el.get_text(" ", strip=True)
            if not _is_deal(title):
                continue
            url = el.get("href", "")
            if url.startswith("/"):
                url = "https://www.desidime.com" + url
            price_el = card.select_one(".price, .deal-price")
            price = _clean_price(price_el.get_text()) if price_el else None
            out.append({"title": title[:120], "url": url, "price": price})
            if len(out) >= MAX_DEALS_PER_SITE:
                break
        except Exception:
            continue
    return out


def scrape_freekaamaal(html):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for card in soup.select("a[href*='amazon'], a[href*='flipkart'], div.deal-item"):
        try:
            title = card.get_text(" ", strip=True)
            if not _is_deal(title):
                continue
            url = card.get("href", "")
            if url and not url.startswith("http"):
                url = "https://www.freekaamaal.com" + url
            out.append({"title": title[:120], "url": url, "price": None})
            if len(out) >= MAX_DEALS_PER_SITE:
                break
        except Exception:
            continue
    return out


def scrape_coupondunia(html):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for card in soup.select("a.coupon, div.coupon, a.offer"):
        try:
            title = card.get_text(" ", strip=True)
            if not _is_deal(title):
                continue
            url = card.get("href", "")
            if url and not url.startswith("http"):
                url = "https://www.coupondunia.in" + url
            out.append({"title": title[:120], "url": url, "price": None})
            if len(out) >= MAX_DEALS_PER_SITE:
                break
        except Exception:
            continue
    return out


def scrape_grabon(html):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for card in soup.select("a.deal, div.deal-box, div.dealItem"):
        try:
            title = card.get_text(" ", strip=True)
            if not _is_deal(title):
                continue
            url = card.get("href", "")
            if url and not url.startswith("http"):
                url = "https://www.grabon.in" + url
            out.append({"title": title[:120], "url": url, "price": None})
            if len(out) >= MAX_DEALS_PER_SITE:
                break
        except Exception:
            continue
    return out


def scrape_generic(html):
    soup = BeautifulSoup(html, "lxml")
    out = []
    seen = set()
    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        if not _is_deal(title):
            continue
        url = a["href"]
        if url in seen:
            continue
        seen.add(url)
        out.append({"title": title[:120], "url": url, "price": None})
        if len(out) >= MAX_DEALS_PER_SITE:
            break
    return out


PARSERS = {
    "desidime": scrape_desidime,
    "freekaamaal": scrape_freekaamaal,
    "coupondunia": scrape_coupondunia,
    "grabon": scrape_grabon,
}


def scrape_all():
    all_deals = []
    for key, cfg in SITES.items():
        if not cfg.get("enabled"):
            continue
        log(f"→ {cfg['label']:15} {cfg['url']}")
        html = _get(cfg["url"])
        if not html:
            continue
        parser = PARSERS.get(key, scrape_generic)
        try:
            deals = parser(html)
        except Exception as e:
            log(f"  parse err: {str(e)[:50]}")
            deals = scrape_generic(html)
        log(f"  {len(deals)} deals")
        for d in deals:
            d["site"] = key
            d["site_label"] = cfg["label"]
            d["site_icon"] = cfg["icon"]
        all_deals.extend(deals)
        time.sleep(REQUEST_DELAY)
    return all_deals
EOF

python3 -m py_compile /storage/emulated/0/2027/dealsbot/scraper.py && echo "scraper OK"
