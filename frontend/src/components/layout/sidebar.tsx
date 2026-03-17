"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Search } from "lucide-react";
import {
  Building2,
  Brain,
  LayoutDashboard,
  Target,
  Kanban,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Cibles prioritaires", href: "/cibles", icon: Target },
  { name: "Pipeline", href: "/kanban", icon: Kanban },
  { name: "Agences", href: "/agences", icon: Building2 },
  { name: "Tous les insights", href: "/insights", icon: Brain },
];

export function Sidebar() {
  const pathname = usePathname();
  const [search, setSearch] = useState("");
  const router = useRouter();

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-card px-4 py-6">
      <div className="mb-4 px-2">
        <h1 className="text-xl font-bold">Amstram</h1>
        <p className="text-sm text-muted-foreground">Opportunity Finder</p>
      </div>
      <div className="mb-4 px-2">
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && search.trim()) { router.push(`/agences?search=${encodeURIComponent(search.trim())}`); } }}
            placeholder="Rechercher..."
            className="w-full rounded-md border bg-background pl-8 pr-3 py-1.5 text-sm placeholder:text-muted-foreground"
          />
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              }`}
            >
              <item.icon className="h-4 w-4" />
              {item.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
