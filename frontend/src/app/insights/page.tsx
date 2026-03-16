"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { InsightCard } from "@/components/cards/insight-card";
import { api } from "@/lib/api";
import type { InsightRead, PaginatedResponse } from "@/lib/types";

export default function InsightsPage() {
  const [data, setData] = useState<PaginatedResponse<InsightRead> | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    api.getInsights(`page=${page}&limit=12`).then(setData).catch(console.error);
  }, [page]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Insights</h2>
          <p className="text-muted-foreground">Classement par score de besoin</p>
        </div>
        <a href={api.exportUrl("insights", "excel")} download><Button variant="outline">Exporter</Button></a>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {data?.items.map((insight) => (
          <InsightCard key={insight.id} insight={insight} />
        ))}
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
