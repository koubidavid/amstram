"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScoreGauge } from "@/components/charts/score-gauge";
import { api } from "@/lib/api";
import type { Agence, AvisRead, OffreEmploi, InsightRead } from "@/lib/types";

export default function AgenceDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const [agence, setAgence] = useState<Agence | null>(null);
  const [avis, setAvis] = useState<AvisRead[]>([]);
  const [offres, setOffres] = useState<OffreEmploi[]>([]);
  const [insights, setInsights] = useState<InsightRead[]>([]);

  useEffect(() => {
    if (!id) return;
    api.getAgence(id).then(setAgence).catch(console.error);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getAgenceAvis(id).then((d: any) => setAvis(d.items)).catch(console.error);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getAgenceOffres(id).then((d: any) => setOffres(d.items)).catch(console.error);
    api.getAgenceInsightsHistorique(id).then(setInsights).catch(console.error);
  }, [id]);

  if (!agence) return <div className="p-8">Chargement...</div>;

  const latestInsight = insights.length > 0 ? insights[insights.length - 1] : null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{agence.nom}</h2>
          <p className="text-muted-foreground">{agence.groupe} — {agence.ville}, {agence.region}</p>
        </div>
        {latestInsight && <ScoreGauge score={latestInsight.score_besoin} size="lg" />}
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Lots gérés</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{agence.nb_lots_geres ?? "—"}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Collaborateurs</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{agence.nb_collaborateurs ?? "—"}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Note Google</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{agence.note_google?.toFixed(1) ?? "—"}</div></CardContent></Card>
        <Card><CardHeader className="pb-2"><CardTitle className="text-sm">Note Trustpilot</CardTitle></CardHeader><CardContent><div className="text-2xl font-bold">{agence.note_trustpilot?.toFixed(1) ?? "—"}</div></CardContent></Card>
      </div>

      <Tabs defaultValue="insights">
        <TabsList>
          <TabsTrigger value="insights">Insights ({insights.length})</TabsTrigger>
          <TabsTrigger value="offres">Offres ({offres.length})</TabsTrigger>
          <TabsTrigger value="avis">Avis ({avis.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="insights" className="space-y-4">
          {latestInsight ? (
            <Card>
              <CardHeader><CardTitle>Dernier insight</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                <p><strong>Recommandation:</strong> {latestInsight.recommandation}</p>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>Ratio lots/collab: <strong>{latestInsight.ratio_lots_collab?.toFixed(1) ?? "N/A"}</strong></div>
                  <div>Turnover: <strong>{latestInsight.turnover_score ?? 0} offres</strong></div>
                  <div>Avis négatifs travaux: <strong>{latestInsight.avis_negatifs_travaux ?? 0}</strong></div>
                  <div>Croissance parc: <strong>{latestInsight.croissance_parc?.toFixed(1) ?? 0}%</strong></div>
                  <div>Service travaux: <Badge variant={latestInsight.has_service_travaux ? "default" : "secondary"}>{latestInsight.has_service_travaux ? "Oui" : "Non"}</Badge></div>
                </div>
              </CardContent>
            </Card>
          ) : <p className="text-muted-foreground">Aucun insight disponible</p>}
        </TabsContent>

        <TabsContent value="offres">
          {offres.length > 0 ? (
            <div className="rounded-md border">
              <table className="w-full">
                <thead><tr className="border-b bg-muted/50"><th className="p-3 text-left text-sm">Titre</th><th className="p-3 text-left text-sm">Type</th><th className="p-3 text-center text-sm">Active</th><th className="p-3 text-left text-sm">Date</th></tr></thead>
                <tbody>
                  {offres.map((o) => (
                    <tr key={o.id} className="border-b"><td className="p-3 text-sm">{o.titre}</td><td className="p-3 text-sm"><Badge variant="outline">{o.type_poste.replace(/_/g, " ")}</Badge></td><td className="p-3 text-center"><Badge variant={o.active ? "default" : "secondary"}>{o.active ? "Oui" : "Non"}</Badge></td><td className="p-3 text-sm">{o.date_publication || "—"}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="text-muted-foreground">Aucune offre</p>}
        </TabsContent>

        <TabsContent value="avis">
          {avis.length > 0 ? (
            <div className="space-y-3">
              {avis.map((a) => (
                <Card key={a.id}>
                  <CardContent className="pt-4">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">{a.source}</Badge>
                      <span className="font-bold">{a.note}/5</span>
                      {a.mentionne_travaux && <Badge variant="destructive">Travaux</Badge>}
                      {a.mentionne_reactivite && <Badge variant="destructive">Réactivité</Badge>}
                    </div>
                    <p className="text-sm text-muted-foreground">{a.texte || "Pas de texte"}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : <p className="text-muted-foreground">Aucun avis</p>}
        </TabsContent>
      </Tabs>
    </div>
  );
}
