"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
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

  return (
    <aside className="flex h-screen w-64 flex-col border-r bg-card px-4 py-6">
      <div className="mb-8 px-2">
        <h1 className="text-xl font-bold">Amstram</h1>
        <p className="text-sm text-muted-foreground">Opportunity Finder</p>
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
