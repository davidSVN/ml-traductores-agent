"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Building2, FileText, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SolicitudDetalle } from "@/lib/types";

interface Props {
  solicitud: SolicitudDetalle;
}

const NIVEL_LABELS: Record<string, string> = {
  nuevo: "Nuevo",
  recurrente: "Recurrente",
  vip: "VIP",
  corporativo: "Corporativo",
};

const COT_ESTADO_COLORS: Record<string, string> = {
  borrador: "bg-surface text-text-muted border-0",
  enviada: "bg-blue-900/30 text-blue-300 border-0",
  aprobada: "bg-green-900/30 text-green-300 border-0",
  perdida: "bg-red-900/30 text-red-300 border-0",
};

export function SolicitudContextCard({ solicitud }: Props) {
  const [open, setOpen] = useState(true);

  const hasDatos = solicitud.datos_formulario && Object.keys(solicitud.datos_formulario).length > 0;

  return (
    <div className="border-b border-border bg-surface">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-surfaceHover transition-colors"
      >
        <span className="text-text-secondary text-xs font-medium uppercase tracking-wide">
          Contexto
        </span>
        {open ? (
          <ChevronUp size={14} className="text-text-muted" />
        ) : (
          <ChevronDown size={14} className="text-text-muted" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4">
          {/* Cliente */}
          {solicitud.cliente_nombre && (
            <div className="space-y-1.5">
              <div className="flex items-center gap-1.5 text-text-muted">
                <Building2 size={12} />
                <span className="text-xs uppercase tracking-wide">Cliente</span>
              </div>
              <p className="text-text-primary text-sm font-medium">{solicitud.cliente_nombre}</p>
              <div className="flex flex-wrap gap-2 mt-1">
                {solicitud.cliente_nivel_precio && (
                  <span className="text-xs text-text-secondary">
                    Nivel:{" "}
                    <span className="text-text-primary">
                      {NIVEL_LABELS[solicitud.cliente_nivel_precio] ?? solicitud.cliente_nivel_precio}
                    </span>
                  </span>
                )}
                {(solicitud.cliente_descuento_min != null || solicitud.cliente_descuento_max != null) && (
                  <span className="text-xs text-text-secondary">
                    Dto:{" "}
                    <span className="text-text-primary">
                      {solicitud.cliente_descuento_min ?? 0}%–{solicitud.cliente_descuento_max ?? 0}%
                    </span>
                  </span>
                )}
                {solicitud.cliente_markup != null && (
                  <span className="text-xs text-text-secondary">
                    Markup: <span className="text-text-primary">{solicitud.cliente_markup}%</span>
                  </span>
                )}
              </div>
              {solicitud.cliente_notas_pricing && (
                <p className="text-text-muted text-xs italic">{solicitud.cliente_notas_pricing}</p>
              )}
            </div>
          )}

          {/* Contacto */}
          {solicitud.contacto_nombre && (
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 text-text-muted">
                <User size={12} />
                <span className="text-xs uppercase tracking-wide">Contacto</span>
              </div>
              <p className="text-text-primary text-sm">{solicitud.contacto_nombre}</p>
              {solicitud.contacto_cargo && (
                <p className="text-text-muted text-xs">{solicitud.contacto_cargo}</p>
              )}
              {solicitud.contacto_email && (
                <p className="text-text-secondary text-xs">{solicitud.contacto_email}</p>
              )}
            </div>
          )}

          {/* Cotización */}
          {solicitud.numero_cotizacion && (
            <div className="space-y-1">
              <div className="flex items-center gap-1.5 text-text-muted">
                <FileText size={12} />
                <span className="text-xs uppercase tracking-wide">Cotización</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-text-primary text-sm font-mono">{solicitud.numero_cotizacion}</span>
                {solicitud.cotizacion_estado && (
                  <Badge className={COT_ESTADO_COLORS[solicitud.cotizacion_estado] ?? "bg-surface text-text-muted border-0 text-xs"}>
                    {solicitud.cotizacion_estado}
                  </Badge>
                )}
              </div>
              {solicitud.cotizacion_total != null && (
                <p className="text-text-secondary text-sm font-medium">
                  ${solicitud.cotizacion_total.toLocaleString("es-CO")}
                </p>
              )}
            </div>
          )}

          {/* Datos formulario del agente */}
          {hasDatos && (
            <div className="space-y-1">
              <span className="text-xs uppercase tracking-wide text-text-muted">
                Datos recopilados
              </span>
              <div className="bg-background rounded-lg p-3 space-y-1">
                {Object.entries(solicitud.datos_formulario).map(([k, v]) => (
                  <div key={k} className="flex gap-2 text-xs">
                    <span className="text-text-muted capitalize min-w-0 shrink-0">
                      {k.replace(/_/g, " ")}:
                    </span>
                    <span className="text-text-secondary break-all">
                      {typeof v === "object" ? JSON.stringify(v) : String(v)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
