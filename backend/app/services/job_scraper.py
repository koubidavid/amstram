"""Job scraper — Google (Serper.dev) + France Travail + direct website scan."""
import logging
import os
import re
import time
from urllib.parse import unquote

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.agence import Agence

logger = logging.getLogger(__name__)

SERPER_API_KEY = os.environ.get("SERPER_API_KEY", "")

TARGET_ROLES = [
    "gestionnaire locatif",
    "assistant gestion locative",
    "gestionnaire copropriété",
    "assistant copropriété",
]

FRANCE_TRAVAIL_URL = "https://candidat.francetravail.fr/offres/recherche"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

GENERIC_WORDS = frozenset([
    "sa", "sas", "sarl", "eurl", "sci", "de", "du", "la", "le", "les", "des",
    "et", "en", "immobilier", "immobiliere", "immobiliers", "gestion", "syndic",
    "cabinet", "agence", "groupe", "societe", "administration", "regie",
])

AGGREGATOR_DOMAINS = {
    "indeed.fr", "indeed.com", "hellowork.com", "linkedin.com", "jooble.org",
    "jobijoba.com", "cadremploi.fr", "apec.fr", "meteojob.com", "optioncarriere.com",
    "glassdoor.fr", "glassdoor.com", "keljob.com", "randstad.fr", "manpower.fr",
    "adecco.fr", "michaelpage.fr", "robertwalters.fr", "talent.com", "adzuna.fr",
    "cojob.fr", "emploi.org", "regionsjob.com", "staffsante.fr", "recrutimmo.com",
    "google.com", "google.fr", "youtube.com", "facebook.com", "wikipedia.org",
    "pole-emploi.fr", "duckduckgo.com", "jobrapido.com", "welcometothejungle.com",
    "monster.fr", "staffme.fr", "directemploi.com", "emploipublic.fr",
}


def _build_name_index(agences: list[Agence]) -> dict[str, list[Agence]]:
    """Build lookup: first significant word -> list of agencies."""
    index: dict[str, list[Agence]] = {}
    for a in agences:
        words = a.nom.lower().split()
        for word in words:
            if word in GENERIC_WORDS or len(word) < 3:
                continue
            if word not in index:
                index[word] = []
            index[word].append(a)
            break
    return index


def _is_aggregator(url: str) -> bool:
    domain = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if not domain:
        return True
    return any(agg in domain.group(1) for agg in AGGREGATOR_DOMAINS)


# ── Source 1: Google via Serper.dev ──────────────────────────────────────────

def _search_google(client: httpx.Client, query: str, num: int = 20) -> list[dict]:
    """Search Google via Serper.dev API. Returns list of {title, url, snippet}."""
    if not SERPER_API_KEY:
        return []

    try:
        resp = client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "gl": "fr", "hl": "fr", "num": num},
            timeout=10.0,
        )
        if resp.status_code != 200:
            return []

        data = resp.json()
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            })
        return results

    except Exception as e:
        logger.warning(f"Serper.dev error: {e}")
        return []


def _search_duckduckgo(client: httpx.Client, query: str) -> list[dict]:
    """Fallback: search DuckDuckGo."""
    try:
        resp = client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=HEADERS,
            timeout=10.0,
        )
        if resp.status_code != 200:
            return []

        results = []
        raw = re.findall(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.+?)</a>', resp.text)
        snippets = re.findall(r'class="result__snippet"[^>]*>(.+?)</[at]', resp.text)

        for i, (raw_url, raw_title) in enumerate(raw[:10]):
            title = re.sub(r"<[^>]+>", "", raw_title).strip()
            url_match = re.search(r"uddg=([^&]+)", raw_url)
            url = unquote(url_match.group(1)) if url_match else raw_url
            snippet = re.sub(r"<[^>]+>", "", snippets[i]).strip() if i < len(snippets) else ""
            results.append({"title": title, "url": url, "snippet": snippet})

        return results
    except Exception:
        return []


def search_engine(client: httpx.Client, query: str, num: int = 20) -> list[dict]:
    """Search Google (Serper) if API key available, otherwise DuckDuckGo."""
    results = _search_google(client, query, num)
    if results:
        return results
    return _search_duckduckgo(client, query)


# ── Source 2: France Travail ─────────────────────────────────────────────────

