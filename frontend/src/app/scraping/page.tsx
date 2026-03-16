"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Loader2, Square, Play } from "lucide-react";
import { api } from "@/lib/api";
import type { ScrapingJob } from "@/lib/types";

export default function ScrapingPage() {
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [cronExpression, setCronExpression] = useState("0 2 * * *");
  const [launching, setLaunching] = useState(false);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);

  const hasRunningJob = jobs.some((j) => j.statut === "running" || j.statut === "pending");

  const loadJobs = useCallback(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getScrapingJobs().then((d: any) => setJobs(d.items)).catch(console.error);
  }, []);

  // Poll every 3s when a job is running
  useEffect(() => {
    loadJobs();
  }, [loadJobs]);

  useEffect(() => {
    if (hasRunningJob) {
      pollingRef.current = setInterval(loadJobs, 3000);
    } else if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
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

  const handleStop = async (jobId: string) => {
    await api.stopScraping(jobId);
    loadJobs();
  };

  const handleStopAll = async () => {
    const running = jobs.filter((j) => j.statut === "running" || j.statut === "pending");
    await Promise.all(running.map((j) => api.stopScraping(j.id)));
    loadJobs();
  };

  const handleCreateCron = async () => {
    await api.createCron(cronExpression);
    loadJobs();
  };

  const handleDeleteCron = async (id: string) => {
    await api.deleteCron(id);
    loadJobs();
  };

  const getStatusBadge = (statut: string) => {
    const config: Record<string, { variant: "default" | "secondary" | "destructive" | "outline"; label: string }> = {
      done: { variant: "default", label: "Terminé" },
      running: { variant: "secondary", label: "En cours..." },
      pending: { variant: "outline", label: "En attente" },
      failed: { variant: "destructive", label: "Arrêté" },
    };
    const c = config[statut] || { variant: "outline" as const, label: statut };
    return <Badge variant={c.variant}>{c.label}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scraping</h2>
          <p className="text-muted-foreground">
            {hasRunningJob
              ? "Scraping en cours — les spiders parcourent internet..."
              : "Lancer et planifier les scrappings"}
          </p>
        </div>
        <div className="flex gap-2">
          {hasRunningJob ? (
            <Button variant="destructive" onClick={handleStopAll}>
              <Square className="mr-2 h-4 w-4" />
              Arrêter le scrapping
            </Button>
          ) : (
            <Button onClick={handleLaunch} disabled={launching}>
              {launching ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Lancement...</>
              ) : (
                <><Play className="mr-2 h-4 w-4" />Lancer un scrapping</>
              )}
            </Button>
          )}
          <Dialog>
            <DialogTrigger render={<Button variant="outline" />}>Planifier (cron)</DialogTrigger>
            <DialogContent>
              <DialogHeader><DialogTitle>Nouvelle automatisation</DialogTitle></DialogHeader>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Expression cron</label>
                  <Input value={cronExpression} onChange={(e) => setCronExpression(e.target.value)} placeholder="0 2 * * *" />
                  <p className="text-xs text-muted-foreground mt-1">Exemple: &quot;0 2 * * *&quot; = tous les jours à 2h</p>
                </div>
                <Button onClick={handleCreateCron} className="w-full">Créer</Button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {hasRunningJob && (
        <Card className="border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950">
          <CardContent className="flex items-center gap-3 pt-6">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            <div>
              <p className="font-medium text-blue-900 dark:text-blue-100">Scraping en cours</p>
              <p className="text-sm text-blue-700 dark:text-blue-300">
                Les spiders parcourent les sites d&apos;agences, Google Reviews et Trustpilot...
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Historique des jobs</CardTitle></CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="p-3 text-left text-sm font-medium">Type</th>
                  <th className="p-3 text-left text-sm font-medium">Statut</th>
                  <th className="p-3 text-left text-sm font-medium">Cron</th>
                  <th className="p-3 text-left text-sm font-medium">Créé le</th>
                  <th className="p-3 text-right text-sm font-medium">Agences</th>
                  <th className="p-3 text-center text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="border-b">
                    <td className="p-3 text-sm"><Badge variant="outline">{job.type}</Badge></td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        {(job.statut === "running" || job.statut === "pending") && (
                          <Loader2 className="h-3 w-3 animate-spin" />
                        )}
                        {getStatusBadge(job.statut)}
                      </div>
                    </td>
                    <td className="p-3 text-sm font-mono">{job.cron_expression || "—"}</td>
                    <td className="p-3 text-sm">{new Date(job.created_at).toLocaleString("fr-FR")}</td>
                    <td className="p-3 text-right text-sm">{job.nb_agences_scrappees}</td>
                    <td className="p-3 text-center">
                      {(job.statut === "running" || job.statut === "pending") && (
                        <Button variant="ghost" size="sm" className="text-red-500" onClick={() => handleStop(job.id)}>
                          <Square className="mr-1 h-3 w-3" />
                          Arrêter
                        </Button>
                      )}
                      {job.type === "cron" && job.statut !== "running" && job.statut !== "pending" && (
                        <Button variant="ghost" size="sm" className="text-red-500" onClick={() => handleDeleteCron(job.id)}>Supprimer</Button>
                      )}
                    </td>
                  </tr>
                ))}
                {jobs.length === 0 && (
                  <tr><td colSpan={6} className="p-6 text-center text-muted-foreground">Aucun job</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
