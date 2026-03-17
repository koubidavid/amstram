"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { Building2, Brain, AlertTriangle, Loader2, Play, RefreshCw, Calculator } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { KpiCard } from "@/components/cards/kpi-card";
import { api } from "@/lib/api";
import type { ScrapingJob } from "@/lib/types";

function NextActionsWidget() {
  const [targets, setTargets] = useState<any[]>([]);

  useEffect(() => {
    // Get top uncontacted targets
    api.getInsights("score_min=50&limit=5").then((d: any) => {
      setTargets(d.items.filter((i: any) => !i.agence_groupe || true).slice(0, 5));
    }).catch(console.error);
  }, []);

  if (targets.length === 0) return <p className="text-sm text-muted-foreground">Aucune cible. Lancez un scraping.</p>;

  return (
    <div className="space-y-2">
      {targets.map((t: any) => (
        <div key={t.id} className="flex items-center justify-between border-b pb-2 last:border-0">
          <div>
            <Link href={`/agences/${t.agence_id}`} className="text-sm font-medium text-primary hover:underline">
              {t.agence_nom?.substring(0, 35)}{t.agence_nom?.length > 35 ? "..." : ""}
            </Link>
            <p className="text-xs text-muted-foreground">{t.agence_ville} — Score: {t.score_besoin}</p>
          </div>
          <Link href={`/agences/${t.agence_id}`}>
            <Button variant="outline" size="sm">Voir</Button>
          </Link>
        </div>
      ))}
      <Link href="/cibles" className="text-sm text-primary hover:underline block text-center mt-2">
        Voir toutes les cibles →
      </Link>
    </div>
  );
}

