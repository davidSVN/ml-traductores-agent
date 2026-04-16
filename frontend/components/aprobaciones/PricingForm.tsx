"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { SolicitudDetalle, ResolverSolicitudPayload } from "@/lib/types";

interface Props {
  solicitud: SolicitudDetalle;
  accion: "aprobar" | "rechazar" | "modificar";
  onSubmit: (payload: ResolverSolicitudPayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

const NIVELES = ["nuevo", "recurrente", "vip", "corporativo"];

export function PricingForm({ solicitud, accion, onSubmit, onCancel, isLoading }: Props) {
  const [respuesta, setRespuesta] = useState("");
  const [nivelPrecio, setNivelPrecio] = useState(solicitud.cliente_nivel_precio ?? "");
  const [descuentoMin, setDescuentoMin] = useState(
    solicitud.cliente_descuento_min != null ? String(solicitud.cliente_descuento_min) : ""
  );
  const [descuentoMax, setDescuentoMax] = useState(
    solicitud.cliente_descuento_max != null ? String(solicitud.cliente_descuento_max) : ""
  );
  const [markup, setMarkup] = useState(
    solicitud.cliente_markup != null ? String(solicitud.cliente_markup) : ""
  );
  const [notasPricing, setNotasPricing] = useState(solicitud.cliente_notas_pricing ?? "");

  const showPricing = accion !== "rechazar";

  const handleSubmit = async () => {
    const payload: ResolverSolicitudPayload = {
      accion,
      respuesta: respuesta || undefined,
    };

    if (showPricing && solicitud.cliente_id) {
      if (nivelPrecio) payload.nivel_precio = nivelPrecio;
      if (descuentoMin !== "") payload.descuento_min = parseFloat(descuentoMin);
      if (descuentoMax !== "") payload.descuento_max = parseFloat(descuentoMax);
      if (markup !== "") payload.markup_personalizado = parseFloat(markup);
      if (notasPricing) payload.notas_pricing = notasPricing;
    }

    await onSubmit(payload);
  };

  const accionLabel = { aprobar: "Aprobar", rechazar: "Rechazar", modificar: "Guardar cambios" }[accion];
  const accionColor = {
    aprobar: "bg-green-700 hover:bg-green-600 text-white",
    rechazar: "bg-red-800 hover:bg-red-700 text-white",
    modificar: "bg-accent-purple hover:bg-accent-purple/80 text-white",
  }[accion];

  return (
    <div className="border-t border-border bg-background p-4 space-y-4">
      {/* Nota/respuesta */}
      <div className="space-y-1.5">
        <label className="text-xs text-text-muted">Nota (opcional)</label>
        <textarea
          value={respuesta}
          onChange={(e) => setRespuesta(e.target.value)}
          placeholder="Agrega un comentario..."
          rows={2}
          className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:ring-1 focus:ring-accent-purple"
        />
      </div>

      {/* Campos de pricing (solo si hay cliente y no es rechazo) */}
      {showPricing && solicitud.cliente_id && (
        <div className="space-y-3">
          <p className="text-xs text-text-muted uppercase tracking-wide">
            Actualizar pricing del cliente
          </p>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-text-muted">Nivel precio</label>
              <select
                value={nivelPrecio}
                onChange={(e) => setNivelPrecio(e.target.value)}
                className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-purple"
              >
                <option value="">Sin cambio</option>
                {NIVELES.map((n) => (
                  <option key={n} value={n} className="capitalize">
                    {n.charAt(0).toUpperCase() + n.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-text-muted">Markup %</label>
              <Input
                type="number"
                min={0}
                max={100}
                step={0.5}
                value={markup}
                onChange={(e) => setMarkup(e.target.value)}
                placeholder="30"
                className="bg-surface border-border text-text-primary"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-text-muted">Descuento mín %</label>
              <Input
                type="number"
                min={0}
                max={100}
                step={0.5}
                value={descuentoMin}
                onChange={(e) => setDescuentoMin(e.target.value)}
                placeholder="0"
                className="bg-surface border-border text-text-primary"
              />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-text-muted">Descuento máx %</label>
              <Input
                type="number"
                min={0}
                max={100}
                step={0.5}
                value={descuentoMax}
                onChange={(e) => setDescuentoMax(e.target.value)}
                placeholder="0"
                className="bg-surface border-border text-text-primary"
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-xs text-text-muted">Notas de pricing</label>
            <textarea
              value={notasPricing}
              onChange={(e) => setNotasPricing(e.target.value)}
              placeholder="Ej: Cliente estratégico, descuento por volumen..."
              rows={2}
              className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:ring-1 focus:ring-accent-purple"
            />
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          disabled={isLoading}
          className="text-text-muted hover:text-text-primary"
        >
          Cancelar
        </Button>
        <Button
          size="sm"
          onClick={handleSubmit}
          disabled={isLoading}
          className={accionColor}
        >
          {isLoading ? "Guardando..." : accionLabel}
        </Button>
      </div>
    </div>
  );
}
