"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Agence, PaginatedResponse } from "@/lib/types";

export default function AgencesPage() {
  const [data, setData] = useState<PaginatedResponse<Agence> | null>(null);
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), limit: "20" });
    if (search) params.set("ville", search);
    api.getAgences(params.toString()).then(setData).catch(console.error);
  }, [page, search]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Agences</h2>
          <p className="text-muted-foreground">{data?.total || 0} agences trouvées</p>
        </div>
        <div className="flex gap-2">
          <Input placeholder="Filtrer par ville..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="w-64" />
          <a href={api.exportUrl("agences", "excel")} download>
            <Button variant="outline">Exporter Excel</Button>
          </a>
        </div>
      </div>

      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-3 text-left text-sm font-medium">Nom</th>
              <th className="p-3 text-left text-sm font-medium">Ville</th>
              <th className="p-3 text-left text-sm font-medium">Région</th>
              <th className="p-3 text-right text-sm font-medium">Lots gérés</th>
              <th className="p-3 text-right text-sm font-medium">Collaborateurs</th>
              <th className="p-3 text-center text-sm font-medium">Note Google</th>
              <th className="p-3 text-center text-sm font-medium">Service travaux</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((agence) => (
              <tr key={agence.id} className="border-b hover:bg-muted/25 transition-colors">
                <td className="p-3">
                  <Link href={`/agences/${agence.id}`} className="font-medium text-primary hover:underline">
                    {agence.nom}
                  </Link>
                  {agence.groupe && <span className="ml-2 text-xs text-muted-foreground">({agence.groupe})</span>}
                </td>
                <td className="p-3 text-sm">{agence.ville || "—"}</td>
                <td className="p-3 text-sm">{agence.region || "—"}</td>
                <td className="p-3 text-right text-sm">{agence.nb_lots_geres ?? "—"}</td>
                <td className="p-3 text-right text-sm">{agence.nb_collaborateurs ?? "—"}</td>
                <td className="p-3 text-center text-sm">{agence.note_google?.toFixed(1) ?? "—"}</td>
                <td className="p-3 text-center">
                  <Badge variant={agence.a_service_travaux ? "default" : "secondary"}>
                    {agence.a_service_travaux ? "Oui" : "Non"}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data && data.pages > 1 && (
        <div className="flex justify-center gap-2">
          <Button variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>Précédent</Button>
          <span className="flex items-center px-3 text-sm">Page {page} / {data.pages}</span>
          <Button variant="outline" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>Suivant</Button>
        </div>
      )}
    </div>
  );
}
