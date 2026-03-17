"""Predictions API — parses real estate news and generates Monga sales insights."""
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["predictions"])

RSS_FEEDS = [
    {"name": "Le Moniteur Immobilier", "url": "https://www.lemoniteur.fr/rss/immobilier.xml"},
    {"name": "Batiactu", "url": "https://www.batiactu.com/feeds/edito-rss.php"},
    {"name": "MySweetImmo", "url": "https://www.mysweetimmo.com/feed/"},
    {"name": "Immo Matin", "url": "https://www.immomatin.com/feed/"},
    {"name": "Journal de l'Agence", "url": "https://www.journaldelagence.com/feed"},
]

# Keywords relevant to Monga's business
MONGA_KEYWORDS = {
    "high_relevance": ["travaux", "rénovation", "copropriété", "syndic", "gestion locative",
                        "entretien", "maintenance", "artisan", "DPE", "performance énergétique",
                        "MaPrimeRénov", "rénovation énergétique", "ravalement", "toiture",
                        "plomberie", "parties communes", "charges", "sinistre"],
    "medium_relevance": ["immobilier", "logement", "locataire", "propriétaire", "bailleur",
                          "gestion", "administrateur", "loi", "décret", "réglementation",
                          "marché immobilier", "investissement locatif"],
}

PITCH_ANGLES = {
    "rénovation énergétique": "Les obligations de rénovation énergétique (DPE) créent un besoin massif de coordination de travaux. Monga peut se positionner comme le partenaire qui simplifie cette transition pour les syndics.",
    "copropriété": "Les syndics sont débordés par la gestion des travaux en copropriété. Monga offre une solution clé en main : recherche d'artisans, suivi devis/factures, coordination.",
    "travaux": "Le volume de travaux dans l'immobilier augmente. Les agences n'ont pas les ressources internes pour gérer — c'est exactement le créneau de Monga.",
    "sinistre": "La gestion des sinistres (dégâts des eaux, etc.) est un cauchemar pour les gestionnaires. Monga peut proposer une prise en charge complète.",
    "réglementation": "Les nouvelles réglementations imposent plus de travaux obligatoires. Les agences auront besoin d'aide pour se conformer — argument de vente pour Monga.",
    "charges": "La hausse des charges pousse les copropriétés à optimiser leurs travaux. Monga aide à obtenir les meilleurs devis et à suivre les chantiers.",
    "artisan": "La pénurie d'artisans qualifiés rend la recherche difficile pour les gestionnaires. Le réseau d'artisans de Monga est un avantage compétitif.",
}


def _fetch_rss(url: str, source_name: str) -> list[dict]:
    """Fetch and parse an RSS feed."""
    articles = []
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                return []

        root = ET.fromstring(resp.content)

        # Handle both RSS 2.0 and Atom formats
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items[:10]:  # Max 10 per feed
            title = ""
            link = ""
            description = ""
            pub_date = ""

            # RSS 2.0
            title_el = item.find("title")
            if title_el is not None and title_el.text:
                title = title_el.text.strip()

            link_el = item.find("link")
            if link_el is not None:
                link = (link_el.text or link_el.get("href", "")).strip()

            desc_el = item.find("description")
            if desc_el is not None and desc_el.text:
                description = desc_el.text.strip()[:300]

            date_el = item.find("pubDate")
            if date_el is not None and date_el.text:
                pub_date = date_el.text.strip()

            if title:
                articles.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "pub_date": pub_date,
                    "source": source_name,
                })
    except Exception:
        pass

    return articles


def _analyze_article(article: dict) -> dict:
    """Score an article's relevance to Monga and generate pitch recommendations."""
    text = f"{article['title']} {article['description']}".lower()

    relevance_score = 0
    matched_keywords = []
    pitch_recommendations = []

    for kw in MONGA_KEYWORDS["high_relevance"]:
        if kw.lower() in text:
            relevance_score += 3
            matched_keywords.append(kw)

    for kw in MONGA_KEYWORDS["medium_relevance"]:
        if kw.lower() in text:
            relevance_score += 1
            matched_keywords.append(kw)

    # Generate pitch angles based on keywords
    for keyword, pitch in PITCH_ANGLES.items():
        if keyword.lower() in text:
            pitch_recommendations.append(pitch)

    return {
        **article,
        "relevance_score": relevance_score,
        "matched_keywords": list(set(matched_keywords)),
        "pitch_recommendations": list(set(pitch_recommendations)),
    }


@router.get("/predictions")
def get_predictions():
    """Fetch real estate news and generate Monga-relevant predictions."""
    all_articles = []
    feed_status = []

    for feed in RSS_FEEDS:
        articles = _fetch_rss(feed["url"], feed["name"])
        feed_status.append({"name": feed["name"], "articles_found": len(articles)})
        all_articles.extend(articles)

    # Analyze and score all articles
    analyzed = [_analyze_article(a) for a in all_articles]

    # Sort by relevance
    analyzed.sort(key=lambda x: x["relevance_score"], reverse=True)

    # Split into categories
    high_relevance = [a for a in analyzed if a["relevance_score"] >= 5]
    medium_relevance = [a for a in analyzed if 2 <= a["relevance_score"] < 5]

    # Aggregate pitch recommendations
    all_pitches = {}
    for a in high_relevance:
        for p in a["pitch_recommendations"]:
            if p not in all_pitches:
                all_pitches[p] = 0
            all_pitches[p] += 1

    top_pitches = sorted(all_pitches.items(), key=lambda x: x[1], reverse=True)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(analyzed),
        "feeds": feed_status,
        "high_relevance": high_relevance[:15],
        "medium_relevance": medium_relevance[:10],
        "top_pitch_angles": [{"pitch": p, "mentions": c} for p, c in top_pitches[:5]],
        "market_summary": {
            "total_relevant": len(high_relevance) + len(medium_relevance),
            "most_mentioned_topics": _get_top_topics(analyzed),
        },
    }


def _get_top_topics(articles: list[dict]) -> list[dict]:
    """Get the most mentioned topics across all articles."""
    topic_counts = {}
    for a in articles:
        for kw in a.get("matched_keywords", []):
            topic_counts[kw] = topic_counts.get(kw, 0) + 1

    sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
    return [{"topic": t, "count": c} for t, c in sorted_topics[:10]]
