"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare,
  BarChart2,
  Users,
  List,
  Bell,
  Settings,
} from "lucide-react";
import { useStats } from "@/lib/hooks/useStats";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/chats", icon: MessageSquare, label: "Chats", badge: "mensajes_no_leidos" as const },
  { href: "/metricas", icon: BarChart2, label: "Métricas" },
  { href: "/clientes", icon: Users, label: "Clientes" },
  { href: "/servicios", icon: List, label: "Servicios" },
  {
    href: "/aprobaciones",
    icon: Bell,
    label: "Aprobaciones",
    badge: "solicitudes_pendientes" as const,
  },
  { href: "/configuracion", icon: Settings, label: "Configuración" },
];

type BadgeKey = "mensajes_no_leidos" | "solicitudes_pendientes";

export function Sidebar() {
  const pathname = usePathname();
  const { data: stats } = useStats();

  const badgeValue: Record<BadgeKey, number> = {
    mensajes_no_leidos: stats?.conversaciones_activas ?? 0,
    solicitudes_pendientes: stats?.solicitudes_pendientes ?? 0,
  };

  return (
    <aside className="w-16 md:w-56 flex flex-col bg-surface border-r border-border h-screen sticky top-0">
      {/* Logo */}
      <div className="px-4 py-5 border-b border-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent-purple flex items-center justify-center shrink-0">
            <span className="text-white text-xs font-bold">ML</span>
          </div>
          <span className="hidden md:block text-text-primary font-semibold text-sm leading-tight">
            ML Traductores
          </span>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {NAV_ITEMS.map(({ href, icon: Icon, label, badge }) => {
          const isActive = pathname === href || pathname.startsWith(href + "/");
          const count = badge ? badgeValue[badge] : 0;

          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-sm",
                isActive
                  ? "bg-accent-purple/20 text-text-primary"
                  : "text-text-secondary hover:bg-surfaceHover hover:text-text-primary"
              )}
            >
              <Icon size={18} className="shrink-0" />
              <span className="hidden md:block flex-1">{label}</span>
              {badge && count > 0 && (
                <span className="hidden md:flex items-center justify-center h-5 min-w-5 px-1 rounded-full bg-accent-orange text-white text-xs font-bold">
                  {count}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-border">
        <p className="hidden md:block text-text-muted text-xs">María Luisa Trujillo</p>
        <p className="hidden md:block text-text-muted text-xs">Directora Comercial</p>
      </div>
    </aside>
  );
}
