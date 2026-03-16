"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import type { ScrapingJob } from "@/lib/types";

export default function ScrapingPage() {
  const [jobs, setJobs] = useState<ScrapingJob[]>([]);
  const [cronExpression, setCronExpression] = useState("0 2 * * *");
  const [launching, setLaunching] = useState(false);

  const loadJobs = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getScrapingJobs().then((d: any) => setJobs(d.items)).catch(console.error);
  };

  useEffect(() => { loadJobs(); }, []);

  const handleLaunch = async () => {
    setLaunching(true);
    try {
      await api.lancerScraping();
      loadJobs();
    } finally {
      setLaunching(false);
    }
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
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline"> = {
      done: "default", running: "secondary", pending: "outline", failed: "destructive",
    };
    return <Badge variant={variants[statut] || "outline"}>{statut}</Badge>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Scraping</h2>
          <p className="text-muted-foreground">Lancer et planifier les scrappings</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleLaunch} disabled={launching}>
            {launching ? "Lancement..." : "Lancer un scrapping"}
          </Button>
          <Dialog>
            <DialogTrigger><Button variant="outline">Planifier (cron)</Button></DialogTrigger>
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
                    <td className="p-3">{getStatusBadge(job.statut)}</td>
                    <td className="p-3 text-sm font-mono">{job.cron_expression || "—"}</td>
                    <td className="p-3 text-sm">{new Date(job.created_at).toLocaleString("fr-FR")}</td>
                    <td className="p-3 text-right text-sm">{job.nb_agences_scrappees}</td>
                    <td className="p-3 text-center">
                      {job.type === "cron" && (
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
