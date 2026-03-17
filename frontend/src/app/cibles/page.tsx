"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ArrowRight, CheckCircle, HelpCircle, Building2, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "@/lib/api";

interface InsightRow {
  id: string;
  agence_id: string;
  agence_nom: string;
  agence_ville: string;
  agence_region: string;
  agence_groupe: string;
  agence_nb_lots: number | null;
  agence_nb_collab: number | null;
  agence_note_google: number | null;
  agence_a_service_travaux: boolean;
  score_besoin: number;
  signaux: {
    scores: Record<string, number>;
    details: string[];
    donnees_verifiees: string[];
    donnees_manquantes: string[];
    source: string;
    fiabilite: string;
  } | null;
  recommandation: string | null;
}

function ScoreBadge({ score }: { score: number }) {
  if (score >= 75) return <Badge variant="destructive" className="text-sm font-bold px-3 py-1">{score}/100</Badge>;
  if (score >= 50) return <Badge className="bg-orange-500 text-white text-sm font-bold px-3 py-1">{score}/100</Badge>;
  return <Badge variant="secondary" className="text-sm font-bold px-3 py-1">{score}/100</Badge>;
}

function SignalLine({ text }: { text: string }) {
  const isPositive = text.startsWith("✓");
  const isNeutral = text.startsWith("○");
  return (
    <div className={`flex items-start gap-2 text-sm py-1.5 px-2 rounded ${
      isPositive
        ? "bg-green-50 dark:bg-green-950/30 text-green-800 dark:text-green-300"
        : isNeutral
          ? "bg-gray-50 dark:bg-gray-900 text-gray-600 dark:text-gray-400"
          : "bg-red-50 dark:bg-red-950/30 text-red-800 dark:text-red-300"
    }`}>
      {text}
    </div>
  );
}

