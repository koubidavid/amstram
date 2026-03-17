"""Job scraper — France Travail + DuckDuckGo reverse search + direct website scan."""
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

FRANCE_TRAVAIL_URL = "https://candidat.francetravail.fr/offres/recherche"

# DuckDuckGo queries as fallback
SEARCH_QUERIES = [
    '"{role}" recrutement immobilier site:indeed.fr OR site:hellowork.com OR site:welcometothejungle.com',
    '"{role}" offre emploi agence immobilière site:linkedin.com OR site:apec.fr OR site:cadremploi.fr',
    '"{role}" site:recrutement.nestenn.com OR site:recrutement.foncia.com OR site:citya-immobilier.com/recrutement',
    '"{role}" site:nexity.fr/emploi OR site:oralia.fr/recrutement OR site:sergic.com/recrutement OR site:laforet.com/recrutement',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}

GENERIC_WORDS = frozenset([
    "sa", "sas", "sarl", "eurl", "sci", "de", "du", "la", "le", "les", "des",
    "et", "en", "immobilier", "immobiliere", "immobiliers", "gestion", "syndic",
    "cabinet", "agence", "groupe", "societe", "administration", "regie",
])


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


def _match_company_to_agencies(company_name: str, name_index: dict, role: str,
                                title: str, url: str, source: str,
                                matched: dict) -> bool:
    """Try to match a company name to agencies in our DB."""
    company_lower = company_name.lower().strip()
    if not company_lower or len(company_lower) < 3:
        return False

    for word in company_lower.split():
        if word in GENERIC_WORDS or len(word) < 3:
            continue
        if word in name_index:
            for agence in name_index[word]:
                if agence.id not in matched:
                    matched[agence.id] = []
                matched[agence.id].append({
                    "role": role,
                    "title": title[:200],
                    "url": url[:300],
                    "source": source,
                    "company_raw": company_name,
                })
            return True
    return False


# ── Source 1: France Travail (best structured data) ──────────────────────────

def _scrape_france_travail(client: httpx.Client, role: str, errors: list, log_fn=None) -> list[dict]:
    """Scrape France Travail search results for a given role. Returns list of {company, title, url, role}."""
    postings = []

    for page_start in [0, 15]:  # 2 pages of 15 results
        try:
            resp = client.get(
                FRANCE_TRAVAIL_URL,
                params={"motsCles": role, "offresPartenaires": "true", "range": f"{page_start}-{page_start+14}"},
                headers=HEADERS,
                timeout=12.0,
            )
            if resp.status_code != 200:
                continue

            html = resp.text

            # Parse job listings: each <li data-id-offre="..."> is a result
            results = re.findall(r'<li[^>]*data-id-offre="([^"]+)"(.*?)</li>', html, re.S)

            for offre_id, block in results:
                # Title
                title_match = re.search(r'<h2[^>]*>(.*?)</h2>', block, re.S)
                title = re.sub(r'<[^>]+>', '', title_match.group(1)).strip() if title_match else ""

                # Company — in the subtext area
                # France Travail puts company name in a specific location in each card
                company = ""
                # Try: text after location, typically "VILLE - COMPANY" or just "COMPANY"
                subtext = re.search(r'class="[^"]*subtext[^"]*"[^>]*>(.*?)<', block, re.S)
                if subtext:
                    company = re.sub(r'<[^>]+>', '', subtext.group(1)).strip()

                # Also try: any standalone text that looks like a company name
                if not company:
                    spans = re.findall(r'<span[^>]*>([^<]{3,50})</span>', block)
                    for s in spans:
                        s = s.strip()
                        if s and not any(kw in s.lower() for kw in ["publi", "cdd", "cdi", "jour", "mois", "€", "h/"]):
                            company = s
                            break

                # Description snippet for matching
                desc = re.search(r'class="description"[^>]*>(.*?)<', block, re.S)
                desc_text = re.sub(r'<[^>]+>', '', desc.group(1)).strip()[:200] if desc else ""

                url = f"https://candidat.francetravail.fr/offres/recherche/detail/{offre_id}"

                postings.append({
                    "company": company,
                    "title": title,
                    "url": url,
                    "role": role,
                    "desc": desc_text,
                })

        except Exception as e:
            errors.append(f"France Travail '{role}' p{page_start}: {str(e)[:80]}")

    return postings


