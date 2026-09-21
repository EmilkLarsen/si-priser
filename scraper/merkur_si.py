'"""Merkur.si (EUR, Slovenia's largest DIY/building chain) — batched sitemaps
/media/sitemap/sitemap-{1..N}-{batch}.xml; product URLs are deep paths ending
in slug; ld+json Product with EUR price."""
import re
from common import get, sitemap_urls, sane_price, valid_ean, first_str, ldjson_products, offer_from_ld, write_jsonl, pmap

BASE = "https://www.merkur.si"
OUT = "data/latest/merkur_si.jsonl"


def fetch_url_list(limit=None):
    urls = []
    for chunk in range(1, 4):
        for batch in range(1, 6):
            try:
                xml = get(f"{BASE}/media/sitemap/sitemap-{chunk}-{batch}.xml")
            except Exception:
                continue
            # product URLs are deep paths (4+ segments) that aren't categories
            us = [u for u in sitemap_urls(xml)
                  if u.rstrip("/").count("/") >= 4 and "/produkt" not in u.lower()]
            urls.extend(us)
            if limit and len(urls) >= limit:
                return urls[:limit]
    return urls[:limit] if limit else urls


def handle(u, html):
    rows = []
    for p in ldjson_products(html):
        off = offer_from_ld(p)
        if off:
            off["price"] = sane_price(off["price"])
        if not off or not off["price"]:
            continue
        t = re.search(r"<title[^>]*>([^<]+)</title>", html)
        name = (t.group(1).split("|")[0].strip() if t else u.rsplit("/", 1)[-1])
        rows.append({
            "chain": "merkur_si",
            "country": "si",
            "currency": off["currency"],
            "sku": None,
            "ean": valid_ean(p.get("gtin13") or p.get("gtin") or p.get("ean")),
            "name": name,
            "url": u,
            "price": off["price"],
            "in_stock": off["in_stock"],
            "image": first_str(p.get("image")),
        })
        break
    return rows


def scrape(limit=None):
    return scrape_urls(fetch_url_list(limit), handle)


if __name__ == "__main__":
    import sys
    lim = int(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = scrape(lim)
    write_jsonl(OUT, rows)
    print("merkur_si: %d products -> %s" % (len(rows), OUT))
