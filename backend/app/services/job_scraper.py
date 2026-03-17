"""Job scraper — reverse search + direct website scan."""
import logging
import re
from urllib.parse import unquote

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.agence import Agence

logger = logging.getLogger(__name__)

TARGET_ROLES = [
    "gestionnaire locatif",
    "assistant gestion locative",
    "gestionnaire copropriété",
    "assistant copropriété",
]

# Compact search queries — one per role, across multiple sources
SEARCH_QUERIES = [
    # Job boards
    '"{role}" recrutement immobilier site:indeed.fr OR site:hellowork.com OR site:welcometothejungle.com',
    '"{role}" offre emploi agence immobilière site:linkedin.com OR site:apec.fr OR site:cadremploi.fr',
    # Agency career portals (grands réseaux)
    '"{role}" site:recrutement.nestenn.com OR site:recrutement.foncia.com OR site:citya-immobilier.com/recrutement',
    '"{role}" site:nexity.fr/emploi OR site:oralia.fr/recrutement OR site:sergic.com/recrutement OR site:laforet.com/recrutement',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def scan_jobs_reverse(db: Session, errors: list, log_fn=None) -> int:
    """Reverse job search: query job boards for target roles, match results to our agencies.

    Instead of N queries per agency (slow), we do ~8 queries total (fast):
    - 4 roles x 2 query templates = 8 DuckDuckGo requests
    - Then fuzzy-match company names from results against our 700+ agencies
    """
    import time

    # Load all agency names for matching
    agences = db.query(Agence).filter(Agence.siren.isnot(None)).all()
    if not agences:
        return 0

    # Build lookup: first significant word of agency name -> list of agences
    # e.g. "foncia" -> [Foncia Paris, Foncia Lyon, ...]
    name_index: dict[str, list[Agence]] = {}
    for a in agences:
        words = a.nom.lower().split()
        for word in words:
            # Skip generic words
            if word in ("sa", "sas", "sarl", "eurl", "sci", "sci", "de", "du", "la", "le",
                        "les", "des", "et", "en", "immobilier", "immobiliere", "immobiliers",
                        "gestion", "syndic", "cabinet", "agence", "groupe", "societe"):
                continue
            if len(word) >= 3:
                if word not in name_index:
                    name_index[word] = []
                name_index[word].append(a)
                break  # Only index on the first significant word

    if log_fn:
        log_fn(f"Index de {len(agences)} agences prêt. Recherche des offres d'emploi...", "search")

    # Collect all job postings from DuckDuckGo
    all_postings: list[dict] = []

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        for role in TARGET_ROLES:
            for query_tpl in SEARCH_QUERIES:
                query = query_tpl.format(role=role)
                try:
                    resp = client.get(
                        "https://html.duckduckgo.com/html/",
                        params={"q": query},
                        headers=HEADERS,
                        timeout=10.0,
                    )
                    if resp.status_code != 200:
                        continue

                    results = re.findall(
                        r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.+?)</a>',
                        resp.text,
                    )

                    for raw_url, raw_title in results[:8]:
                        title = re.sub(r"<[^>]+>", "", raw_title).strip()
                        url_match = re.search(r"uddg=([^&]+)", raw_url)
                        url = unquote(url_match.group(1)) if url_match else raw_url

                        all_postings.append({
                            "role": role,
                            "title": title[:200],
                            "url": url[:300],
                            "title_lower": title.lower(),
                        })

                    time.sleep(1.5)  # Rate limit between queries

                except Exception as e:
                    errors.append(f"DuckDuckGo '{role}': {str(e)[:80]}")
                    continue

            if log_fn:
                log_fn(f"Recherche « {role} » — {len(all_postings)} résultats trouvés", "search", count=len(all_postings))

    if log_fn:
        log_fn(f"{len(all_postings)} offres d'emploi trouvées au total. Matching avec les agences...", "database")

    # Match postings to our agencies
    matched_agencies: dict[int, list[dict]] = {}  # agence.id -> list of findings

    for posting in all_postings:
        title_lower = posting["title_lower"]

        # Check if any agency name word appears in the title
        for word, agency_list in name_index.items():
            if word in title_lower:
                # Verify it's actually a job posting
                is_job = any(kw in title_lower for kw in [
                    "recrutement", "emploi", "offre", "poste", "recrute",
                    "cdi", "cdd", "stage", "alternance", "careers",
                    "gestionnaire", "assistant", "copropriété", "locatif",
                    "h/f", "f/h", "m/f",
                ])
                if not is_job:
                    continue

                for agence in agency_list:
                    if agence.id not in matched_agencies:
                        matched_agencies[agence.id] = []
                    matched_agencies[agence.id].append({
                        "role": posting["role"],
                        "title": posting["title"],
                        "url": posting["url"],
                        "source": "DuckDuckGo (recherche inversée)",
                    })

    # Deduplicate per agency and save
    found = 0
    for agence in agences:
        findings = matched_agencies.get(agence.id, [])

        # Deduplicate by title
        seen = set()
        unique = []
        for f in findings:
            key = f["title"][:50]
            if key not in seen:
                seen.add(key)
                unique.append(f)

        if agence.offres_emploi_detectees is None:
            agence.offres_emploi_detectees = unique if unique else []

        if unique:
            found += 1
            if log_fn:
                roles = list(set(f["role"] for f in unique))
                log_fn(
                    f"🔥 {agence.nom} recrute ! ({', '.join(roles[:2])})",
                    "fire", count=found,
                )

    db.commit()

    if log_fn:
        log_fn(
            f"Matching terminé : {found} agence(s) recrutent sur {len(agences)} analysées",
            "success" if found > 0 else "info", count=found,
        )

    return found


# ── Direct website scanning ──────────────────────────────────────────────────

CAREER_PATHS = [
    "/recrutement", "/carrieres", "/careers", "/emploi",
    "/nous-rejoindre", "/rejoignez-nous", "/jobs", "/offres-emploi",
    "/recrutement/offres", "/carrieres/offres",
]


def scan_agency_websites(db: Session, errors: list, log_fn=None) -> int:
    """Scan agency websites directly for career pages mentioning target roles.
    Complements the reverse search by catching agencies with their own career portals."""

    agences = (
        db.query(Agence)
        .filter(Agence.site_web.isnot(None), Agence.site_web != "")
        .filter(Agence.offres_emploi_detectees == [])  # Only scan those with no findings yet
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
                # Merge with any existing findings
                existing = agence.offres_emploi_detectees or []
                agence.offres_emploi_detectees = existing + site_findings
                found += 1
                roles = list(set(f["role"] for f in site_findings))
                if log_fn:
                    log_fn(
                        f"🔥 {agence.nom} — {len(site_findings)} offre(s) sur leur site ({', '.join(roles[:2])})",
                        "fire", count=found,
                    )

            if (i + 1) % 10 == 0 and log_fn:
                log_fn(f"Sites scannés : {i+1}/{len(agences)}, {found} avec offres", "search")

    db.commit()

    if log_fn:
        log_fn(
            f"Scan sites terminé : {found} agence(s) avec offres sur leur site",
            "success" if found > 0 else "info", count=found,
        )

    return found


def _scan_one_website(client: httpx.Client, site_web: str, agence_nom: str, errors: list) -> list[dict]:
    """Scan a single agency website for career pages."""
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

            # If we found anything on this page, no need to check other paths
            if findings:
                break

        except Exception:
            continue

    return findings
