"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Phone, Building2, User, ArrowRight } from "lucide-react";
import { api } from "@/lib/api";

const COLUMNS = [
  { key: "nouveau", label: "Nouvelles cibles", color: "bg-gray-100 border-gray-300" },
  { key: "a_contacter", label: "À contacter", color: "bg-blue-50 border-blue-300" },
  { key: "contacte", label: "Contacté", color: "bg-yellow-50 border-yellow-300" },
  { key: "interesse", label: "Intéressé", color: "bg-green-50 border-green-300" },
  { key: "en_negociation", label: "En négociation", color: "bg-purple-50 border-purple-300" },
  { key: "client", label: "Client", color: "bg-emerald-50 border-emerald-300" },
  { key: "pas_interesse", label: "Pas intéressé", color: "bg-red-50 border-red-300" },
];

interface KanbanCard {
  id: string;
  nom: string;
  ville: string;
  dirigeant_nom: string | null;
  telephone: string | null;
  nb_lots_geres: number | null;
  nb_appels: number;
  dernier_appel: string | null;
}

export default function KanbanPage() {
  const [data, setData] = useState<Record<string, KanbanCard[]>>({});
  const [moving, setMoving] = useState<string | null>(null);

  const loadData = () => {
    api.getKanban().then(setData).catch(console.error);
  };

  useEffect(() => { loadData(); }, []);

  const handleMove = async (agenceId: string, newStatut: string) => {
    setMoving(agenceId);
    try {
      await api.updateCommercial(agenceId, { statut_commercial: newStatut });
      loadData();
    } finally {
      setMoving(null);
    }
  };

  const totalCards = Object.values(data).reduce((sum, cards) => sum + cards.length, 0);

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Pipeline commercial</h2>
        <p className="text-muted-foreground">{totalCards} agences en suivi</p>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-4">
        {COLUMNS.map((col) => {
          const cards = data[col.key] || [];
          return (
            <div key={col.key} className={`min-w-[280px] max-w-[280px] rounded-lg border-2 ${col.color} p-3 flex flex-col`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-sm">{col.label}</h3>
                <Badge variant="secondary" className="text-xs">{cards.length}</Badge>
              </div>

              <div className="space-y-2 flex-1">
                {cards.map((card) => (
                  <Card key={card.id} className="shadow-sm hover:shadow-md transition-shadow">
                    <CardContent className="p-3 space-y-2">
                      <Link href={`/agences/${card.id}`} className="font-medium text-sm text-primary hover:underline block">
                        {card.nom.length > 35 ? card.nom.substring(0, 35) + "..." : card.nom}
                      </Link>

                      <div className="text-xs text-muted-foreground space-y-0.5">
                        {card.ville && (
                          <div className="flex items-center gap-1"><Building2 className="h-3 w-3" /> {card.ville}</div>
                        )}
                        {card.dirigeant_nom && (
                          <div className="flex items-center gap-1"><User className="h-3 w-3" /> {card.dirigeant_nom}</div>
                        )}
                        {card.telephone && (
                          <div className="flex items-center gap-1"><Phone className="h-3 w-3" /> {card.telephone}</div>
                        )}
                        {card.nb_lots_geres && (
                          <div className="text-xs">{card.nb_lots_geres.toLocaleString()} lots</div>
                        )}
                      </div>

                      {card.nb_appels > 0 && (
                        <div className="text-xs text-muted-foreground">
                          {card.nb_appels} appel{card.nb_appels > 1 ? "s" : ""}
                          {card.dernier_appel && ` — dernier: ${new Date(card.dernier_appel).toLocaleDateString("fr-FR")}`}
                        </div>
                      )}

                      {/* Move buttons */}
                      <div className="flex flex-wrap gap-1 pt-1">
                        {COLUMNS.filter((c) => c.key !== col.key).slice(0, 3).map((target) => (
                          <button
                            key={target.key}
                            onClick={() => handleMove(card.id, target.key)}
                            disabled={moving === card.id}
                            className="text-[10px] px-1.5 py-0.5 rounded bg-muted hover:bg-primary hover:text-primary-foreground transition-colors"
                          >
                            → {target.label}
                          </button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {cards.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-4">Aucune agence</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
