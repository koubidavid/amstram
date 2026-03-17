"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, TrendingUp, Newspaper, Lightbulb, ExternalLink, RefreshCw } from "lucide-react";

interface Article {
  title: string;
  link: string;
  description: string;
  pub_date: string;
  source: string;
  relevance_score: number;
  matched_keywords: string[];
  pitch_recommendations: string[];
}

interface PredictionsData {
  generated_at: string;
  total_articles: number;
  high_relevance: Article[];
  medium_relevance: Article[];
  top_pitch_angles: { pitch: string; mentions: number }[];
  market_summary: {
    total_relevant: number;
    most_mentioned_topics: { topic: string; count: number }[];
  };
}

export default function PredictionsPage() {
  const [data, setData] = useState<PredictionsData | null>(null);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const d = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/predictions`
      ).then((r) => r.json());
      setData(d);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        <span className="ml-3 text-muted-foreground">Analyse des actualités immobilières...</span>
      </div>
    );
  }

  if (!data) return <div className="p-8 text-muted-foreground">Impossible de charger les prédictions.</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Prédictions &amp; Veille</h2>
          <p className="text-muted-foreground">
            {data.total_articles} articles analysés — {data.market_summary.total_relevant} pertinents pour Monga
          </p>
        </div>
        <Button variant="outline" onClick={load} disabled={loading}>
          <RefreshCw className="mr-2 h-4 w-4" /> Actualiser
        </Button>
      </div>

      {/* Top pitch angles */}
      {data.top_pitch_angles.length > 0 && (
        <Card className="border-2 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-yellow-500" /> Arguments de vente recommandés
            </CardTitle>
            <p className="text-xs text-muted-foreground">Basés sur l&apos;actualité du moment — à intégrer dans le pitch commercial</p>
          </CardHeader>
          <CardContent className="space-y-3">
            {data.top_pitch_angles.map((angle, i) => (
              <div key={i} className="p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                <div className="flex items-start gap-2">
                  <span className="text-lg font-bold text-yellow-600">{i + 1}.</span>
                  <div>
                    <p className="text-sm font-medium">{angle.pitch}</p>
                    <p className="text-xs text-muted-foreground mt-1">Mentionné dans {angle.mentions} article{angle.mentions > 1 ? "s" : ""}</p>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Trending topics */}
      {data.market_summary.most_mentioned_topics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-blue-500" /> Tendances du marché
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {data.market_summary.most_mentioned_topics.map((topic, i) => (
                <Badge key={i} variant={i < 3 ? "default" : "secondary"} className="text-sm py-1 px-3">
                  {topic.topic} ({topic.count})
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* High relevance articles */}
      {data.high_relevance.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Newspaper className="h-5 w-5" /> Actualités clés pour Monga
          </h3>
          <div className="space-y-3">
            {data.high_relevance.map((article, i) => (
              <Card key={i}>
                <CardContent className="pt-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs">{article.source}</Badge>
                        <Badge className="bg-red-100 text-red-800 text-xs">Score: {article.relevance_score}</Badge>
                      </div>
                      <h4 className="font-medium text-sm">{article.title}</h4>
                      {article.description && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{article.description.replace(/<[^>]*>/g, "")}</p>
                      )}
                      <div className="flex flex-wrap gap-1 mt-2">
                        {article.matched_keywords.slice(0, 5).map((kw, j) => (
                          <span key={j} className="text-[10px] bg-muted px-1.5 py-0.5 rounded">{kw}</span>
                        ))}
                      </div>
                      {article.pitch_recommendations.length > 0 && (
                        <div className="mt-2 p-2 bg-yellow-50 dark:bg-yellow-950/20 rounded text-xs">
                          <strong>Angle de pitch :</strong> {article.pitch_recommendations[0]}
                        </div>
                      )}
                    </div>
                    {article.link && (
                      <a href={article.link} target="_blank" rel="noopener noreferrer" className="shrink-0">
                        <Button variant="ghost" size="sm"><ExternalLink className="h-4 w-4" /></Button>
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Medium relevance */}
      {data.medium_relevance.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Autres actualités pertinentes</h3>
          <div className="space-y-2">
            {data.medium_relevance.map((article, i) => (
              <div key={i} className="flex items-center justify-between border-b pb-2 text-sm">
                <div className="flex-1">
                  <span className="text-xs text-muted-foreground mr-2">[{article.source}]</span>
                  {article.title}
                </div>
                {article.link && (
                  <a href={article.link} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline text-xs shrink-0 ml-2">
                    Lire →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <p className="text-xs text-muted-foreground text-center">
        Dernière analyse : {new Date(data.generated_at).toLocaleString("fr-FR")}
      </p>
    </div>
  );
}
