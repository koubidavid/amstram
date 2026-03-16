import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScoreGauge } from "@/components/charts/score-gauge";
import type { InsightRead } from "@/lib/types";

interface InsightCardProps {
  insight: InsightRead;
  agenceNom?: string;
}

export function InsightCard({ insight, agenceNom }: InsightCardProps) {
  const getBadgeVariant = (score: number) => {
    if (score > 75) return "destructive" as const;
    if (score > 50) return "default" as const;
    return "secondary" as const;
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div className="space-y-1">
          {agenceNom && <CardTitle className="text-base">{agenceNom}</CardTitle>}
          <Badge variant={getBadgeVariant(insight.score_besoin)}>{insight.recommandation}</Badge>
        </div>
        <ScoreGauge score={insight.score_besoin} />
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>Ratio lots/collab: <strong>{insight.ratio_lots_collab?.toFixed(1) || "N/A"}</strong></div>
          <div>Turnover: <strong>{insight.turnover_score || 0} offres</strong></div>
          <div>Avis négatifs travaux: <strong>{insight.avis_negatifs_travaux || 0}</strong></div>
          <div>Croissance parc: <strong>{insight.croissance_parc?.toFixed(1) || 0}%</strong></div>
          <div>Service travaux: <strong>{insight.has_service_travaux ? "Oui" : "Non"}</strong></div>
        </div>
      </CardContent>
    </Card>
  );
}
