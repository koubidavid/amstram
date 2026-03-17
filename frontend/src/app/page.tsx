"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { Building2, Brain, AlertTriangle, Loader2, Play, RefreshCw, Calculator, Square } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { KpiCard } from "@/components/cards/kpi-card";
import { api } from "@/lib/api";
import type { ScrapingJob } from "@/lib/types";

function NextActionsWidget() {
  const [targets, setTargets] = useState<any[]>([]);

  useEffect(() => {
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

function AnimatedNumber({ value, loading }: { value: number; loading: boolean }) {
  const [display, setDisplay] = useState(0);
  const prev = useRef(0);

  useEffect(() => {
    if (loading) return;
    const from = prev.current;
    const to = value;
    if (from === to) { setDisplay(to); return; }
    const duration = 800;
    const start = performance.now();
    const animate = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setDisplay(Math.round(from + (to - from) * eased));
      if (progress < 1) requestAnimationFrame(animate);
      else prev.current = to;
    };
    requestAnimationFrame(animate);
  }, [value, loading]);

  return <>{loading ? "..." : display}</>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState({ totalAgences: 0, insightsTotal: 0, insightsHigh: 0, rnicEnriched: 0 });
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [scraping, setScraping] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [loading, setLoading] = useState(true);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const hasRunningJob = jobs.some((j) => j.statut === "running" || j.statut === "pending");
  const runningJob = jobs.find((j) => j.statut === "running" || j.statut === "pending");
  const prog = runningJob?.progression;

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

  const handleStop = async () => {
    if (!runningJob) return;
    try {
      await api.stopScraping(runningJob.id);
      loadJobs();
    } catch (e) {
      console.error("Failed to stop", e);
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
  const steps = [
    "Collecte agences",
    "RNIC",
    "Pappers",
    "Offres d'emploi",
    "Scores",
  ];

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
            <div className="flex items-center gap-2 ml-4 shrink-0">
              {hasRunningJob && (
                <Button onClick={handleStop} variant="destructive" size="lg">
                  <Square className="mr-2 h-4 w-4" />Stop
                </Button>
              )}
              <Button onClick={handleScrape} disabled={scraping || hasRunningJob || calculating} size="lg">
                {scraping || hasRunningJob ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" />En cours...</>
                ) : lastDoneJob ? (
                  <><RefreshCw className="mr-2 h-4 w-4" />Relancer</>
                ) : (
                  <><Play className="mr-2 h-4 w-4" />Scrapper</>
                )}
              </Button>
            </div>
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

      {/* Pipeline progress */}
      {hasRunningJob && (
        <Card className="border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 dark:border-blue-900 overflow-hidden">
          <CardContent className="pt-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                  <div className="absolute inset-0 h-6 w-6 animate-ping opacity-20 rounded-full bg-blue-600" />
                </div>
                <div>
                  <p className="font-semibold text-blue-900 dark:text-blue-100">
                    {prog?.step_label || "Démarrage du pipeline..."}
                  </p>
                  {prog?.detail && (
                    <p className="text-sm text-blue-600 dark:text-blue-300">{prog.detail}</p>
                  )}
                </div>
              </div>
              {prog?.eta_display && (
                <Badge variant="outline" className="text-blue-700 border-blue-300 bg-white/50 dark:bg-blue-900/50 font-mono text-sm px-3 py-1">
                  {prog.eta_display} restant
                </Badge>
              )}
            </div>

            {/* Progress bar */}
            <div className="w-full bg-blue-200/60 rounded-full h-3 dark:bg-blue-800/60 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full transition-all duration-1000 ease-out relative"
                style={{ width: `${prog?.percent || 2}%` }}
              >
                <div className="absolute inset-0 bg-white/20 animate-pulse" />
              </div>
            </div>

            {/* Step indicators */}
            <div className="flex justify-between">
              {steps.map((label, i) => {
                const stepNum = prog?.step || 0;
                const isDone = i < stepNum - 1;
                const isCurrent = i === stepNum - 1;
                return (
                  <div key={i} className={`flex flex-col items-center gap-1 transition-all duration-500 ${
                    isDone ? "text-green-600 dark:text-green-400" :
                    isCurrent ? "text-blue-700 dark:text-blue-300 scale-110" : "text-blue-300 dark:text-blue-700"
                  }`}>
                    <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold transition-all duration-500 ${
                      isDone ? "bg-green-500 text-white shadow-md shadow-green-500/30" :
                      isCurrent ? "bg-blue-600 text-white shadow-lg shadow-blue-500/40 ring-2 ring-blue-300" :
                      "bg-blue-200/80 dark:bg-blue-800/80"
                    }`}>
                      {isDone ? "✓" : i + 1}
                    </span>
                    <span className="text-[10px] md:text-xs font-medium hidden sm:block">{label}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPIs with animated numbers */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="transition-all duration-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Agences collectées</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold"><AnimatedNumber value={stats.totalAgences} loading={loading} /></div>
          </CardContent>
        </Card>
        <Card className="transition-all duration-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Enrichies RNIC</CardTitle>
            <Building2 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold"><AnimatedNumber value={stats.rnicEnriched} loading={loading} /></div>
            <p className="text-xs text-muted-foreground">Avec nb lots réels vérifié</p>
          </CardContent>
        </Card>
        <Card className="transition-all duration-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Insights calculés</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold"><AnimatedNumber value={stats.insightsTotal} loading={loading} /></div>
          </CardContent>
        </Card>
        <Card className="transition-all duration-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Cibles prioritaires</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold"><AnimatedNumber value={stats.insightsHigh} loading={loading} /></div>
            <p className="text-xs text-muted-foreground">Score &ge; 50</p>
          </CardContent>
        </Card>
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
                    {job.progression?.step_label && job.statut !== "done" && (
                      <span className="text-xs text-muted-foreground">{job.progression.step_label}</span>
                    )}
                  </div>
                  <span className="text-muted-foreground">{new Date(job.created_at).toLocaleString("fr-FR")}</span>
                  <span className="font-medium">{job.nb_agences_scrappees} agences</span>
                  <span className="text-muted-foreground">
                    {job.started_at && job.finished_at
                      ? `${Math.round((new Date(job.finished_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s`
                      : job.progression?.eta_display || "—"}
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
