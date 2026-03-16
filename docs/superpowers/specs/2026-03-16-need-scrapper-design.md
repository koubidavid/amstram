# Need Scrapper — Spec de Design

## Objectif

Outil de scrapping et d'analyse prédictive ciblant les agences immobilières françaises (gestion locative & copropriété). Deux volets :

1. **Scrapping** — Collecter les offres d'emploi publiées sur les sites d'agences + les données caractéristiques de chaque agence
2. **Insights prédictifs** — Identifier les agences ayant potentiellement besoin d'une aide humaine et logistique pour la gestion de travaux (recherche artisan, suivi devis/factures), même sans offre d'emploi active

## Périmètre

- **Géographie** : Toute la France
- **Types de postes recherchés** : Gestionnaire locatif, assistant de gestion locative, gestionnaire de copropriété, assistant de copropriété
- **Sources scrappées** : Sites d'agences (pages carrières), annuaires (PagesJaunes, FNAIM, UNIS), Google Reviews, Trustpilot
- **Authentification** : Pas d'auth pour le MVP — outil interne, usage mono-utilisateur
- **Déploiement** : Local via Docker Compose pour le MVP. Migration cloud possible ultérieurement.

---

## Stack technique

| Couche | Technologie |
|---|---|
| Scrapping | Python — Scrapy + Playwright + BeautifulSoup |
| Backend API | Python — FastAPI |
| Base de données | PostgreSQL |
| Cache & file de tâches | Redis |
| Task queue & scheduler | Celery + Celery Beat |
| Frontend | Next.js + Tailwind CSS + shadcn/ui |
| Graphiques | Recharts |
| Export | CSV / Excel (openpyxl) |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND                          │
│         Next.js + Tailwind + shadcn/ui              │
│  Dashboard / Filtres / Export / Insights / Scheduler │
└──────────────────────┬──────────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────────┐
│                   BACKEND API                        │
│                    FastAPI                            │
│  Endpoints: agences, offres, avis, insights, jobs   │
└───────┬──────────────────────────────┬──────────────┘
        │                              │
┌───────▼────────┐           ┌─────────▼────────────┐
│  PostgreSQL    │           │   Redis               │
│  - agences     │           │   - cache             │
│  - offres      │           │   - file de tâches    │
│  - avis        │           │   - résultats Celery  │
│  - insights    │           └─────────┬────────────┘
│  - agence_hist │                     │
│  - scraping_jobs│           ┌────────▼───────────┐
└────────────────┘           │  Celery Workers     │
                              │  + Celery Beat      │
                              │  (scheduler cron)   │
                              └────────┬───────────┘
                                       │
                    ┌──────────────────▼───────────────────┐
                    │         SCRAPPING ENGINE              │
                    │  Scrapy + Playwright + BeautifulSoup  │
                    │                                       │
                    │  + Proxy rotation (liste configurable)│
                    └──────────────────────────────────────┘
