"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
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
  ratio_lots_collab: number | null;
  turnover_score: number | null;
  avis_negatifs_travaux: number | null;
  croissance_parc: number | null;
  has_service_travaux: boolean;
  recommandation: string | null;
}

function ScoreBadge({ score }: { score: number }) {
  if (score > 75) return <Badge variant="destructive" className="text-xs font-bold">{score}</Badge>;
  if (score > 50) return <Badge className="bg-orange-500 text-white text-xs font-bold">{score}</Badge>;
  if (score > 25) return <Badge className="bg-yellow-500 text-black text-xs font-bold">{score}</Badge>;
  return <Badge variant="secondary" className="text-xs font-bold">{score}</Badge>;
}

export default function InsightsPage() {
  const [items, setItems] = useState<InsightRow[]>([]);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [scoreFilter, setScoreFilter] = useState("");

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), limit: "20" });
    if (scoreFilter) params.set("score_min", scoreFilter);
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
  }, [page, scoreFilter, search]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Insights</h2>
          <p className="text-muted-foreground">{total} agences analysées — classées par score de besoin</p>
        </div>
        <a href={api.exportUrl("insights", "excel")} download><Button variant="outline">Exporter</Button></a>
      </div>

      <div className="flex gap-3">
        <Input
          placeholder="Rechercher une agence, ville, groupe..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); }}
          className="max-w-sm"
        />
        <select
          className="rounded-md border px-3 py-2 text-sm"
          value={scoreFilter}
          onChange={(e) => { setScoreFilter(e.target.value); setPage(1); }}
        >
          <option value="">Tous les scores</option>
          <option value="75">Score &gt; 75 (Forte probabilité)</option>
          <option value="50">Score &gt; 50 (Besoin probable)</option>
          <option value="25">Score &gt; 25 (À surveiller)</option>
        </select>
      </div>

      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-3 text-left text-sm font-medium">Score</th>
              <th className="p-3 text-left text-sm font-medium">Agence</th>
              <th className="p-3 text-left text-sm font-medium">Ville</th>
              <th className="p-3 text-left text-sm font-medium">Région</th>
              <th className="p-3 text-right text-sm font-medium">Lots</th>
              <th className="p-3 text-right text-sm font-medium">Collab.</th>
              <th className="p-3 text-center text-sm font-medium">Note Google</th>
              <th className="p-3 text-center text-sm font-medium">Service travaux</th>
              <th className="p-3 text-left text-sm font-medium">Recommandation</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.id} className="border-b hover:bg-muted/25 transition-colors cursor-pointer">
                <td className="p-3">
                  <ScoreBadge score={row.score_besoin} />
                </td>
                <td className="p-3">
                  <Link href={`/agences/${row.agence_id}`} className="font-medium text-primary hover:underline">
                    {row.agence_nom}
                  </Link>
                  {row.agence_groupe && (
                    <span className="ml-2 text-xs text-muted-foreground">({row.agence_groupe})</span>
                  )}
                </td>
                <td className="p-3 text-sm">{row.agence_ville || "—"}</td>
                <td className="p-3 text-sm">{row.agence_region || "—"}</td>
                <td className="p-3 text-right text-sm">{row.agence_nb_lots ?? "—"}</td>
                <td className="p-3 text-right text-sm">{row.agence_nb_collab ?? "—"}</td>
                <td className="p-3 text-center text-sm">
                  {row.agence_note_google ? (
                    <span className={row.agence_note_google < 3 ? "text-red-600 font-medium" : ""}>
                      {row.agence_note_google.toFixed(1)}/5
                    </span>
                  ) : "—"}
                </td>
                <td className="p-3 text-center">
                  <Badge variant={row.has_service_travaux ? "default" : "secondary"}>
                    {row.has_service_travaux ? "Oui" : "Non"}
                  </Badge>
                </td>
                <td className="p-3 text-sm max-w-[200px] truncate">
                  {row.recommandation || "—"}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={9} className="p-6 text-center text-muted-foreground">Aucun insight disponible. Lancez un scraping d&apos;abord.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>Précédent</Button>
          <span className="flex items-center px-3 text-sm">Page {page} / {pages}</span>
          <Button variant="outline" disabled={page >= pages} onClick={() => setPage(page + 1)}>Suivant</Button>
        </div>
      )}
    </div>
  );
}
