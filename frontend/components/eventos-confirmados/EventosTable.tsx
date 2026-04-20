"use client";

import { useEffect, useState } from "react";
import { CheckCircle, AlertCircle, Calendar, CalendarCheck, Building2, Phone, Mail } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "";

interface DatosFaltantes {
  nit: boolean;
  rut: boolean;
  orden_compra: boolean;
}

interface EventoConfirmado {
  cotizacion_id: number;
  numero_cotizacion: string;
  cliente: string;
  contacto: string | null;
  telefono: string | null;
  email: string | null;
  servicio: string;
  idioma: string | null;
  fecha_evento: string | null;
  fecha_fin_evento: string | null;
  ubicacion: string | null;
  total: number | null;
  exento_iva: boolean | null;
  nit: string | null;
  tiene_rut: boolean | null;
  numero_rut: string | null;
  numero_orden_compra: string | null;
  correo_facturacion: string | null;
  datos_faltantes: DatosFaltantes;
}

function EstadoFacturacion({ faltantes }: { faltantes: DatosFaltantes }) {
  const lista = [
    faltantes.nit && "NIT",
    faltantes.rut && "RUT",
    faltantes.orden_compra && "Orden de compra",
  ].filter(Boolean) as string[];

  if (lista.length === 0) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/15 text-green-400 text-xs font-medium">
        <CheckCircle size={11} />
        Completo
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-orange-500/15 text-orange-400 text-xs font-medium" title={`Falta: ${lista.join(", ")}`}>
      <AlertCircle size={11} />
      Falta: {lista.join(", ")}
    </span>
  );
}

function formatFecha(fecha: string | null): string {
  if (!fecha) return "—";
  const [y, m, d] = fecha.split("-");
  return `${d}/${m}/${y}`;
}

function formatTotal(total: number | null, exento: boolean | null): string {
  if (!total) return "—";
  const fmt = `$${total.toLocaleString("es-CO", { maximumFractionDigits: 0 })}`;
  return exento ? `${fmt} (exento IVA)` : fmt;
}

export function EventosTable() {
  const [eventos, setEventos] = useState<EventoConfirmado[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API}/dashboard/eventos-confirmados`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setEventos)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-text-muted text-sm">
        Cargando eventos…
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-20 text-red-400 text-sm">
        Error cargando datos: {error}
      </div>
    );
  }

  if (eventos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-text-muted gap-3">
        <CalendarCheck size={40} className="opacity-20" />
        <p className="text-sm">No hay eventos confirmados aún.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-text-muted text-xs uppercase tracking-wide">
            <th className="px-4 py-3 text-left">Cotización</th>
            <th className="px-4 py-3 text-left">Cliente</th>
            <th className="px-4 py-3 text-left">Servicio</th>
            <th className="px-4 py-3 text-left">Fecha evento</th>
            <th className="px-4 py-3 text-left">Ubicación</th>
            <th className="px-4 py-3 text-right">Total</th>
            <th className="px-4 py-3 text-left">NIT</th>
            <th className="px-4 py-3 text-left">RUT</th>
            <th className="px-4 py-3 text-left">Orden compra</th>
            <th className="px-4 py-3 text-left">Facturación</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {eventos.map((ev) => (
            <tr key={ev.cotizacion_id} className="hover:bg-surfaceHover transition-colors">
              <td className="px-4 py-3 font-mono text-text-primary text-xs">
                {ev.numero_cotizacion}
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col gap-0.5">
                  <span className="font-medium text-text-primary flex items-center gap-1">
                    <Building2 size={12} className="text-text-muted shrink-0" />
                    {ev.cliente}
                  </span>
                  {ev.contacto && (
                    <span className="text-text-muted text-xs">{ev.contacto}</span>
                  )}
                  {ev.telefono && (
                    <span className="text-text-muted text-xs flex items-center gap-1">
                      <Phone size={10} /> {ev.telefono}
                    </span>
                  )}
                  {ev.email && (
                    <span className="text-text-muted text-xs flex items-center gap-1">
                      <Mail size={10} /> {ev.email}
                    </span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-col gap-0.5">
                  <span className="text-text-primary">{ev.servicio}</span>
                  {ev.idioma && (
                    <span className="text-text-muted text-xs">{ev.idioma}</span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-text-secondary">
                <span className="flex items-center gap-1">
                  <Calendar size={12} className="text-text-muted shrink-0" />
                  {formatFecha(ev.fecha_evento)}
                  {ev.fecha_fin_evento && ev.fecha_fin_evento !== ev.fecha_evento && (
                    <span className="text-text-muted"> – {formatFecha(ev.fecha_fin_evento)}</span>
                  )}
                </span>
              </td>
              <td className="px-4 py-3 text-text-muted text-xs max-w-32 truncate" title={ev.ubicacion ?? ""}>
                {ev.ubicacion || "—"}
              </td>
              <td className="px-4 py-3 text-right font-medium text-text-primary whitespace-nowrap">
                {formatTotal(ev.total, ev.exento_iva)}
              </td>
              <td className="px-4 py-3 text-text-secondary text-xs">
                {ev.nit || <span className="text-orange-400">Pendiente</span>}
              </td>
              <td className="px-4 py-3 text-text-secondary text-xs">
                {ev.tiene_rut && ev.numero_rut
                  ? ev.numero_rut
                  : ev.tiene_rut === false
                  ? <span className="text-text-muted">No aplica</span>
                  : <span className="text-orange-400">Pendiente</span>
                }
              </td>
              <td className="px-4 py-3 text-text-secondary text-xs">
                {ev.numero_orden_compra || <span className="text-text-muted">No aplica</span>}
              </td>
              <td className="px-4 py-3">
                <EstadoFacturacion faltantes={ev.datos_faltantes} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
