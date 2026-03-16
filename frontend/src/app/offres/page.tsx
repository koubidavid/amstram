"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { OffreEmploi, PaginatedResponse } from "@/lib/types";

export default function OffresPage() {
  const [data, setData] = useState<PaginatedResponse<OffreEmploi> | null>(null);
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState("");

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), limit: "20" });
    if (typeFilter) params.set("type_poste", typeFilter);
    api.getOffres(params.toString()).then(setData).catch(console.error);
  }, [page, typeFilter]);

  const typeOptions = [
    { value: "", label: "Tous les types" },
    { value: "gestionnaire_locatif", label: "Gestionnaire locatif" },
    { value: "assistant_gestion_locative", label: "Assistant gestion locative" },
    { value: "gestionnaire_copropriete", label: "Gestionnaire copropriété" },
    { value: "assistant_copropriete", label: "Assistant copropriété" },
    { value: "autre", label: "Autre" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Offres d&apos;emploi</h2>
          <p className="text-muted-foreground">{data?.total || 0} offres trouvées</p>
        </div>
        <div className="flex gap-2">
          <select className="rounded-md border px-3 py-2 text-sm" value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}>
            {typeOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <a href={api.exportUrl("offres", "excel")} download><Button variant="outline">Exporter</Button></a>
        </div>
      </div>

      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              <th className="p-3 text-left text-sm font-medium">Titre</th>
              <th className="p-3 text-left text-sm font-medium">Type</th>
              <th className="p-3 text-center text-sm font-medium">Active</th>
              <th className="p-3 text-left text-sm font-medium">Date publication</th>
              <th className="p-3 text-left text-sm font-medium">URL</th>
            </tr>
          </thead>
          <tbody>
            {data?.items.map((offre) => (
              <tr key={offre.id} className="border-b hover:bg-muted/25">
                <td className="p-3 text-sm font-medium">{offre.titre}</td>
                <td className="p-3"><Badge variant="outline">{offre.type_poste.replace(/_/g, " ")}</Badge></td>
                <td className="p-3 text-center"><Badge variant={offre.active ? "default" : "secondary"}>{offre.active ? "Active" : "Inactive"}</Badge></td>
                <td className="p-3 text-sm">{offre.date_publication || "—"}</td>
                <td className="p-3 text-sm">{offre.url_source ? <a href={offre.url_source} target="_blank" className="text-primary hover:underline">Voir</a> : "—"}</td>
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
