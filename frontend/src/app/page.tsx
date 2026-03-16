"use client";

import { useEffect, useState } from "react";
import { Building2, BriefcaseBusiness, Brain, AlertTriangle } from "lucide-react";
import { KpiCard } from "@/components/cards/kpi-card";
import { api } from "@/lib/api";

export default function DashboardPage() {
  const [stats, setStats] = useState({
    totalAgences: 0,
    offresActives: 0,
    insightsHigh: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadStats() {
      try {
        const [agences, offres, insightsHigh] = await Promise.all([
          api.getAgences("limit=1"),
          api.getOffres("active=true&limit=1"),
          api.getInsights("score_min=50&limit=1"),
        ]);
        setStats({
          totalAgences: agences.total,
          offresActives: offres.total,
          insightsHigh: insightsHigh.total,
        });
      } catch (e) {
        console.error("Failed to load stats", e);
      } finally {
        setLoading(false);
      }
    }
    loadStats();
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Vue d&apos;ensemble</h2>
        <p className="text-muted-foreground">Tableau de bord Amstram</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard title="Agences scrappées" value={loading ? "..." : stats.totalAgences} icon={Building2} />
        <KpiCard title="Offres actives" value={loading ? "..." : stats.offresActives} icon={BriefcaseBusiness} />
        <KpiCard title="Insights score > 50" value={loading ? "..." : stats.insightsHigh} icon={Brain} />
        <KpiCard title="Besoins détectés" value={loading ? "..." : stats.insightsHigh} description="Agences avec score élevé" icon={AlertTriangle} />
      </div>
    </div>
  );
}