function CibleCard({ row, expanded, onToggle }: { row: InsightRow; expanded: boolean; onToggle: () => void }) {
  const signaux = row.signaux;
  const details = signaux?.details || [];
  const missing = signaux?.donnees_manquantes || [];
  const verified = signaux?.donnees_verifiees || [];

  return (
    <Card className="border-l-4 border-l-orange-500">
      {/* Header — always visible */}
      <CardHeader className="cursor-pointer" onClick={onToggle}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <ScoreBadge score={row.score_besoin} />
            <div>
              <Link href={`/agences/${row.agence_id}`} className="text-lg font-semibold text-primary hover:underline" onClick={(e) => e.stopPropagation()}>
                {row.agence_nom}
              </Link>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Building2 className="h-3 w-3" />
                {row.agence_ville}{row.agence_region ? `, ${row.agence_region}` : ""}
                {row.agence_groupe && <Badge variant="outline" className="ml-1 text-xs">{row.agence_groupe}</Badge>}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right text-sm">
              {row.agence_nb_lots !== null ? (
                <div><span className="font-semibold">{row.agence_nb_lots.toLocaleString()}</span> lots <span className="text-xs text-green-600">(RNIC)</span></div>
              ) : (
                <div className="text-muted-foreground">Lots non vérifiés</div>
              )}
              {row.agence_nb_collab !== null ? (
                <div><span className="font-semibold">{row.agence_nb_collab}</span> collaborateurs <span className="text-xs text-green-600">(INSEE)</span></div>
              ) : (
                <div className="text-muted-foreground">Effectif non vérifié</div>
              )}
            </div>
            {expanded ? <ChevronUp className="h-5 w-5 text-muted-foreground" /> : <ChevronDown className="h-5 w-5 text-muted-foreground" />}
          </div>
        </div>
      </CardHeader>

      {/* Expanded details */}
      {expanded && (
        <CardContent className="space-y-4 border-t pt-4">
          {/* Raisons du score */}
          <div>
            <h4 className="font-medium mb-2">Pourquoi cette agence est une cible</h4>
            <div className="space-y-1">
              {details.map((d, i) => <SignalLine key={i} text={d} />)}
            </div>
          </div>

          {/* Score breakdown */}
          {signaux?.scores && (
            <div>
              <h4 className="font-medium mb-2">Décomposition du score</h4>
              <div className="flex flex-wrap gap-2">
                {Object.entries(signaux.scores)
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

          {/* Data reliability */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium mb-1 flex items-center gap-1 text-green-700 dark:text-green-400">
                <CheckCircle className="h-4 w-4" /> Données vérifiées ({verified.length})
              </h4>
              <ul className="text-sm space-y-0.5">
                {verified.map((d, i) => (
                  <li key={i} className="text-green-600 dark:text-green-400">
                    {d.replace(/_/g, " ")}
                  </li>
                ))}
                {verified.length === 0 && <li className="text-muted-foreground">Aucune</li>}
              </ul>
            </div>
            <div>
              <h4 className="font-medium mb-1 flex items-center gap-1 text-orange-700 dark:text-orange-400">
                <HelpCircle className="h-4 w-4" /> À vérifier ({missing.length})
              </h4>
              <ul className="text-sm space-y-0.5">
                {missing.map((d, i) => (
                  <li key={i} className="text-orange-600 dark:text-orange-400">
                    {d.split("(")[0].trim()}
                  </li>
                ))}
                {missing.length === 0 && <li className="text-muted-foreground">Tout est vérifié</li>}
              </ul>
            </div>
          </div>

          {/* Source */}
          <div className="text-xs text-muted-foreground border-t pt-2">
            Source : {signaux?.source || "N/A"} — Fiabilité : {signaux?.fiabilite || "Inconnue"}
          </div>

          {/* CTA */}
          <div className="flex gap-2">
            <Button variant="default" size="sm" onClick={async (e) => { e.stopPropagation(); await api.updateCommercial(row.agence_id, { statut_commercial: "a_contacter" }); }}>
              Marquer &quot;À contacter&quot;
            </Button>
            <Link href={`/agences/${row.agence_id}`}>
              <Button variant="outline" size="sm">
                Voir la fiche complète <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export default function CiblesPage() {
  const [items, setItems] = useState<InsightRow[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), limit: "20", score_min: "50" });
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    api.getInsights(params.toString()).then((d: any) => {
      let filtered = d.items;
      if (search) {
        const s = search.toLowerCase();
        filtered = filtered.filter((i: InsightRow) =>
          i.agence_nom.toLowerCase().includes(s) ||
          i.agence_ville?.toLowerCase().includes(s) ||
          i.agence_groupe?.toLowerCase().includes(s)
        );
      }
      setItems(filtered);
      setTotal(d.total);
      setPages(d.pages);
    }).catch(console.error);
  }, [page, search]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Cibles prioritaires</h2>
          <p className="text-muted-foreground">
            {total} agences avec un score de besoin &ge; 50 — classées par potentiel pour Monga
          </p>
        </div>
        <a href={api.exportUrl("insights", "excel")} download>
          <Button variant="outline">Exporter Excel</Button>
        </a>
      </div>

      <Input
        placeholder="Rechercher une agence, ville, groupe..."
        value={search}
        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        className="max-w-md"
      />

      <div className="space-y-3">
        {items.map((row) => (
          <CibleCard
            key={row.id}
            row={row}
            expanded={expandedId === row.id}
            onToggle={() => setExpandedId(expandedId === row.id ? null : row.id)}
          />
        ))}
        {items.length === 0 && (
          <Card>
            <CardContent className="p-8 text-center text-muted-foreground">
              Aucune cible prioritaire. Lancez un scraping depuis le Dashboard.
            </CardContent>
          </Card>
        )}
      </div>

      {pages > 1 && (
        <div className="flex justify-center items-center gap-1">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>←</Button>
          {Array.from({ length: pages }, (_, i) => i + 1)
            .filter((p) => p === 1 || p === pages || Math.abs(p - page) <= 2)
            .reduce<(number | string)[]>((acc, p, i, arr) => {
              if (i > 0 && p - (arr[i - 1] as number) > 1) acc.push("...");
              acc.push(p);
              return acc;
            }, [])
            .map((p, i) =>
              p === "..." ? (
                <span key={`dots-${i}`} className="px-2 text-sm text-muted-foreground">...</span>
              ) : (
                <Button
                  key={p}
                  variant={p === page ? "default" : "outline"}
                  size="sm"
                  className="w-9"
                  onClick={() => setPage(p as number)}
                >
                  {p}
                </Button>
              )
            )}
          <Button variant="outline" size="sm" disabled={page >= pages} onClick={() => setPage(page + 1)}>→</Button>
        </div>
      )}
    </div>
  );
}