def _scrape_france_travail(client: httpx.Client, role: str, errors: list) -> list[dict]:
    """Scrape France Travail search results."""
    postings = []

    for page_start in [0, 15]:
        try:
            resp = client.get(
                FRANCE_TRAVAIL_URL,
                params={"motsCles": role, "offresPartenaires": "true", "range": f"{page_start}-{page_start+14}"},
                headers=HEADERS,
                timeout=12.0,
            )
            if resp.status_code != 200:
                continue

            entries = re.findall(r'<li[^>]*data-id-offre="([^"]+)"(.*?)</li>', resp.text, re.S)

            for offre_id, block in entries:
                title_m = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.S)
                title = re.sub(r'<[^>]+>', '', title_m.group(1)).strip() if title_m else ""
                desc_m = re.search(r'class="description"[^>]*>(.*?)<', block, re.S)
                desc = re.sub(r'<[^>]+>', '', desc_m.group(1)).strip()[:200] if desc_m else ""

                postings.append({
                    "title": title,
                    "url": f"https://candidat.francetravail.fr/offres/recherche/detail/{offre_id}",
                    "snippet": desc,
                    "role": role,
                    "source": "France Travail",
                })

        except Exception as e:
            errors.append(f"France Travail '{role}': {str(e)[:80]}")

    return postings


# ── Main: reverse search ────────────────────────────────────────────────────

def scan_jobs_reverse(db: Session, errors: list, log_fn=None) -> int:
    """Reverse search: Google/DDG + France Travail, then match to agencies."""
    agences = db.query(Agence).filter(Agence.siren.isnot(None)).all()
    if not agences:
        return 0

    name_index = _build_name_index(agences)
    source = "Google (Serper)" if SERPER_API_KEY else "DuckDuckGo"

    if log_fn:
        log_fn(f"Index de {len(agences)} agences. Recherche via {source} + France Travail...", "search")

    all_postings: list[dict] = []
    matched_agencies: dict[int, list[dict]] = {}

    with httpx.Client(timeout=12.0, follow_redirects=True) as client:
        for role in TARGET_ROLES:
            # Google/DuckDuckGo search
            queries = [
                f'offre emploi "{role}" agence immobilière recrutement',
                f'"{role}" recrute CDI immobilier 2026',
            ]

            role_count = 0
            for query in queries:
                results = search_engine(client, query, num=30)
                for r in results:
                    r["role"] = role
                    r["source"] = source
                    all_postings.append(r)
                    role_count += 1
                time.sleep(1)

            if log_fn:
                log_fn(f"{source} « {role} » — {role_count} résultats", "search", count=role_count)

            time.sleep(1)

    if log_fn:
        log_fn(f"{len(all_postings)} résultats collectés. Matching avec les agences...", "database")

    # Match to agencies
    for posting in all_postings:
        title_lower = (posting.get("title", "") + " " + posting.get("snippet", "")).lower()

        for word, agency_list in name_index.items():
            if word in title_lower:
                is_job = any(kw in title_lower for kw in [
                    "recrutement", "emploi", "offre", "poste", "recrute",
                    "cdi", "cdd", "gestionnaire", "assistant", "copropriété", "locatif",
                    "h/f", "f/h",
                ])
                if not is_job:
                    continue

                for agence in agency_list:
                    if agence.id not in matched_agencies:
                        matched_agencies[agence.id] = []
                    matched_agencies[agence.id].append({
                        "role": posting.get("role", ""),
                        "title": posting.get("title", "")[:200],
                        "url": posting.get("url", "")[:300],
                        "source": posting.get("source", ""),
                    })

    # Save
    found = 0
    for agence in agences:
        findings = matched_agencies.get(agence.id, [])
        seen = set()
        unique = [f for f in findings if not (f["title"][:50] in seen or seen.add(f["title"][:50]))]

        if agence.offres_emploi_detectees is None:
            agence.offres_emploi_detectees = unique if unique else []

        if unique:
            found += 1
            if log_fn:
                roles = list(set(f["role"] for f in unique))
                log_fn(f"🔥 {agence.nom} — {len(unique)} offre(s) ({', '.join(roles[:2])})", "fire", count=found)

    db.commit()

    if log_fn:
        log_fn(f"Résultat : {found} agence(s) recrutent sur {len(agences)} en base", "success" if found > 0 else "info", count=found)

    return found


# ── Live search (for /emploi page) ──────────────────────────────────────────

