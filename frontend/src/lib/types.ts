export interface Agence {
  id: string;
  nom: string;
  groupe: string | null;
  adresse: string | null;
  ville: string | null;
  region: string | null;
  code_postal: string | null;
  site_web: string | null;
  nb_lots_geres: number | null;
  nb_collaborateurs: number | null;
  a_service_travaux: boolean;
  note_google: number | null;
  nb_avis_google: number | null;
  note_trustpilot: number | null;
  nb_avis_trustpilot: number | null;
  derniere_maj: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface OffreEmploi {
  id: string;
  agence_id: string;
  titre: string;
  description: string | null;
  type_poste: string;
  url_source: string | null;
  date_publication: string | null;
  date_scrappee: string;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AvisRead {
  id: string;
  agence_id: string;
  source: "google" | "trustpilot";
  note: number;
  texte: string | null;
  mentionne_travaux: boolean;
  mentionne_reactivite: boolean;
  date_avis: string | null;
  created_at: string;
}

export interface InsightRead {
  id: string;
  agence_id: string;
  score_besoin: number;
  signaux: Record<string, number> | null;
  ratio_lots_collab: number | null;
  turnover_score: number | null;
  avis_negatifs_travaux: number | null;
  croissance_parc: number | null;
  has_service_travaux: boolean;
  recommandation: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScrapingJob {
  id: string;
  type: "manuel" | "cron";
  cron_expression: string | null;
  statut: "pending" | "running" | "done" | "failed";
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  nb_agences_scrappees: number;
  progression: {
    step: number;
    total_steps: number;
    step_key: string;
    step_label: string;
    detail: string;
    percent: number;
    eta_minutes: number;
    eta_display: string;
  } | null;
  erreurs: Record<string, string> | null;
}
