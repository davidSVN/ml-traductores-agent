"use client";

import { useSolicitudes } from "@/lib/hooks/useSolicitudes";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { useState } from "react";
import type { Solicitud } from "@/lib/types";

const TIPO_LABELS: Record<string, string> = {
  aprobar_cotizacion: "Aprobar cotización",
  completar_cliente: "Completar cliente",
  consulta_precio: "Consulta precio",
  escalar_negociacion: "Negociación",
  otro: "Otro",
};

const TIPO_COLORS: Record<string, string> = {
  aprobar_cotizacion: "bg-accent-purple/20 text-accent-purple border-0",
  completar_cliente: "bg-blue-900/30 text-blue-300 border-0",
  consulta_precio: "bg-accent-orange/15 text-accent-orange border-0",
  escalar_negociacion: "bg-red-900/30 text-red-300 border-0",
  otro: "bg-surface text-text-muted border-0",
};

interface SolicitudListProps {
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function SolicitudList({ selectedId, onSelect }: SolicitudListProps) {
  const [estado, setEstado] = useState<string | undefined>("pendiente");
  const { data, isLoading } = useSolicitudes(estado);

  return (
    <div className="flex flex-col flex-1 min-h-0 bg-surface overflow-hidden">
      {/* Header */}
      <div className="px-4 py-4 border-b border-border">
        <h2 className="text-text-primary font-semibold text-sm mb-3">Aprobaciones</h2>
        <Tabs
          defaultValue="pendiente"
          onValueChange={(v) => setEstado(v === "todas" ? undefined : v)}
        >
          <TabsList className="bg-background w-full">
            <TabsTrigger value="pendiente" className="flex-1 text-xs">Pendientes</TabsTrigger>
            <TabsTrigger value="aprobada" className="flex-1 text-xs">Resueltas</TabsTrigger>
            <TabsTrigger value="todas" className="flex-1 text-xs">Todas</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Lista */}
      <div className="flex-1 min-h-0 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-1/2" />
              </div>
            ))}
          </div>
        ) : data?.data.length === 0 ? (
          <div className="p-8 text-center text-text-muted text-sm">
            Sin solicitudes {estado === "pendiente" ? "pendientes" : ""}
          </div>
        ) : (
          data?.data.map((s: Solicitud) => (
            <SolicitudItem
              key={s.id}
              solicitud={s}
              isSelected={selectedId === s.id}
              onClick={() => onSelect(s.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

function SolicitudItem({
  solicitud,
  isSelected,
  onClick,
}: {
  solicitud: Solicitud;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left px-4 py-3 border-b border-border transition-colors",
        isSelected
          ? "bg-accent-purple/10 border-l-2 border-l-accent-purple"
          : "hover:bg-surfaceHover"
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <Badge className={cn("text-xs shrink-0", TIPO_COLORS[solicitud.tipo] ?? "bg-surface text-text-muted border-0")}>
          {TIPO_LABELS[solicitud.tipo] ?? solicitud.tipo}
        </Badge>
        {solicitud.estado === "pendiente" && (
          <span className="w-2 h-2 rounded-full bg-accent-orange shrink-0 mt-1" />
        )}
      </div>
      <p className="text-text-primary text-sm font-medium leading-snug line-clamp-2 mt-1">
        {solicitud.titulo}
      </p>
      {solicitud.cliente_nombre && (
        <p className="text-text-muted text-xs mt-1 truncate">{solicitud.cliente_nombre}</p>
      )}
      <div className="flex items-center justify-between mt-1.5">
        {solicitud.numero_cotizacion && (
          <span className="text-text-muted text-xs font-mono">{solicitud.numero_cotizacion}</span>
        )}
        <span className="text-text-muted text-xs ml-auto">
          {formatRelativeTime(solicitud.created_at ?? "")}
        </span>
      </div>
    </button>
  );
}
