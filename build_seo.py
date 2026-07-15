#!/usr/bin/env python3
"""
build_seo.py — bake AI-citable content into index.html from games.json.

The interactive card grid is rendered by JavaScript, which most AI crawlers
(GPTBot, ClaudeBot, PerplexityBot, Google-Extended) never execute — so without
this step the 166 games are invisible to the systems we want citing us. This
injects, between marker comments in index.html:

  * SEO:CARDS  — the full list as static cards (visible in raw HTML)
  * SEO:FAQ    — a human-readable FAQ (mirrored in the JSON-LD below)
  * SEO:JSONLD — Dataset + ItemList(VideoGame) + FAQPage + Person structured data

Re-run after editing games.json:  python build_seo.py
"""

import json
import html
import re
import sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).parent
HTML = HERE / "index.html"
DATA = HERE / "games.json"

PAGE_URL = "https://michaelnocito.github.io/steam-hidden-gems-list/"
AUTHOR_URL = "https://michaelnocito.github.io"
PUBLISHED = "2026-07-08"
MODIFIED = "2026-07-14"


def esc(s):
    return html.escape(str(s), quote=True)


def store_url(g):
    if g.get("appid"):
        return f"https://store.steampowered.com/app/{g['appid']}/"
    return f"https://store.steampowered.com/search/?term={quote(g.get('searchTerm') or g['name'])}"


def img_url(g):
    return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{g['appid']}/header.jpg" if g.get("appid") else None


def rank_label(g):
    if g.get("rank"):
        return f'#{g["rank"]}'
    if g.get("freeRank"):
        return f'Free #{g["freeRank"]}'
    return ""


def price_number(g):
    """Return float USD price, or None if free/unparseable."""
    if g.get("free"):
        return 0.0
    m = re.search(r"[\d.]+", str(g.get("price", "")))
    return float(m.group()) if m else None


# ---------- static cards (what crawlers read) ----------
def build_cards(games):
    out = []
    for g in games:
        img = img_url(g)
        thumb = (
            f'<img loading="lazy" src="{img}" alt="{esc(g["name"])}" />'
            if img else f'<div class="noimg">{esc(g["name"])}</div>'
        )
        rl = rank_label(g)
        free_cls = " free" if g.get("free") else ""
        out.append(
            f'<div class="card" data-free="{str(bool(g.get("free"))).lower()}" data-name="{esc(g["name"].lower())}">'
            f'<div class="thumb">{thumb}'
            + (f'<span class="rankbadge">{rl}</span>' if rl else "")
            + f'<span class="pricepill{free_cls}">{esc(g["price"])}</span></div>'
            f'<div class="body"><h3>{esc(g["name"])}</h3>'
            f'<div class="meta"><span class="pos">{g["positive"]}% positive</span> · '
            f'<span>{g["reviews"]:,} reviews</span></div>'
            + (f'<p class="pitch">{esc(g["pitch"])}</p>' if g.get("pitch") else "")
            + f'</div>'
            f'<div class="actions"><a class="steam-btn" href="{store_url(g)}" target="_blank" rel="noopener">View on Steam ↗</a></div>'
            f'</div>'
        )
    return "\n".join(out)


# ---------- FAQ (visible + JSON-LD, single source of truth) ----------
def faq_items(meta):
    analyzed = f'{meta["totalAnalyzed"]:,}'
    gems = meta["totalGems"]
    raw = meta.get("rawFilterCount", gems)
    return [
        ("What counts as a “hidden gem” Steam game here?",
         f'A game qualifies if it has <b>2,000+ reviews</b> that are <b>95%+ positive</b>, is priced <b>$20 or under</b>, '
         f'and has a genuinely small audience (roughly <b>20,000–200,000 owners</b>). Highly rated, cheap, and still under the radar. '
         f'{raw} games cleared the raw filter; 9 were removed for corrupted or duplicate owner data (Steam mega-hits mislabeled as tiny), '
         f'leaving <b>{gems}</b> real hidden gems.'),
        ("How were these games found?",
         f'With SQL. I queried a public Steam dataset of about <b>{analyzed} games</b>, applied the review, rating, price, '
         f'and audience thresholds above, ranked the survivors, and hand-checked the outliers. The full methodology, the exact SQL, '
         f'and the data-cleaning story are in the companion GitHub repository.'),
        ("How many games were analyzed?",
         f'{analyzed} titles were in the dataset. After filtering and cleaning, {gems} met every criterion and made the list.'),
        ("Are these games free or paid?",
         'Most are paid but cheap ($20 or under); a few are free-to-play. Use the “Free only” and “Paid picks” filters on the page. '
         'Every card links straight to the game’s Steam store page.'),
        ("What’s the data source, and how current is it?",
         'The Steam Games Dataset by FronkonGames (published on Kaggle). Review counts and ratings reflect that dataset snapshot.'),
        ("Who made this, and how should I cite it?",
         'Built by <b>Michael Nocito</b>, a data analyst. You can cite it as '
         '“Steam Hidden Gems (Michael Nocito, 2026), michaelnocito.github.io/steam-hidden-gems-list”. '
         'The underlying review and ownership figures come from the FronkonGames Steam dataset.'),
    ]


