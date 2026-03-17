"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Play, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import type { ScrapingJob } from "@/lib/types";

export default function ScrapingPage() {
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [launching, setLaunching] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const hasRunningJob = jobs.some((j) => j.statut === "running" || j.statut === "pending");

  const loadJobs = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getScrapingJobs().then((d: any) => setJobs(d.items)).catch(console.error);
  }, []);

  useEffect(() => { loadJobs(); }, [loadJobs]);

  useEffect(() => {
    if (hasRunningJob) {
      pollingRef.current = setInterval(loadJobs, 3000);
    } else {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
    }
    return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
  }, [hasRunningJob, loadJobs]);

  const handleLaunch = async () => {
    setLaunching(true);
    try {
      await api.lancerScraping();
      loadJobs();
    } finally {
      setLaunching(false);
    }
  };

  const getStatusBadge = (statut: string) => {
    const config: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      done: { variant: "default", label: "Terminé" },
      running: { variant: "secondary", label: "En cours..." },
      pending: { variant: "outline", label: "En attente" },
      failed: { variant: "destructive", label: "Erreur" },
    };
    const c = config[statut] || { variant: "outline" as const, label: statut };
    return <Badge variant={c.variant}>{c.label}</Badge>;
  };

  const lastJob = jobs.length > 0 ? jobs[0] : null;
  const lastDoneJob = jobs.find((j) => j.statut === "done");

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scraping</h2>
          <p className="text-muted-foreground">
            {hasRunningJob
              ? "Scraping en cours — collecte des agences, enrichissement RNIC, calcul des insights..."
              : lastDoneJob
                ? `Dernier scraping : ${new Date(lastDoneJob.created_at).toLocaleString("fr-FR")} — ${lastDoneJob.nb_agences_scrappees} agences`
                : "Lancez un scraping pour collecter les données"}
          </p>
        </div>
        <Button onClick={handleLaunch} disabled={launching || hasRunningJob} size="lg">
          {launching || hasRunningJob ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Scraping en cours...</>
          ) : lastDoneJob ? (
            <><RefreshCw className="mr-2 h-4 w-4" />Relancer le scraping</>
          ) : (
            <><Play className="mr-2 h-4 w-4" />Lancer le scraping</>
          )}
        </Button>
      </div>

      {hasRunningJob && (() => {
        const runningJob = jobs.find((j) => j.statut === "running" || j.statut === "pending");
        const prog = runningJob?.progression;
        const steps = [
          "Collecte agences (API INSEE)",
          "Enrichissement RNIC (lots)",
          "Enrichissement Pappers (CA, dirigeants)",
          "Détection offres d'emploi",
          "Calcul des scores",
        ];
        return (
          <Card className="border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950">
            <CardContent className="pt-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
                  <div>
                    <p className="font-medium text-blue-900 dark:text-blue-100">
                      {prog?.step_label || "Démarrage du pipeline..."}
                    </p>
                    {prog?.detail && (
                      <p className="text-sm text-blue-700 dark:text-blue-300">{prog.detail}</p>
                    )}
                  </div>
                </div>
                {prog?.eta_display && (
                  <Badge variant="outline" className="text-blue-700 border-blue-300">
                    {prog.eta_display} restant
                  </Badge>
                )}
              </div>

              {/* Progress bar */}
              <div className="w-full bg-blue-200 rounded-full h-2.5 dark:bg-blue-800">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                  style={{ width: `${prog?.percent || 2}%` }}
                />
              </div>

              {/* Step indicators */}
              <div className="flex justify-between text-xs text-blue-600 dark:text-blue-400">
                {steps.map((label, i) => (
                  <div key={i} className={`flex items-center gap-1 ${
                    prog && i < (prog.step || 1) - 1 ? "text-green-600 dark:text-green-400" :
                    prog && i === (prog.step || 1) - 1 ? "font-bold" : "opacity-50"
                  }`}>
                    <span className={`inline-block w-4 h-4 rounded-full text-center leading-4 text-[10px] ${
                      prog && i < (prog.step || 1) - 1 ? "bg-green-500 text-white" :
                      prog && i === (prog.step || 1) - 1 ? "bg-blue-600 text-white" : "bg-blue-200 dark:bg-blue-700"
                    }`}>
                      {prog && i < (prog.step || 1) - 1 ? "✓" : i + 1}
                    </span>
                    <span className="hidden md:inline">{label}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        );
      })()}

      {/* Stats from last completed job */}
      {lastDoneJob && !hasRunningJob && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Agences collectées</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">{lastDoneJob.nb_agences_scrappees}</div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Durée</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold">
              {lastDoneJob.started_at && lastDoneJob.finished_at
                ? `${Math.round((new Date(lastDoneJob.finished_at).getTime() - new Date(lastDoneJob.started_at).getTime()) / 1000)}s`
                : "—"}
            </div></CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm">Statut</CardTitle></CardHeader>
            <CardContent><div className="text-2xl font-bold text-green-600">Complet</div></CardContent>
          </Card>
        </div>
      )}

      <Card>
        <CardHeader><CardTitle>Historique</CardTitle></CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-3 text-left text-sm font-medium">Statut</th>
                  <th className="p-3 text-left text-sm font-medium">Date</th>
                  <th className="p-3 text-right text-sm font-medium">Agences</th>
                  <th className="p-3 text-right text-sm font-medium">Durée</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="border-b">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        {(job.statut === "running" || job.statut === "pending") && <Loader2 className="h-3 w-3 animate-spin" />}
                        {getStatusBadge(job.statut)}
                      </div>
                    </td>
                    <td className="p-3 text-sm">{new Date(job.created_at).toLocaleString("fr-FR")}</td>
                    <td className="p-3 text-right text-sm">{job.nb_agences_scrappees}</td>
                    <td className="p-3 text-right text-sm">
                      {job.started_at && job.finished_at
                        ? `${Math.round((new Date(job.finished_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s`
                        : "—"}
                    </td>
                  </tr>
                ))}
                {jobs.length === 0 && (
                  <tr><td colSpan={4} className="p-6 text-center text-muted-foreground">Aucun scraping effectué</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
