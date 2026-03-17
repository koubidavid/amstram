"""Job scraper — finds agencies actively hiring for property management roles."""
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
    "gestionnaire copropriete",
    "gestionnaire copropriété",
    "assistant copropriete",
    "assistant copropriété",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
}


def scan_agency_jobs(db: Session, errors: list, max_agencies: int = 50) -> int:
    """Scan top agencies for active job postings via DuckDuckGo + agency websites.
    Limited to max_agencies to avoid rate limiting."""
    import time

    # Prioritize agencies with SIREN and most lots
    agences = (
        db.query(Agence)
        .filter(Agence.siren.isnot(None))
        .filter(Agence.offres_emploi_detectees.is_(None))  # Only scan un-scanned
        .order_by(Agence.nb_lots_geres.desc().nullslast())
        .limit(max_agencies)
        .all()
    )

    found = 0

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for agence in agences:
            job_findings = []

            # Try agency website first (faster, no rate limit)
            if agence.site_web:
                job_findings = _scan_agency_website(client, agence.site_web, agence.nom, errors)

            # If nothing found on website, try DuckDuckGo
            if not job_findings:
                job_findings = _search_duckduckgo(client, agence.nom, errors)
                time.sleep(1.5)  # Rate limit DuckDuckGo

            # Store findings (even empty list means "scanned, nothing found")
            agence.offres_emploi_detectees = job_findings if job_findings else []
            if job_findings:
                found += 1

    db.commit()
    return found


def _search_duckduckgo(client: httpx.Client, agence_nom: str, errors: list) -> list[dict]:
    """Search DuckDuckGo for job postings by this agency — single query."""
    findings = []

    # Single query instead of 6 separate ones
    query = f'"{agence_nom}" recrutement gestionnaire locatif copropriété assistant'
    try:
        resp = client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers=HEADERS,
            timeout=8.0,
        )
        if resp.status_code != 200:
            return []

        html = resp.text
        results = re.findall(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.+?)</a>',
            html,
        )

        for raw_url, raw_title in results[:5]:
            title = re.sub(r"<[^>]+>", "", raw_title).strip()
            url_match = re.search(r"uddg=([^&]+)", raw_url)
            url = unquote(url_match.group(1)) if url_match else raw_url

            title_lower = title.lower()
            is_job = any(kw in title_lower for kw in [
                "recrutement", "emploi", "offre", "poste", "recrute",
                "cdi", "cdd", "stage", "alternance", "careers",
                "gestionnaire", "assistant", "copropriété", "locatif",
            ])

            agence_in_title = agence_nom.lower().split()[0] in title_lower

            if is_job and agence_in_title:
                # Detect which role
                role = "gestionnaire locatif"
                for r in TARGET_ROLES:
                    if r in title_lower:
                        role = r
                        break

                findings.append({
                    "role": role,
                    "title": title[:150],
                    "url": url[:300],
                    "source": "DuckDuckGo",
                })

    except Exception:
        return []

    # Deduplicate by title
    seen = set()
    unique = []
    for f in findings:
        key = f["title"][:50]
        if key not in seen:
            seen.add(key)
            unique.append(f)

    return unique


def _scan_agency_website(client: httpx.Client, site_web: str, agence_nom: str, errors: list) -> list[dict]:
    """Scan an agency's website for career/recruitment pages."""
    findings = []

    base_url = site_web if site_web.startswith("http") else f"https://{site_web}"

    # Common career page paths
    career_paths = [
        "/recrutement", "/carrieres", "/careers", "/emploi",
        "/nous-rejoindre", "/rejoignez-nous", "/jobs", "/offres-emploi",
    ]

    for path in career_paths:
        try:
            resp = client.get(f"{base_url}{path}", headers=HEADERS)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            text = soup.get_text(separator=" ", strip=True).lower()

            # Check if any target role is mentioned
            for role in TARGET_ROLES:
                if role in text:
                    # Try to extract the specific job listing
                    findings.append({
                        "role": role,
                        "title": f"Offre détectée sur le site : {role}",
                        "url": f"{base_url}{path}",
                        "source": "Site agence",
                    })

        except Exception:
            continue

    return findings
