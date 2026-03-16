/* eslint-disable @typescript-eslint/no-explicit-any */
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  getAgences: (params?: string) => fetchApi<any>(`/api/agences?${params || ""}`),
  getAgence: (id: string) => fetchApi<any>(`/api/agences/${id}`),
  getAgenceAvis: (id: string, params?: string) => fetchApi<any>(`/api/agences/${id}/avis?${params || ""}`),
  getAgenceOffres: (id: string) => fetchApi<any>(`/api/agences/${id}/offres`),
  getAgenceInsightsHistorique: (id: string) => fetchApi<any[]>(`/api/agences/${id}/insights/historique`),
  getAgenceSnapshots: (id: string) => fetchApi<any>(`/api/agences/${id}/snapshots`),
  getOffres: (params?: string) => fetchApi<any>(`/api/offres?${params || ""}`),
  getInsights: (params?: string) => fetchApi<any>(`/api/insights?${params || ""}`),
  lancerScraping: () => fetchApi<any>("/api/scraping/lancer", { method: "POST" }),
  getScrapingJobs: () => fetchApi<any>("/api/scraping/jobs"),
  createCron: (cron: string) => fetchApi<any>("/api/scraping/cron", { method: "POST", body: JSON.stringify({ cron_expression: cron }) }),
  deleteCron: (id: string) => fetchApi<void>(`/api/scraping/cron/${id}`, { method: "DELETE" }),
  exportUrl: (entity: string, format: string) => `${API_BASE}/api/export/${entity}/${format}`,
};
