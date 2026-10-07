"""Deal Bot — Config."""
import os

TG_TOKEN = os.environ.get("TG_TOKEN", "")
TG_CHAT = os.environ.get("TG_CHAT", "")

SITES = {
    "desidime": {
        "label": "DesiDime", "icon": "🟠",
        "url": "https://www.desidime.com/deals", "enabled": True,
    },
    "freekaamaal": {
        "label": "FreeKaaMaal", "icon": "🟢",
        "url": "https://www.freekaamaal.com/", "enabled": True,
    },
    "coupondunia": {
        "label": "CouponDunia", "icon": "🔵",
        "url": "https://www.coupondunia.in/", "enabled": True,
    },
    "grabon": {
        "label": "GrabOn", "icon": "🟣",
        "url": "https://www.grabon.in/deals/", "enabled": True,
    },
    "zoutons": {
        "label": "Zoutons", "icon": "🟡",
        "url": "https://www.zoutons.com/", "enabled": True,
    },
    "indiafreestuff": {
        "label": "IndiaFreeStuff", "icon": "🔴",
        "url": "https://www.indiafreestuff.in/", "enabled": True,
    },
    "dealyaan": {
        "label": "DealYaan", "icon": "⚪",
        "url": "https://www.dealyaan.com/", "enabled": True,
    },
    "savethedeals": {
        "label": "SaveTheDeals", "icon": "🟤",
        "url": "https://savethedeals.in/", "enabled": True,
    },
    "achhadeals": {
        "label": "AchhaDeals", "icon": "🟢",
        "url": "https://achhadeals.com/", "enabled": True,
    },
    "mytokri": {
        "label": "MyTokri", "icon": "🟠",
        "url": "https://www.mytokri.com/", "enabled": True,
    },
}

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
]

DEAL_KEYWORDS = (
    "off", "discount", "sale", "deal", "free", "cashback",
    "coupon", "promo", "₹", "rs.", "flat", "%",
)

REQUEST_DELAY = 1.5
MAX_DEALS_PER_SITE = 15
