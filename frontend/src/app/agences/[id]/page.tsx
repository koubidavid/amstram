"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink, AlertTriangle, CheckCircle, HelpCircle } from "lucide-react";
import { ScoreGauge } from "@/components/charts/score-gauge";
import { api } from "@/lib/api";
import type { Agence, InsightRead } from "@/lib/types";

function DataField({ label, value, source }: { label: string; value: string | number | null | undefined; source?: string }) {
  const hasValue = value !== null && value !== undefined && value !== "";
  return (
    <div className="flex items-start justify-between border-b py-3 last:border-0">
      <div>
        <p className="text-sm font-medium">{label}</p>
        {hasValue ? (
          <p className="text-lg font-semibold">{value}</p>
        ) : (
          <p className="text-sm text-orange-600 flex items-center gap-1">
            <HelpCircle className="h-3 w-3" /> Non vérifié
          </p>
        )}
      </div>
      {source && <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">{source}</span>}
    </div>
  );
}

export default function AgenceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const [agence, setAgence] = useState<Agence | null>(null);
  const [insights, setInsights] = useState<InsightRead[]>([]);

  useEffect(() => {
    if (!id) return;
    api.getAgence(id).then(setAgence).catch(console.error);
    api.getAgenceInsightsHistorique(id).then(setInsights).catch(console.error);
  }, [id]);

  if (!agence) return <div className="p-8">Chargement...</div>;

  const latestInsight = insights.length > 0 ? insights[insights.length - 1] : null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const signaux = (latestInsight?.signaux as any) || {};
  const details: string[] = signaux.details || [];
  const missingData: string[] = signaux.donnees_manquantes || [];
  const verifiedData: string[] = signaux.donnees_verifiees || [];

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <Button variant="ghost" onClick={() => router.back()} className="gap-2 -ml-2">
        <ArrowLeft className="h-4 w-4" /> Retour
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{agence.nom}</h2>
          <p className="text-muted-foreground">
            {agence.groupe && <span className="font-medium">{agence.groupe} — </span>}
            {agence.ville}{agence.region ? `, ${agence.region}` : ""}
          </p>
          {agence.adresse && <p className="text-sm text-muted-foreground mt-1">{agence.adresse}</p>}
          {agence.site_web && (
            <a href={agence.site_web} target="_blank" rel="noopener noreferrer"
               className="text-sm text-primary hover:underline flex items-center gap-1 mt-1">
              {agence.site_web} <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
        {latestInsight && <ScoreGauge score={latestInsight.score_besoin} size="lg" />}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Données vérifiées */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" /> Données vérifiées
            </CardTitle>
            <p className="text-xs text-muted-foreground">Source: API INSEE / recherche-entreprises.api.gouv.fr</p>
          </CardHeader>
          <CardContent>
            <DataField label="Nom complet" value={agence.nom} source="INSEE" />
            <DataField label="Adresse" value={agence.adresse} source="INSEE" />
            <DataField label="Code postal" value={agence.code_postal} source="INSEE" />
            <DataField label="Ville" value={agence.ville} source="INSEE" />
            <DataField label="Région" value={agence.region} source="INSEE" />
            <DataField label="Groupe" value={agence.groupe || null} source="Détection auto" />
            <DataField label="Nombre de collaborateurs" value={agence.nb_collaborateurs} source="INSEE (tranche)" />
            <DataField label="Activité" value="Administration d'immeubles / Agence immobilière" source="Code NAF" />
          </CardContent>
        </Card>

        {/* Données à vérifier */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HelpCircle className="h-5 w-5 text-orange-500" /> À vérifier par le commercial
            </CardTitle>
            <p className="text-xs text-muted-foreground">Ces informations ne sont pas disponibles via les APIs publiques</p>
          </CardHeader>
          <CardContent>
            <DataField label="Nombre de lots gérés" value={agence.nb_lots_geres} />
            <DataField label="Note Google" value={agence.note_google ? `${agence.note_google}/5` : null} />
            <DataField label="Nombre d'avis Google" value={agence.nb_avis_google} />
            <DataField label="Note Trustpilot" value={agence.note_trustpilot ? `${agence.note_trustpilot}/5` : null} />
            <DataField label="Service travaux interne" value={agence.a_service_travaux ? "Oui (détecté dans le nom)" : null} />
            <DataField label="Site web" value={agence.site_web || null} />

            <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-950 rounded-lg">
              <p className="text-sm font-medium text-orange-800 dark:text-orange-200 mb-2">Actions recommandées :</p>
              <ul className="text-sm text-orange-700 dark:text-orange-300 space-y-1">
                {missingData.map((item, i) => (
                  <li key={i} className="flex items-start gap-1">
                    <span className="mt-0.5">•</span> {item}
                  </li>
                ))}
                {missingData.length === 0 && <li>Toutes les données sont disponibles</li>}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Insight détaillé */}
      {latestInsight && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5" /> Analyse Monga — Potentiel commercial
              </CardTitle>
              <Badge variant={latestInsight.score_besoin >= 30 ? "default" : "secondary"}>
                {latestInsight.recommandation}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Fiabilité : {signaux.fiabilite || "Inconnue"} — Source : {signaux.source || "N/A"}
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Signaux détectés */}
            <div>
              <h4 className="font-medium mb-2">Signaux détectés</h4>
              <div className="space-y-2">
                {details.map((detail: string, i: number) => (
                  <div key={i} className={`flex items-start gap-2 text-sm p-2 rounded ${
                    detail.startsWith("✓")
                      ? "bg-green-50 dark:bg-green-950 text-green-800 dark:text-green-200"
                      : "bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400"
                  }`}>
                    {detail}
                  </div>
                ))}
                {details.length === 0 && (
                  <p className="text-sm text-muted-foreground">Aucun signal détecté — données insuffisantes</p>
                )}
              </div>
            </div>

            {/* Score breakdown */}
            {signaux.scores && (
              <div>
                <h4 className="font-medium mb-2">Décomposition du score</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(signaux.scores as Record<string, number>).map(([key, val]) => (
                    <div key={key} className="text-center p-3 bg-muted/50 rounded-lg">
                      <p className="text-2xl font-bold">{typeof val === 'number' ? (key === 'completude_donnees' ? `${val}%` : `+${val}`) : val}</p>
                      <p className="text-xs text-muted-foreground">{key.replace(/_/g, " ")}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Verified vs missing */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-1 text-green-700 dark:text-green-400">Données vérifiées ({verifiedData.length})</h4>
                <ul className="text-sm space-y-0.5">
                  {verifiedData.map((d, i) => (
                    <li key={i} className="flex items-center gap-1 text-green-600 dark:text-green-400">
                      <CheckCircle className="h-3 w-3" /> {d.replace(/_/g, " ")}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-1 text-orange-700 dark:text-orange-400">Données manquantes ({missingData.length})</h4>
                <ul className="text-sm space-y-0.5">
                  {missingData.map((d, i) => (
                    <li key={i} className="flex items-center gap-1 text-orange-600 dark:text-orange-400">
                      <HelpCircle className="h-3 w-3" /> {d.split("(")[0].trim()}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
