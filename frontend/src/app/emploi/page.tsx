"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Loader2, Search, ExternalLink, Building2, Briefcase } from "lucide-react";
import { api } from "@/lib/api";

interface JobLink {
  title: string;
  url: string;
  snippet: string;
  domain: string;
  is_aggregator: boolean;
  matched_agency: string | null;
  role: string;
}

export default function EmploiPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<string>("all_matched");

  const handleSearch = async () => {
    setLoading(true);
    try {
      const result = await api.rechercheEmploi();
      setData(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const roleBadgeColor = (role: string) => {
    if (role.includes("gestionnaire locatif")) return "bg-blue-100 text-blue-800";
    if (role.includes("assistant gestion")) return "bg-cyan-100 text-cyan-800";
    if (role.includes("gestionnaire copro")) return "bg-purple-100 text-purple-800";
    return "bg-orange-100 text-orange-800";
  };

  const renderLink = (link: JobLink, i: number) => (
    <div
      key={`${link.url}-${i}`}
      className={`p-4 rounded-lg border transition-all hover:shadow-md ${
        link.matched_agency
          ? "border-green-200 bg-green-50/50 dark:bg-green-950/20 dark:border-green-900"
          : "border-gray-200 dark:border-gray-800"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${roleBadgeColor(link.role)}`}>
              {link.role}
            </span>
            {link.matched_agency && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-800 font-semibold flex items-center gap-1">
                <Building2 className="h-3 w-3" />
                {link.matched_agency}
              </span>
            )}
            <span className="text-xs text-muted-foreground">{link.domain}</span>
          </div>
          <a
            href={link.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-primary hover:underline flex items-center gap-1"
          >
            {link.title}
            <ExternalLink className="h-3 w-3 shrink-0" />
          </a>
          {link.snippet && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{link.snippet}</p>
          )}
        </div>
      </div>
    </div>
  );

  const tabs = [
    { key: "all_matched", label: "Matchées avec nos agences", icon: Building2 },
    { key: "all_non_aggregator", label: "Tous (hors agrégateurs)", icon: Briefcase },
    { key: "gestionnaire locatif", label: "Gestionnaire locatif", icon: Search },
    { key: "assistant gestion locative", label: "Assistant gestion locative", icon: Search },
    { key: "gestionnaire copropriété", label: "Gestionnaire copro", icon: Search },
    { key: "assistant copropriété", label: "Assistant copro", icon: Search },
  ];

  const getLinksForTab = (): JobLink[] => {
    if (!data) return [];
    if (activeTab === "all_matched") return data.all_matched || [];
    if (activeTab === "all_non_aggregator") return data.all_non_aggregator || [];
    return (data.by_role?.[activeTab] || []);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Recherche offres d&apos;emploi</h2>
          <p className="text-muted-foreground">
            Scan DuckDuckGo + France Travail pour trouver les agences qui recrutent
          </p>
        </div>
        <Button onClick={handleSearch} disabled={loading} size="lg">
          {loading ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Recherche en cours...</>
          ) : (
            <><Search className="mr-2 h-4 w-4" />Lancer la recherche</>
          )}
        </Button>
      </div>

      {data && (
        <>
          {/* Stats */}
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{data.total_links}</div>
                <p className="text-sm text-muted-foreground">Liens trouvés au total</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{data.agency_links}</div>
                <p className="text-sm text-muted-foreground">Liens d&apos;agences (hors agrégateurs)</p>
              </CardContent>
            </Card>
            <Card className="border-green-200 bg-green-50/50">
              <CardContent className="pt-6">
                <div className="text-2xl font-bold text-green-700">{data.matched_to_db}</div>
                <p className="text-sm text-green-600">Matchées avec nos agences en base</p>
              </CardContent>
            </Card>
          </div>

          {/* Tabs */}
          <div className="flex flex-wrap gap-2">
            {tabs.map((tab) => (
              <Button
                key={tab.key}
                variant={activeTab === tab.key ? "default" : "outline"}
                size="sm"
                onClick={() => setActiveTab(tab.key)}
              >
                <tab.icon className="mr-1 h-3 w-3" />
                {tab.label}
                <Badge variant="secondary" className="ml-2 text-xs">
                  {tab.key === "all_matched"
                    ? data.all_matched?.length || 0
                    : tab.key === "all_non_aggregator"
                    ? data.all_non_aggregator?.length || 0
                    : data.by_role?.[tab.key]?.length || 0}
                </Badge>
              </Button>
            ))}
          </div>

          {/* Results */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {tabs.find((t) => t.key === activeTab)?.label}
                <Badge>{getLinksForTab().length} résultats</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {getLinksForTab().map((link, i) => renderLink(link, i))}
                {getLinksForTab().length === 0 && (
                  <p className="text-center text-muted-foreground py-8">Aucun résultat</p>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {!data && !loading && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Search className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Cliquez sur &quot;Lancer la recherche&quot; pour scanner les offres d&apos;emploi
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              Recherche sur DuckDuckGo + France Travail, ~30 secondes
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
