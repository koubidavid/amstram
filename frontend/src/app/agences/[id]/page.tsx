"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, ExternalLink, CheckCircle, HelpCircle, User, Phone, Save } from "lucide-react";
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

const STATUTS = [
  { value: "nouveau", label: "Nouveau", color: "bg-gray-100 text-gray-800" },
  { value: "a_contacter", label: "À contacter", color: "bg-blue-100 text-blue-800" },
  { value: "contacte", label: "Contacté", color: "bg-yellow-100 text-yellow-800" },
  { value: "interesse", label: "Intéressé", color: "bg-green-100 text-green-800" },
  { value: "en_negociation", label: "En négociation", color: "bg-purple-100 text-purple-800" },
  { value: "client", label: "Client", color: "bg-emerald-100 text-emerald-800" },
  { value: "pas_interesse", label: "Pas intéressé", color: "bg-red-100 text-red-800" },
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function AgenceDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [agence, setAgence] = useState<any>(null);
  const [insights, setInsights] = useState<InsightRead[]>([]);
  const [notes, setNotes] = useState("");
  const [statut, setStatut] = useState("nouveau");
  const [telephone, setTelephone] = useState("");
  const [saving, setSaving] = useState(false);
  const [appelResume, setAppelResume] = useState("");
  const [appelResultat, setAppelResultat] = useState("pas_repondu");
  const [loggingAppel, setLoggingAppel] = useState(false);

  useEffect(() => {
    if (!id) return;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getAgence(id).then((a: any) => {
      setAgence(a);
      setNotes(a.notes_commercial || "");
      setStatut(a.statut_commercial || "nouveau");
      setTelephone(a.telephone || "");
    }).catch(console.error);
    api.getAgenceInsightsHistorique(id).then(setInsights).catch(console.error);
  }, [id]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await api.updateCommercial(id, { statut_commercial: statut, notes_commercial: notes, telephone });
      setAgence(updated);
    } finally {
      setSaving(false);
    }
  };

  const handleLogAppel = async () => {
    setLoggingAppel(true);
    try {
      const updated = await api.logAppel(id, { resume: appelResume, resultat: appelResultat });
      setAgence(updated);
      setAppelResume("");
    } finally {
      setLoggingAppel(false);
    }
  };

  if (!agence) return <div className="p-8">Chargement...</div>;

  const latestInsight = insights.length > 0 ? insights[insights.length - 1] : null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const signaux = (latestInsight?.signaux as any) || {};
  const details: string[] = signaux.details || [];
  const missingData: string[] = signaux.donnees_manquantes || [];
  const verifiedData: string[] = signaux.donnees_verifiees || [];

  return (
    <div className="space-y-6">
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
            <a href={agence.site_web.startsWith("http") ? agence.site_web : `https://${agence.site_web}`} target="_blank" rel="noopener noreferrer"
               className="text-sm text-primary hover:underline flex items-center gap-1 mt-1">
              {agence.site_web} <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
        {latestInsight && <ScoreGauge score={latestInsight.score_besoin} size="lg" />}
      </div>

      {/* Commercial tracking */}
      <Card className="border-2 border-primary/20">
        <CardHeader>
          <CardTitle>Suivi commercial</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2 flex-wrap">
            {STATUTS.map((s) => (
              <button
                key={s.value}
                onClick={() => setStatut(s.value)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                  statut === s.value ? `${s.color} ring-2 ring-offset-1 ring-primary` : "bg-muted text-muted-foreground hover:bg-muted/80"
                }`}
              >
                {s.label}
              </button>
            ))}
          </div>
          <div className="flex gap-3">
            <Input
              value={telephone}
              onChange={(e) => setTelephone(e.target.value)}
              placeholder="Numéro de téléphone"
              className="max-w-[200px]"
            />
            {telephone && (
              <a href={`tel:${telephone}`}>
                <Button variant="outline" size="sm"><Phone className="mr-2 h-4 w-4" /> Appeler</Button>
              </a>
            )}
          </div>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Notes du commercial..."
            className="w-full min-h-[60px] rounded-md border px-3 py-2 text-sm"
          />
          <Button onClick={handleSave} disabled={saving} size="sm">
            <Save className="mr-2 h-4 w-4" /> {saving ? "Sauvegarde..." : "Sauvegarder"}
          </Button>
        </CardContent>
      </Card>

      {/* Log appel */}
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Phone className="h-5 w-5" /> Journal d&apos;appels</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Input
              value={appelResume}
              onChange={(e) => setAppelResume(e.target.value)}
              placeholder="Résumé de l'appel..."
              className="flex-1"
            />
            <select className="rounded-md border px-2 text-sm" value={appelResultat} onChange={(e) => setAppelResultat(e.target.value)}>
              <option value="pas_repondu">Pas répondu</option>
              <option value="rappeler">À rappeler</option>
              <option value="interesse">Intéressé</option>
              <option value="rdv_pris">RDV pris</option>
              <option value="pas_interesse">Pas intéressé</option>
            </select>
            <Button onClick={handleLogAppel} disabled={loggingAppel || !appelResume} size="sm">
              {loggingAppel ? "..." : "Enregistrer"}
            </Button>
          </div>

          {/* Historique */}
          {agence.appels && agence.appels.length > 0 ? (
            <div className="space-y-2">
              {[...agence.appels].reverse().map((appel: { date: string; resume: string; resultat: string }, i: number) => (
                <div key={i} className="flex items-start gap-3 text-sm border-b pb-2 last:border-0">
                  <span className="text-xs text-muted-foreground whitespace-nowrap">{new Date(appel.date).toLocaleString("fr-FR")}</span>
                  <span className="flex-1">{appel.resume}</span>
                  <Badge variant="outline" className="text-xs shrink-0">{appel.resultat}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Aucun appel enregistré</p>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Données vérifiées */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" /> Données vérifiées
            </CardTitle>
          </CardHeader>
          <CardContent>
            <DataField label="Nom complet" value={agence.nom} source="INSEE" />
            <DataField label="SIREN" value={agence.siren} source="INSEE" />
            <DataField label="Adresse" value={agence.adresse} source="INSEE" />
            <DataField label="Ville" value={agence.ville} source="INSEE" />
            <DataField label="Collaborateurs (tranche)" value={agence.nb_collaborateurs} source="INSEE" />
            {agence.effectif_precise && <DataField label="Effectif précis" value={agence.effectif_precise} source="Pappers" />}
            <DataField label="Nombre de lots gérés" value={agence.nb_lots_geres} source="RNIC" />
            {agence.nb_coproprietes > 0 && <DataField label="Copropriétés gérées" value={agence.nb_coproprietes} source="RNIC" />}
          </CardContent>
        </Card>

        {/* Données Pappers */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5 text-blue-600" /> Informations Pappers
            </CardTitle>
            <p className="text-xs text-muted-foreground">Source: Pappers.fr / INPI / BODACC</p>
          </CardHeader>
          <CardContent>
            <DataField label="Dirigeant" value={agence.dirigeant_nom ? `${agence.dirigeant_nom} (${agence.dirigeant_qualite || ""})` : null} source="Pappers" />
            <DataField label="Chiffre d'affaires" value={agence.chiffre_affaires ? `${(agence.chiffre_affaires as number).toLocaleString("fr-FR")} €` : null} source="Pappers" />
            <DataField label="Résultat net" value={agence.resultat_net !== null && agence.resultat_net !== undefined ? `${(agence.resultat_net as number).toLocaleString("fr-FR")} €` : null} source="Pappers" />
            <DataField label="Date de création" value={agence.date_creation} source="Pappers" />
            <DataField label="Forme juridique" value={agence.forme_juridique} source="Pappers" />
            <DataField label="Site web" value={agence.site_web || null} source={agence.site_web ? "Pappers" : undefined} />
          </CardContent>
        </Card>
      </div>

      {/* Insight détaillé */}
      {latestInsight && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Analyse Monga — Potentiel commercial</CardTitle>
              <Badge variant={latestInsight.score_besoin >= 50 ? "default" : "secondary"}>
                {latestInsight.recommandation}
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Fiabilité : {signaux.fiabilite || "Inconnue"} — Source : {signaux.source || "N/A"}
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Signaux détectés</h4>
              <div className="space-y-1.5">
                {details.map((detail: string, i: number) => (
                  <div key={i} className={`text-sm p-2 rounded ${
                    detail.startsWith("✓") ? "bg-green-50 dark:bg-green-950/30 text-green-800 dark:text-green-200"
                    : detail.startsWith("○") ? "bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400"
                    : "bg-red-50 dark:bg-red-950/30 text-red-800 dark:text-red-200"
                  }`}>
                    {detail}
                  </div>
                ))}
              </div>
            </div>

            {signaux.scores && (
              <div>
                <h4 className="font-medium mb-2">Décomposition du score</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(signaux.scores as Record<string, number>)
                    .filter(([key]) => key !== "completude_donnees")
                    .sort(([, a], [, b]) => (b as number) - (a as number))
                    .map(([key, val]) => (
                      <div key={key} className={`text-center px-3 py-1.5 rounded-lg text-sm ${
                        (val as number) > 0 ? "bg-green-100 dark:bg-green-950 text-green-800 dark:text-green-300 font-medium" : "bg-gray-100 dark:bg-gray-900 text-gray-500"
                      }`}>
                        +{val as number} {key.replace(/_/g, " ")}
                      </div>
                    ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-1 text-green-700 dark:text-green-400 flex items-center gap-1">
                  <CheckCircle className="h-4 w-4" /> Vérifié ({verifiedData.length})
                </h4>
                <ul className="text-sm space-y-0.5">
                  {verifiedData.map((d, i) => <li key={i} className="text-green-600">{d.replace(/_/g, " ")}</li>)}
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-1 text-orange-700 dark:text-orange-400 flex items-center gap-1">
                  <HelpCircle className="h-4 w-4" /> À vérifier ({missingData.length})
                </h4>
                <ul className="text-sm space-y-0.5">
                  {missingData.map((d, i) => <li key={i} className="text-orange-600">{d.split("(")[0].trim()}</li>)}
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