def build_faq_html(items):
    return "\n".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in items)


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


# ---------- JSON-LD ----------
def build_jsonld(meta, games, items):
    person = {
        "@type": "Person",
        "@id": AUTHOR_URL + "/#michaelnocito",
        "name": "Michael Nocito",
        "url": AUTHOR_URL,
        "jobTitle": "Data Analyst",
    }

    def game_node(g):
        node = {
            "@type": "VideoGame",
            "name": g["name"],
            "url": store_url(g),
            "gamePlatform": "PC (Steam)",
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": g["positive"],
                "bestRating": 100,
                "worstRating": 0,
                "ratingCount": g["reviews"],
                "description": f'{g["positive"]}% of {g["reviews"]:,} Steam reviews are positive',
            },
        }
        price = price_number(g)
        if price is not None:
            node["offers"] = {
                "@type": "Offer",
                "price": price,
                "priceCurrency": "USD",
                "url": store_url(g),
            }
        return node

    item_list = {
        "@type": "ItemList",
        "name": "Steam Hidden Gems",
        "numberOfItems": len(games),
        "itemListOrder": "https://schema.org/ItemListOrderDescending",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "item": game_node(g)}
            for i, g in enumerate(games)
        ],
    }
    dataset = {
        "@type": "Dataset",
        "@id": PAGE_URL + "#dataset",
        "name": "Steam Hidden Gems — 166 highly-rated, under-owned games",
        "description": (
            f'{meta["totalGems"]} Steam hidden gems surfaced with SQL from a dataset of about '
            f'{meta["totalAnalyzed"]:,} games. Criteria: {meta["criteria"]}'
        ),
        "url": PAGE_URL,
        "creator": person,
        "isBasedOn": "https://www.kaggle.com/datasets/fronkongames/steam-games-dataset",
        "measurementTechnique": "SQL aggregation and threshold filtering over the Steam games dataset",
        "variableMeasured": ["percent positive reviews", "total reviews", "price (USD)", "estimated owners"],
        "distribution": {
            "@type": "DataDownload",
            "encodingFormat": "application/json",
            "contentUrl": PAGE_URL + "games.json",
        },
    }
    webpage = {
        "@type": "CollectionPage",
        "@id": PAGE_URL + "#webpage",
        "url": PAGE_URL,
        "name": "Steam Hidden Gems — 166 great games almost nobody has played",
        "description": (
            f'{meta["totalGems"]} Steam hidden gems — 2,000+ reviews, 95%+ positive, under $20 '
            f'— surfaced with SQL from a {meta["totalAnalyzed"]:,}-game dataset.'
        ),
        "author": person,
        "creator": person,
        "datePublished": PUBLISHED,
        "dateModified": MODIFIED,
        "isPartOf": {"@type": "WebSite", "name": "Michael Nocito", "url": AUTHOR_URL},
        "mainEntity": {"@id": PAGE_URL + "#dataset"},
    }
    faqpage = {
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
            for q, a in items
        ],
    }
    graph = {"@context": "https://schema.org", "@graph": [webpage, person, dataset, item_list, faqpage]}
    return '<script type="application/ld+json">\n' + json.dumps(graph, ensure_ascii=False, indent=2) + "\n</script>"


def inject(text, start_marker, end_marker, payload, label):
    pattern = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.DOTALL)
    if not pattern.search(text):
        sys.exit(f"ERROR: markers for {label} not found ({start_marker} ... {end_marker})")
    return pattern.sub(start_marker + "\n" + payload + "\n" + end_marker, text)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    meta, games = data["meta"], data["games"]
    items = faq_items(meta)

    text = HTML.read_text(encoding="utf-8")
    text = inject(text, "<!-- SEO:CARDS:START -->", "<!-- SEO:CARDS:END -->", build_cards(games), "cards")
    text = inject(text, "<!-- SEO:FAQ:START -->", "<!-- SEO:FAQ:END -->", build_faq_html(items), "faq")
    text = inject(text, "<!-- SEO:JSONLD:START -->", "<!-- SEO:JSONLD:END -->", build_jsonld(meta, games, items), "jsonld")
    HTML.write_text(text, encoding="utf-8")
    print(f"Baked {len(games)} games into index.html (cards + FAQ + JSON-LD).")


if __name__ == "__main__":
    main()