export default function DashboardPage() {
  const [stats, setStats] = useState({ totalAgences: 0, insightsTotal: 0, insightsHigh: 0, rnicEnriched: 0 });
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [scraping, setScraping] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [loading, setLoading] = useState(true);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const hasRunningJob = jobs.some((j) => j.statut === "running" || j.statut === "pending");

  const loadStats = useCallback(async () => {
    try {
      const [agences, insightsAll, insightsHigh] = await Promise.all([
        api.getAgences("limit=1"),
        api.getInsights("limit=1"),
        api.getInsights("score_min=50&limit=1"),
      ]);
      const agencesData = await api.getAgences("limit=100");
      const rnicCount = agencesData.items.filter((a: { nb_lots_geres: number | null }) => a.nb_lots_geres !== null).length;
      setStats({
        totalAgences: agences.total,
        insightsTotal: insightsAll.total,
        insightsHigh: insightsHigh.total,
        rnicEnriched: rnicCount,
      });
    } catch (e) {
      console.error("Failed to load stats", e);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadJobs = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getScrapingJobs().then((d: any) => setJobs(d.items)).catch(console.error);
  }, []);

  useEffect(() => { loadStats(); loadJobs(); }, [loadStats, loadJobs]);

  useEffect(() => {
    if (hasRunningJob) {
      pollingRef.current = setInterval(() => { loadJobs(); loadStats(); }, 3000);
    } else {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
    }
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [hasRunningJob, loadJobs, loadStats]);

  const handleScrape = async () => {
    setScraping(true);
    try {
      await api.lancerScraping();
      loadJobs();
    } finally {
      setScraping(false);
    }
  };

  const handleCalculateInsights = async () => {
    setCalculating(true);
    try {
      await api.calculateInsights();
      await loadStats();
    } finally {
      setCalculating(false);
    }
  };

  const lastDoneJob = jobs.find((j) => j.statut === "done");

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Amstram</h2>
          <p className="text-muted-foreground">Opportunity Finder — Outil de prospection Monga</p>
        </div>
      </div>

      {/* Action buttons */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-2">
          <CardContent className="flex items-center justify-between pt-6">
            <div>
              <h3 className="font-semibold text-lg">Scrapper internet</h3>
              <p className="text-sm text-muted-foreground">
                Collecte les agences depuis l&apos;API INSEE + enrichit avec le RNIC + calcule les insights
              </p>
              {lastDoneJob && (
                <p className="text-xs text-muted-foreground mt-1">
                  Dernier : {new Date(lastDoneJob.created_at).toLocaleString("fr-FR")} — {lastDoneJob.nb_agences_scrappees} agences
                </p>
              )}
            </div>
            <Button onClick={handleScrape} disabled={scraping || hasRunningJob || calculating} size="lg" className="ml-4 shrink-0">
              {scraping || hasRunningJob ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />En cours...</>
              ) : lastDoneJob ? (
                <><RefreshCw className="mr-2 h-4 w-4" />Relancer</>
              ) : (
                <><Play className="mr-2 h-4 w-4" />Scrapper</>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card className="border-2">
          <CardContent className="flex items-center justify-between pt-6">
            <div>
              <h3 className="font-semibold text-lg">Calculer les insights</h3>
              <p className="text-sm text-muted-foreground">
                Recalcule les scores et recommandations sur les agences déjà collectées
              </p>
              {stats.insightsTotal > 0 && (
                <p className="text-xs text-muted-foreground mt-1">
                  {stats.insightsTotal} insights existants — {stats.insightsHigh} cibles prioritaires
                </p>
              )}
            </div>
            <Button onClick={handleCalculateInsights} disabled={calculating || scraping || hasRunningJob || stats.totalAgences === 0} size="lg" variant="outline" className="ml-4 shrink-0">
              {calculating ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Calcul...</>
              ) : (
                <><Calculator className="mr-2 h-4 w-4" />Calculer</>
              )}
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Progress banner */}
      {hasRunningJob && (
        <Card className="border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950">
          <CardContent className="flex items-center gap-3 pt-6">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            <div>
              <p className="font-medium text-blue-900 dark:text-blue-100">Pipeline en cours</p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                1. Collecte des agences (API INSEE) → 2. Enrichissement RNIC (lots réels) → 3. Calcul des insights
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPIs */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Agences collectées" value={loading ? "..." : stats.totalAgences} icon={Building2} />
        <KpiCard
          title="Enrichies RNIC"
          value={loading ? "..." : stats.rnicEnriched}
          description="Avec nb lots réels vérifié"
          icon={Building2}
        />
        <KpiCard title="Insights calculés" value={loading ? "..." : stats.insightsTotal} icon={Brain} />
        <KpiCard
          title="Cibles prioritaires"
          value={loading ? "..." : stats.insightsHigh}
          description="Score ≥ 50"
          icon={AlertTriangle}
        />
      </div>

      {/* Next actions widget */}
      <Card>
        <CardHeader>
          <CardTitle>Prochaines actions</CardTitle>
          <p className="text-xs text-muted-foreground">Agences à contacter en priorité</p>
        </CardHeader>
        <CardContent>
          <NextActionsWidget />
        </CardContent>
      </Card>

      {/* Recent jobs */}
      {jobs.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Derniers scrappings</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {jobs.slice(0, 5).map((job) => (
                <div key={job.id} className="flex items-center justify-between text-sm border-b pb-2 last:border-0">
                  <div className="flex items-center gap-2">
                    {(job.statut === "running" || job.statut === "pending") && <Loader2 className="h-3 w-3 animate-spin" />}
                    <Badge variant={job.statut === "done" ? "default" : job.statut === "failed" ? "destructive" : "secondary"}>
                      {job.statut === "done" ? "Terminé" : job.statut === "running" ? "En cours" : job.statut === "pending" ? "En attente" : "Erreur"}
                    </Badge>
                  </div>
                  <span className="text-muted-foreground">{new Date(job.created_at).toLocaleString("fr-FR")}</span>
                  <span className="font-medium">{job.nb_agences_scrappees} agences</span>
                  <span className="text-muted-foreground">
                    {job.started_at && job.finished_at
                      ? `${Math.round((new Date(job.finished_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s`
                      : "—"}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
