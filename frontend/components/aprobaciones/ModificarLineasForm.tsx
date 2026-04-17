"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { getLineasCotizacion, modificarLineas } from "@/lib/api";
import type { LineaCotizacion } from "@/lib/types";
import { Loader2 } from "lucide-react";

interface Props {
  solicitudId: number;
  cotizacionId: number;
  onDone: () => void;
  onCancel: () => void;
}

function formatCOP(value: number) {
  return `$${Math.round(value).toLocaleString("es-CO")}`;
}

function parseCOP(raw: string): number {
  return parseFloat(raw.replace(/[^0-9.]/g, "")) || 0;
}

export function ModificarLineasForm({ solicitudId, cotizacionId, onDone, onCancel }: Props) {
  const [lineas, setLineas] = useState<LineaCotizacion[]>([]);
  const [precios, setPrecios] = useState<Record<number, string>>({});
  const [respuesta, setRespuesta] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getLineasCotizacion(cotizacionId)
      .then((data) => {
        setLineas(data);
        const init: Record<number, string> = {};
        data.forEach((l) => {
          init[l.id] = Math.round(l.precio_total).toLocaleString("es-CO");
        });
        setPrecios(init);
      })
      .finally(() => setLoading(false));
  }, [cotizacionId]);

  const subtotal = lineas.reduce((sum, l) => sum + parseCOP(precios[l.id] ?? "0"), 0);
  const iva = subtotal * 0.19;
  const total = subtotal + iva;

  const handlePrecioChange = (id: number, raw: string) => {
    // Solo números y puntos
    const cleaned = raw.replace(/[^0-9]/g, "");
    setPrecios((prev) => ({ ...prev, [id]: cleaned ? Number(cleaned).toLocaleString("es-CO") : "" }));
  };

  const handleSubmit = async () => {
    setSaving(true);
    try {
      await modificarLineas(solicitudId, {
        lineas: lineas.map((l) => ({ linea_id: l.id, nuevo_precio: parseCOP(precios[l.id] ?? "0") })),
        respuesta: respuesta || undefined,
      });
      onDone();
    } catch {
      // silently ignore
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="border-t border-border bg-background p-4 flex items-center gap-2 text-text-muted text-sm">
        <Loader2 size={14} className="animate-spin" />
        Cargando líneas de cotización...
      </div>
    );
  }

  return (
    <div className="border-t border-border bg-background p-4 space-y-4">
      <p className="text-xs font-medium text-text-muted uppercase tracking-wide">
        Modificar precios — edita cada línea directamente
      </p>

      {/* Líneas editables */}
      <div className="space-y-2">
        {lineas.map((linea) => (
          <div key={linea.id} className="flex items-start gap-3 bg-surface rounded-xl px-3 py-2.5">
            <div className="flex-1 min-w-0">
              <p className="text-sm text-text-primary leading-snug">{linea.descripcion}</p>
            </div>
            <div className="shrink-0">
              <div className="flex items-center gap-1">
                <span className="text-text-muted text-sm">$</span>
                <input
                  type="text"
                  value={precios[linea.id] ?? ""}
                  onChange={(e) => handlePrecioChange(linea.id, e.target.value)}
                  className="w-32 bg-background border border-border rounded-lg px-2 py-1 text-sm text-text-primary text-right focus:outline-none focus:ring-1 focus:ring-accent-purple"
                  placeholder="0"
                />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Resumen de totales recalculado en tiempo real */}
      <div className="bg-surface rounded-xl px-3 py-2.5 space-y-1 text-sm">
        <div className="flex justify-between text-text-muted">
          <span>Subtotal</span>
          <span>{formatCOP(subtotal)}</span>
        </div>
        <div className="flex justify-between text-text-muted">
          <span>IVA 19%</span>
          <span>{formatCOP(iva)}</span>
        </div>
        <div className="flex justify-between font-semibold text-text-primary border-t border-border pt-1 mt-1">
          <span>Total</span>
          <span>{formatCOP(total)}</span>
        </div>
      </div>

      {/* Nota */}
      <div className="space-y-1">
        <label className="text-xs text-text-muted">Nota para el cliente (opcional)</label>
        <textarea
          value={respuesta}
          onChange={(e) => setRespuesta(e.target.value)}
          placeholder="Ej: Ajustamos los precios según lo acordado..."
          rows={2}
          className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:ring-1 focus:ring-accent-purple"
        />
      </div>

      <div className="flex gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          disabled={saving}
          className="text-text-muted hover:text-text-primary"
        >
          Cancelar
        </Button>
        <Button
          size="sm"
          onClick={handleSubmit}
          disabled={saving || lineas.length === 0}
          className="bg-accent-purple hover:bg-accent-purple/80 text-white gap-1.5"
        >
          {saving ? (
            <>
              <Loader2 size={13} className="animate-spin" />
              Guardando...
            </>
          ) : (
            "Guardar y reenviar PDF"
          )}
        </Button>
      </div>
    </div>
  );
}