```

3 couches distinctes :
1. **Scrapping Engine** — collecte les données brutes, piloté par Celery (manuel ou Celery Beat pour les crons)
2. **Backend API** — expose les données, calcule les insights, gère les jobs de scrapping
3. **Frontend Dashboard** — consultation, filtres, export, configuration des automatisations

---

## Modèle de données

### Agence

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant unique |
| nom | string | Nom de l'agence |
| groupe | string | Groupe parent (Foncia, Nexity, Citya...) |
| adresse | string | Adresse complète |
| ville | string | Ville |
| region | string | Région |
| code_postal | string | Code postal |
| site_web | string | URL du site |
| nb_lots_geres | integer | Nombre de lots gérés (estimé) — valeur courante |
| nb_collaborateurs | integer | Nombre de collaborateurs |
| a_service_travaux | boolean | Service travaux dédié détecté |
| note_google | float | Note Google (0-5) |
| nb_avis_google | integer | Nombre d'avis Google |
| note_trustpilot | float | Note Trustpilot (0-5) |
| nb_avis_trustpilot | integer | Nombre d'avis Trustpilot |
| derniere_maj | datetime | Date du dernier scrapping |
| created_at | datetime | Date de création |
| updated_at | datetime | Date de mise à jour |

### AgenceSnapshot (historique)

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant unique |
| agence_id | UUID (FK) | Agence liée |
| nb_lots_geres | integer | Nombre de lots au moment du snapshot |
| nb_collaborateurs | integer | Nombre de collaborateurs au moment du snapshot |
| a_service_travaux | boolean | Service travaux détecté au moment du snapshot |
| note_google | float | Note Google au moment du snapshot |
| note_trustpilot | float | Note Trustpilot au moment du snapshot |
| scraping_job_id | UUID (FK) | Job de scrapping ayant produit ce snapshot |
| created_at | datetime | Date du snapshot |

> Un snapshot est créé à chaque scrapping. Permet de calculer la croissance du parc et l'évolution de tous les indicateurs.

### OffreEmploi

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant unique |
| agence_id | UUID (FK) | Agence liée |
| titre | string | Titre du poste |
| description | text | Description complète |
| type_poste | enum | gestionnaire_locatif, assistant_gestion_locative, gestionnaire_copropriete, assistant_copropriete, autre |
| url_source | string | URL de l'offre |
| date_publication | date | Date de publication |
| date_scrappee | datetime | Date de collecte |
| active | boolean | Offre encore active |
| created_at | datetime | Date de création |
| updated_at | datetime | Date de mise à jour |

> Les offres inactives sont conservées indéfiniment (nécessaire pour le calcul du turnover sur 12 mois). Archivage optionnel au-delà de 24 mois.

### Avis

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant unique |
| agence_id | UUID (FK) | Agence liée |
| source | enum | google, trustpilot |
| note | float | Note de l'avis |
| texte | text | Contenu de l'avis |
| mentionne_travaux | boolean | Mentionne des problèmes liés aux travaux |
| mentionne_reactivite | boolean | Mentionne des problèmes de réactivité |
| date_avis | date | Date de l'avis |
| created_at | datetime | Date de collecte |

### Insight

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant unique |
| agence_id | UUID (FK) | Agence liée |
| score_besoin | integer | Score composite 0-100 |
| signaux | JSON | Détail de chaque signal détecté |
| ratio_lots_collab | float | Ratio lots/collaborateurs |
| turnover_score | float | Score de turnover |
| avis_negatifs_travaux | integer | Nb avis négatifs mentionnant travaux |
| croissance_parc | float | % de croissance du parc |
| has_service_travaux | boolean | Service travaux détecté |
| recommandation | text | Recommandation générée |
| created_at | datetime | Date de calcul |
| updated_at | datetime | Date de mise à jour |

### ScrapingJob

| Champ | Type | Description |
|---|---|---|
| id | UUID | Identifiant unique |
| type | enum | manuel, cron |
| cron_expression | string | Expression cron (si automatisé) |
| statut | enum | pending, running, done, failed |
| created_at | datetime | Date de création du job |
| started_at | datetime (nullable) | Début d'exécution |
| finished_at | datetime (nullable) | Fin d'exécution |
| nb_agences_scrappees | integer | Nombre d'agences traitées |
| erreurs | JSON | Détail des erreurs rencontrées |

---

## Scrapping Engine

### 4 Spiders spécialisés

| Spider | Sources | Données collectées |
|---|---|---|
| AgenceInfoSpider | Sites web des agences, pages "à propos", annuaires (PagesJaunes, FNAIM, UNIS) | Nom, adresse, parc géré, nb collaborateurs, service travaux |
| OffreEmploiSpider | Pages carrières/recrutement des sites d'agences | Offres d'emploi, type de poste, description |
| GoogleReviewsSpider | Google Maps / Google Business | Note, nb avis, texte des avis négatifs |
| TrustpilotSpider | Trustpilot | Note, nb avis, texte des avis pertinents |

### Stratégie

- **Playwright** pour les sites avec rendu JS (SPA des agences, Google Maps)
- **Scrapy + BeautifulSoup** pour les sites statiques (annuaires, Trustpilot)
- **Rate limiting** intelligent : délai aléatoire entre requêtes (2-5s), rotation de User-Agent, respect des robots.txt
- **Proxy rotation** : liste de proxies configurable dans `config/proxies.yaml`. Rotation automatique par le middleware Scrapy. Indispensable pour le scrapping à grande échelle (Google Maps, milliers de sites agences).
- **Sélecteurs configurables** : chaque spider utilise des sélecteurs CSS/XPath stockés en config YAML — adaptation sans modifier le code
- **Pipeline de nettoyage** : normalisation des noms d'agences, dédoublonnage, validation des données avant insertion en base
- **Snapshots** : à chaque scrapping, un AgenceSnapshot est créé pour chaque agence mise à jour

### Gestion des erreurs

- Retry automatique (3 tentatives avec backoff exponentiel)
- Log des pages échouées dans ScrapingJob.erreurs
- Alertes si un spider échoue complètement (notification dashboard)

### Scheduling (Celery Beat)

- Les automatisations créées via l'API (`POST /api/scraping/cron`) sont persistées en base (ScrapingJob avec cron_expression)
- **Celery Beat** lit les schedules depuis la base (via `django-celery-beat` adapter ou schedule custom) et déclenche les tâches Celery correspondantes
- Le dashboard permet de créer, modifier et supprimer les crons visuellement

---

## Moteur d'Insights

### Score de besoin (0-100) — 5 signaux pondérés

| Signal | Poids | Calcul |
|---|---|---|
| Ratio lots/collaborateurs | 30 pts | Comparaison à la médiane du secteur. >médiane+50% = 30pts, >médiane+25% = 20pts, etc. |
| Avis négatifs travaux/réactivité | 25 pts | % d'avis mentionnant mots-clés travaux parmi avis < 3 étoiles |
| Turnover visible | 20 pts | Nb d'offres (actives + inactives) publiées pour postes similaires sur 12 derniers mois. >3 offres = 20pts |
| Croissance du parc | 15 pts | Variation du nb_lots_geres entre le dernier AgenceSnapshot et le précédent. Croissance >10% = 15pts |
| Absence service travaux | 10 pts | Binaire : pas de service travaux détecté = 10pts |

### Dictionnaire de mots-clés (configurable)

```
travaux, artisan, plombier, électricien, devis, facture,
intervention, réparation, suivi, relance, réactivité,
dégât des eaux, sinistre, maintenance, entretien
```

### Recommandations automatiques

- Score > 75 : "Forte probabilité de besoin — agence sous-dimensionnée avec signaux multiples"
- Score 50-75 : "Besoin probable — plusieurs indices convergents"
- Score 25-50 : "À surveiller — quelques signaux détectés"
- Score < 25 : "Pas de besoin identifié actuellement"

### Historisation

Chaque calcul d'insight est horodaté, permettant de visualiser l'évolution du score (tendance montante = signal renforcé).

---

## API REST (FastAPI)

Toutes les routes de liste supportent la **pagination** : `?page=1&limit=20` (défaut: page=1, limit=20, max limit=100).

| Méthode | Route | Description |
|---|---|---|
| GET | /api/agences | Liste agences (filtres: ville, région, score, taille) |
| GET | /api/agences/{id} | Détail agence + historique insights |
| GET | /api/agences/{id}/avis | Avis d'une agence (filtres: source, note_max) |
| GET | /api/agences/{id}/offres | Offres d'une agence |
| GET | /api/agences/{id}/snapshots | Historique des snapshots |
| GET | /api/agences/{id}/insights/historique | Évolution du score dans le temps |
| GET | /api/offres | Liste offres (filtres: type_poste, région, date) |
| GET | /api/insights | Classement agences par score_besoin |
| POST | /api/scraping/lancer | Lancer un scrapping manuel |
| GET | /api/scraping/jobs | Historique des exécutions |
| POST | /api/scraping/cron | Créer/modifier une automatisation |
| DELETE | /api/scraping/cron/{id} | Supprimer une automatisation |
| GET | /api/export/agences/{format} | Export agences en CSV ou Excel |
| GET | /api/export/offres/{format} | Export offres en CSV ou Excel |
| GET | /api/export/insights/{format} | Export insights en CSV ou Excel |

Auto-documentation Swagger sur /docs.

---

## Dashboard (Next.js)

### 5 pages principales

1. **Vue d'ensemble** — KPIs (nb agences scrappées, nb offres actives, nb insights score > 50), graphiques de tendance
2. **Agences** — Table triable/filtrable, clic pour fiche détaillée (avec onglets: infos, avis, offres, snapshots, insights)
3. **Offres d'emploi** — Liste avec filtres par type de poste, région, date, agence
4. **Insights** — Classement par score_besoin, cartes avec jauges visuelles, détail des signaux
5. **Scraping** — Lancement manuel, configuration crons, historique et erreurs

### Composants UI (shadcn/ui)

- Data tables avec pagination, tri, recherche
- Cartes KPI avec sparklines
- Jauges de score colorées (vert → rouge)
- Graphiques d'évolution (Recharts)
- Filtres combinables en sidebar
- Bouton export CSV/Excel contextuel
- Toast notifications pour le statut des jobs

---

## Structure du projet

```
need-scrapper/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── api/
│   │   │   ├── agences.py
│   │   │   ├── offres.py
│   │   │   ├── avis.py
│   │   │   ├── insights.py
│   │   │   ├── scraping.py
│   │   │   └── export.py
│   │   ├── models/
│   │   │   ├── agence.py
│   │   │   ├── agence_snapshot.py
│   │   │   ├── offre.py
│   │   │   ├── avis.py
│   │   │   ├── insight.py
│   │   │   └── scraping_job.py
│   │   ├── services/
│   │   │   ├── insight_calculator.py
│   │   │   └── export_service.py
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── migrations/
│   │   └── config.py
│   ├── requirements.txt
│   └── Dockerfile
├── scrapper/
│   ├── scrapper/
│   │   ├── spiders/
│   │   │   ├── agence_info.py
│   │   │   ├── offre_emploi.py
│   │   │   ├── google_reviews.py
│   │   │   └── trustpilot.py
│   │   ├── pipelines/
│   │   │   ├── cleaning.py
│   │   │   ├── snapshot.py
│   │   │   └── database.py
│   │   ├── config/
│   │   │   ├── selectors.yaml
│   │   │   └── proxies.yaml
│   │   └── settings.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   ├── celery_tasks.py
│   │   └── beat_schedule.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # Vue d'ensemble
│   │   │   ├── agences/
│   │   │   ├── offres/
│   │   │   ├── insights/
│   │   │   └── scraping/
│   │   ├── components/
│   │   │   ├── ui/               # shadcn/ui
│   │   │   ├── charts/
│   │   │   ├── tables/
│   │   │   └── layout/
│   │   └── lib/
│   │       ├── api.ts
│   │       └── types.ts
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```