def live_search_jobs(db: Session) -> dict:
    """Live search: returns all links found, grouped by role, with agency matching."""
    agences = db.query(Agence).filter(Agence.siren.isnot(None)).all()
    name_index = _build_name_index(agences)
    source = "Google" if SERPER_API_KEY else "DuckDuckGo"

    all_links = []
    by_role = {}
    ft_links = []

    with httpx.Client(timeout=12.0, follow_redirects=True) as client:
        for role in TARGET_ROLES:
            role_links = []

            # Search engine
            queries = [
                f'offre emploi "{role}" agence immobilière',
                f'"{role}" recrute CDI immobilier',
                f'"{role}" recrutement agence',
            ]
            for query in queries:
                results = search_engine(client, query, num=20)
                for r in results:
                    matched_agency = _find_agency_match(r, name_index, agences)
                    link = {
                        "title": r["title"][:150],
                        "url": r["url"][:300],
                        "snippet": r.get("snippet", "")[:200],
                        "domain": _extract_domain(r["url"]),
                        "is_aggregator": _is_aggregator(r["url"]),
                        "matched_agency": matched_agency,
                        "role": role,
                        "source": source,
                    }
                    role_links.append(link)
                    all_links.append(link)
                time.sleep(1)

            by_role[role] = role_links
            time.sleep(1)

    # Filter and categorize
    agency_links = [l for l in all_links if not l["is_aggregator"]]
    matched_links = [l for l in all_links if l["matched_agency"]]

    return {
        "total_links": len(all_links),
        "agency_links": len(agency_links),
        "matched_to_db": len(matched_links),
        "search_engine": source,
        "by_role": {role: [l for l in links] for role, links in by_role.items()},
        "all_links": all_links,
        "all_matched": matched_links,
        "all_non_aggregator": agency_links,
    }


def _find_agency_match(result: dict, name_index: dict, agences: list) -> str | None:
    text = (result.get("title", "") + " " + result.get("snippet", "")).lower()
    for a in agences:
        words = a.nom.lower().split()
        for word in words:
            if word in GENERIC_WORDS or len(word) < 4:
                continue
            if word in text:
                return a.nom
    return None


def _extract_domain(url: str) -> str:
    m = re.search(r'https?://(?:www\.)?([^/]+)', url)
    return m.group(1) if m else ""


# ── Direct website scanning ──────────────────────────────────────────────────

CAREER_PATHS = [
    "/recrutement", "/carrieres", "/careers", "/emploi",
    "/nous-rejoindre", "/rejoignez-nous", "/jobs", "/offres-emploi",
    "/recrutement/offres", "/carrieres/offres",
]


def scan_agency_websites(db: Session, errors: list, log_fn=None) -> int:
    """Scan agency websites directly for career pages."""
    agences = (
        db.query(Agence)
        .filter(Agence.site_web.isnot(None), Agence.site_web != "")
        .filter(Agence.offres_emploi_detectees == [])
        .limit(30)
        .all()
    )

    if not agences:
        if log_fn:
            log_fn("Aucune agence avec site web à scanner", "info")
        return 0

    if log_fn:
        log_fn(f"Scan direct de {len(agences)} sites agences...", "search")

    found = 0

    with httpx.Client(timeout=8.0, follow_redirects=True) as client:
        for i, agence in enumerate(agences):
            site_findings = _scan_one_website(client, agence.site_web, agence.nom, errors)

            if site_findings:
                existing = agence.offres_emploi_detectees or []
                agence.offres_emploi_detectees = existing + site_findings
                found += 1
                roles = list(set(f["role"] for f in site_findings))
                if log_fn:
                    log_fn(f"🔥 {agence.nom} — offre(s) sur leur site ({', '.join(roles[:2])})", "fire", count=found)

            if (i + 1) % 10 == 0 and log_fn:
                log_fn(f"Sites scannés : {i+1}/{len(agences)}, {found} avec offres", "search")

    db.commit()

    if log_fn:
        log_fn(f"Scan sites terminé : {found} agence(s) avec offres", "success" if found > 0 else "info", count=found)

    return found


def _scan_one_website(client: httpx.Client, site_web: str, agence_nom: str, errors: list) -> list[dict]:
    findings = []
    base_url = site_web if site_web.startswith("http") else f"https://{site_web}"

    for path in CAREER_PATHS:
        try:
            resp = client.get(f"{base_url}{path}", headers=HEADERS, timeout=6.0)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ", strip=True).lower()

            for role in TARGET_ROLES:
                if role in text:
                    findings.append({
                        "role": role,
                        "title": f"Offre sur le site : {role}",
                        "url": f"{base_url}{path}",
                        "source": "Site agence",
                    })

            if findings:
                break
        except Exception:
            continue

    return findings