# ── Source 2: DuckDuckGo reverse search ──────────────────────────────────────

def _search_duckduckgo_reverse(client: httpx.Client, role: str, errors: list) -> list[dict]:
    """Search DuckDuckGo for job postings for a given role."""
    import time
    postings = []

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

                postings.append({
                    "company": "",  # Will try to extract from title
                    "title": title,
                    "url": url,
                    "role": role,
                    "desc": "",
                })

            time.sleep(1.5)

        except Exception as e:
            errors.append(f"DuckDuckGo '{role}': {str(e)[:80]}")

    return postings


# ── Main function ────────────────────────────────────────────────────────────

def scan_jobs_reverse(db: Session, errors: list, log_fn=None) -> int:
    """Reverse job search: France Travail + DuckDuckGo, then match to agencies."""
    import time

    agences = db.query(Agence).filter(Agence.siren.isnot(None)).all()
    if not agences:
        return 0

    name_index = _build_name_index(agences)

    if log_fn:
        log_fn(f"Index de {len(agences)} agences. Recherche sur France Travail + DuckDuckGo...", "search")

    all_postings: list[dict] = []
    matched_agencies: dict[int, list[dict]] = {}

    with httpx.Client(timeout=12.0, follow_redirects=True) as client:
        for role in TARGET_ROLES:
            # France Travail (primary — best data)
            ft_postings = _scrape_france_travail(client, role, errors, log_fn)
            all_postings.extend(ft_postings)

            if log_fn:
                log_fn(f"France Travail « {role} » — {len(ft_postings)} offres", "search", count=len(ft_postings))

            time.sleep(1)

            # DuckDuckGo (secondary — broader but less structured)
            ddg_postings = _search_duckduckgo_reverse(client, role, errors)
            all_postings.extend(ddg_postings)

            if log_fn:
                log_fn(f"DuckDuckGo « {role} » — {len(ddg_postings)} résultats", "search", count=len(ddg_postings))

    if log_fn:
        log_fn(f"{len(all_postings)} offres collectées. Matching avec les agences...", "database")

    # Match postings to agencies
    for posting in all_postings:
        company = posting.get("company", "")
        title = posting.get("title", "")

        # Try matching company name first
        if company:
            _match_company_to_agencies(
                company, name_index, posting["role"],
                posting["title"], posting["url"], "France Travail",
                matched_agencies,
            )

        # Also try matching words from the title (for DuckDuckGo results)
        title_lower = title.lower()
        is_job = any(kw in title_lower for kw in [
            "recrutement", "emploi", "offre", "poste", "recrute",
            "cdi", "cdd", "gestionnaire", "assistant", "copropriété", "locatif",
            "h/f", "f/h",
        ])
        if is_job:
            for word in title_lower.split():
                if word in GENERIC_WORDS or len(word) < 4:
                    continue
                if word in name_index:
                    for agence in name_index[word]:
                        if agence.id not in matched_agencies:
                            matched_agencies[agence.id] = []
                        matched_agencies[agence.id].append({
                            "role": posting["role"],
                            "title": title[:200],
                            "url": posting["url"],
                            "source": "DuckDuckGo",
                        })

    # Save results
    found = 0
    for agence in agences:
        findings = matched_agencies.get(agence.id, [])

        # Deduplicate
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
                    f"🔥 {agence.nom} — {len(unique)} offre(s) ({', '.join(roles[:2])})",
                    "fire", count=found,
                )

    db.commit()

    if log_fn:
        log_fn(
            f"Résultat : {found} agence(s) recrutent sur {len(agences)} en base",
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
    """Scan agency websites directly for career pages mentioning target roles."""

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
                    log_fn(
                        f"🔥 {agence.nom} — offre(s) sur leur site ({', '.join(roles[:2])})",
                        "fire", count=found,
                    )

            if (i + 1) % 10 == 0 and log_fn:
                log_fn(f"Sites scannés : {i+1}/{len(agences)}, {found} avec offres", "search")

    db.commit()

    if log_fn:
        log_fn(
            f"Scan sites terminé : {found} agence(s) avec offres",
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

            if findings:
                break

        except Exception:
            continue

    return findings
