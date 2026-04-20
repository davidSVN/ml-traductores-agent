"use client";

import { useState } from "react";
import { createPortal } from "react-dom";
import { Building2, User, FileText, Pencil, X, Save, ExternalLink, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useSolicitudDetalle } from "@/lib/hooks/useSolicitudDetalle";
import { updateClientePricing, updateContacto, updateCotizacion } from "@/lib/api";
import type { SolicitudDetalle, UpdatePricingPayload } from "@/lib/types";

// ─── Visor PDF modal ───────────────────────────────────────────────────────────
function PdfModal({ url, onClose }: { url: string; onClose: () => void }) {
  const [loaded, setLoaded] = useState(false);

  const modal = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="relative bg-surface rounded-xl overflow-hidden flex flex-col shadow-2xl"
        style={{ width: "min(90vw, 1100px)", height: "90vh" }}>

        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-surface shrink-0">
          <span className="text-text-secondary text-sm font-medium">Vista previa del PDF</span>
          <div className="flex items-center gap-2">
            <a href={url} target="_blank" rel="noopener noreferrer"
              className="flex items-center gap-1 text-xs text-text-muted hover:text-accent-purple transition-colors">
              <ExternalLink size={13} />
              Abrir en nueva pestaña
            </a>
            <button onClick={onClose}
              className="text-text-muted hover:text-text-primary transition-colors ml-2">
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Iframe */}
        <div className="flex-1 relative bg-background">
          {!loaded && (
            <div className="absolute inset-0 flex items-center justify-center">
              <Loader2 size={28} className="text-accent-purple animate-spin" />
            </div>
          )}
          <iframe
            src={url}
            onLoad={() => setLoaded(true)}
            className="w-full h-full border-0"
            title="Cotización PDF"
          />
        </div>
      </div>
    </div>
  );

  if (typeof document === "undefined") return null;
  return createPortal(modal, document.body);
}

interface Props {
  solicitudId: number;
}

const NIVEL_LABELS: Record<string, string> = {
  nuevo: "Nuevo",
  recurrente: "Recurrente",
  vip: "VIP",
  corporativo: "Corporativo",
};

const NIVELES = ["nuevo", "recurrente", "vip", "corporativo"];

const COT_ESTADO_COLORS: Record<string, string> = {
  borrador: "bg-surface text-text-muted border-0",
  enviada: "bg-blue-900/30 text-blue-300 border-0",
  aprobada: "bg-green-900/30 text-green-300 border-0",
  perdida: "bg-red-900/30 text-red-300 border-0",
};

export function SolicitudInfoPanel({ solicitudId }: Props) {
  const { data: solicitud, mutate } = useSolicitudDetalle(solicitudId);
  const [editingPricing, setEditingPricing] = useState(false);
  const [editingContacto, setEditingContacto] = useState(false);
  const [saving, setSaving] = useState(false);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);

  // Pricing form state
  const [nivelPrecio, setNivelPrecio] = useState("");
  const [descuentoMin, setDescuentoMin] = useState("");
  const [descuentoMax, setDescuentoMax] = useState("");
  const [markup, setMarkup] = useState("");
  const [notasPricing, setNotasPricing] = useState("");

  // Contacto form state
  const [email, setEmail] = useState("");
  const [telefono, setTelefono] = useState("");
  const [cargo, setCargo] = useState("");

  const startEditPricing = (s: SolicitudDetalle) => {
    setNivelPrecio(s.cliente_nivel_precio ?? "");
    setDescuentoMin(s.cliente_descuento_min != null ? String(s.cliente_descuento_min) : "");
    setDescuentoMax(s.cliente_descuento_max != null ? String(s.cliente_descuento_max) : "");
    setMarkup(s.cliente_markup != null ? String(s.cliente_markup) : "");
    setNotasPricing(s.cliente_notas_pricing ?? "");
    setEditingPricing(true);
  };

  const savePricing = async () => {
    if (!solicitud?.cliente_id) return;
    setSaving(true);
    try {
      const payload: UpdatePricingPayload = {};
      if (nivelPrecio) payload.nivel_precio = nivelPrecio;
      if (descuentoMin !== "") payload.descuento_min_porcentaje = parseFloat(descuentoMin);
      if (descuentoMax !== "") payload.descuento_max_porcentaje = parseFloat(descuentoMax);
      if (markup !== "") payload.markup_personalizado = parseFloat(markup);
      if (notasPricing) payload.notas_pricing = notasPricing;
      await updateClientePricing(solicitud.cliente_id, payload);
      setEditingPricing(false);
      await mutate();
    } finally {
      setSaving(false);
    }
  };

  const startEditContacto = (s: SolicitudDetalle) => {
    setEmail(s.contacto_email ?? "");
    setTelefono(s.contacto_telefono ?? "");
    setCargo(s.contacto_cargo ?? "");
    setEditingContacto(true);
  };

  const saveContacto = async () => {
    if (!solicitud?.contacto_id) return;
    setSaving(true);
    try {
      await updateContacto(solicitud.contacto_id, {
        email: email || undefined,
        telefono: telefono || undefined,
        cargo: cargo || undefined,
      });
      setEditingContacto(false);
      await mutate();
    } finally {
      setSaving(false);
    }
  };

  if (!solicitud) {
    return (
      <div className="w-72 shrink-0 border-l border-border bg-surface p-4 space-y-4 overflow-y-auto">
        <Skeleton className="h-4 w-1/2" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-12 w-full" />
      </div>
    );
  }

  return (
    <div className="w-72 shrink-0 border-l border-border bg-surface overflow-y-auto">

      {/* ── CLIENTE ── */}
      <section className="border-b border-border p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-text-muted">
            <Building2 size={12} />
            <span className="text-xs uppercase tracking-wide font-medium">Cliente</span>
          </div>
          {solicitud.cliente_id && !editingPricing && (
            <button
              onClick={() => startEditPricing(solicitud)}
              className="text-text-muted hover:text-accent-purple transition-colors"
              title="Editar pricing"
            >
              <Pencil size={12} />
            </button>
          )}
          {editingPricing && (
            <button onClick={() => setEditingPricing(false)} className="text-text-muted hover:text-text-primary">
              <X size={12} />
            </button>
          )}
        </div>

        {solicitud.cliente_nombre ? (
          <p className="text-text-primary font-semibold text-sm">{solicitud.cliente_nombre}</p>
        ) : (
          <p className="text-text-muted text-xs italic">Sin cliente asignado</p>
        )}

        {!editingPricing ? (
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 flex-wrap">
              {solicitud.cliente_nivel_precio && (
                <span className="text-xs bg-background rounded px-2 py-0.5 text-text-secondary">
                  {NIVEL_LABELS[solicitud.cliente_nivel_precio] ?? solicitud.cliente_nivel_precio}
                </span>
              )}
              {(solicitud.cliente_descuento_min != null || solicitud.cliente_descuento_max != null) && (
                <span className="text-xs text-text-muted">
                  Dto: <span className="text-text-secondary">{solicitud.cliente_descuento_min ?? 0}%–{solicitud.cliente_descuento_max ?? 0}%</span>
                </span>
              )}
              {solicitud.cliente_markup != null && (
                <span className="text-xs text-text-muted">
                  Markup: <span className="text-text-secondary">{solicitud.cliente_markup}%</span>
                </span>
              )}
            </div>
            {solicitud.cliente_notas_pricing ? (
              <p className="text-text-muted text-xs italic leading-relaxed">{solicitud.cliente_notas_pricing}</p>
            ) : (
              <p className="text-text-muted text-xs italic opacity-60">sin notas de pricing</p>
            )}
          </div>
        ) : (
          <div className="space-y-2">
            <div>
              <label className="text-xs text-text-muted">Nivel</label>
              <select
                value={nivelPrecio}
                onChange={(e) => setNivelPrecio(e.target.value)}
                className="w-full mt-1 bg-background border border-border rounded px-2 py-1.5 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-purple"
              >
                <option value="">Sin cambio</option>
                {NIVELES.map((n) => (
                  <option key={n} value={n}>{n.charAt(0).toUpperCase() + n.slice(1)}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-text-muted">Dto mín %</label>
                <Input type="number" min={0} max={100} step={0.5} value={descuentoMin}
                  onChange={(e) => setDescuentoMin(e.target.value)} placeholder="0"
                  className="mt-1 h-7 text-xs bg-background border-border text-text-primary" />
              </div>
              <div>
                <label className="text-xs text-text-muted">Dto máx %</label>
                <Input type="number" min={0} max={100} step={0.5} value={descuentoMax}
                  onChange={(e) => setDescuentoMax(e.target.value)} placeholder="0"
                  className="mt-1 h-7 text-xs bg-background border-border text-text-primary" />
              </div>
            </div>
            <div>
              <label className="text-xs text-text-muted">Markup %</label>
              <Input type="number" min={0} max={200} step={0.5} value={markup}
                onChange={(e) => setMarkup(e.target.value)} placeholder="30"
                className="mt-1 h-7 text-xs bg-background border-border text-text-primary" />
            </div>
            <div>
              <label className="text-xs text-text-muted">Notas de pricing</label>
              <textarea value={notasPricing} onChange={(e) => setNotasPricing(e.target.value)}
                rows={2} placeholder="Ej: descuento por volumen..."
                className="mt-1 w-full bg-background border border-border rounded px-2 py-1.5 text-xs text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:ring-1 focus:ring-accent-purple" />
            </div>
            <Button size="sm" onClick={savePricing} disabled={saving}
              className="w-full h-7 text-xs bg-accent-purple hover:bg-accent-purple/80 text-white gap-1">
              <Save size={11} />
              {saving ? "Guardando..." : "Guardar pricing"}
            </Button>
          </div>
        )}
      </section>

      {/* ── CONTACTO ── */}
      {solicitud.contacto_id && (
        <section className="border-b border-border p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-text-muted">
              <User size={12} />
              <span className="text-xs uppercase tracking-wide font-medium">Contacto</span>
            </div>
            {!editingContacto && (
              <button onClick={() => startEditContacto(solicitud)}
                className="text-text-muted hover:text-accent-purple transition-colors" title="Editar contacto">
                <Pencil size={12} />
              </button>
            )}
            {editingContacto && (
              <button onClick={() => setEditingContacto(false)} className="text-text-muted hover:text-text-primary">
                <X size={12} />
              </button>
            )}
          </div>

          <p className="text-text-primary text-sm font-medium">{solicitud.contacto_nombre}</p>

          {!editingContacto ? (
            <div className="space-y-1">
              {solicitud.contacto_cargo && <p className="text-text-muted text-xs">{solicitud.contacto_cargo}</p>}
              {solicitud.contacto_email && <p className="text-text-secondary text-xs">{solicitud.contacto_email}</p>}
              {solicitud.contacto_telefono && <p className="text-text-muted text-xs">{solicitud.contacto_telefono}</p>}
              {!solicitud.contacto_cargo && !solicitud.contacto_email && !solicitud.contacto_telefono && (
                <p className="text-text-muted text-xs italic opacity-60">sin datos de contacto</p>
              )}
            </div>
          ) : (
            <div className="space-y-2">
              <div>
                <label className="text-xs text-text-muted">Cargo</label>
                <Input value={cargo} onChange={(e) => setCargo(e.target.value)} placeholder="Director Ejecutivo"
                  className="mt-1 h-7 text-xs bg-background border-border text-text-primary" />
              </div>
              <div>
                <label className="text-xs text-text-muted">Email</label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="correo@empresa.com"
                  className="mt-1 h-7 text-xs bg-background border-border text-text-primary" />
              </div>
              <div>
                <label className="text-xs text-text-muted">Teléfono</label>
                <Input value={telefono} onChange={(e) => setTelefono(e.target.value)} placeholder="+57..."
                  className="mt-1 h-7 text-xs bg-background border-border text-text-primary" />
              </div>
              <Button size="sm" onClick={saveContacto} disabled={saving}
                className="w-full h-7 text-xs bg-accent-purple hover:bg-accent-purple/80 text-white gap-1">
                <Save size={11} />
                {saving ? "Guardando..." : "Guardar contacto"}
              </Button>
            </div>
          )}
        </section>
      )}

      {/* ── COTIZACIÓN ── */}
      {solicitud.numero_cotizacion && (
        <section className="border-b border-border p-4 space-y-3">
          <div className="flex items-center gap-1.5 text-text-muted">
            <FileText size={12} />
            <span className="text-xs uppercase tracking-wide font-medium">Cotización</span>
          </div>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-text-primary text-sm font-mono font-semibold">{solicitud.numero_cotizacion}</span>
              {solicitud.cotizacion_estado && (
                <Badge className={`text-xs ${COT_ESTADO_COLORS[solicitud.cotizacion_estado] ?? "bg-surface text-text-muted border-0"}`}>
                  {solicitud.cotizacion_estado}
                </Badge>
              )}
            </div>
            {solicitud.cotizacion_total != null && (
              <p className="text-text-primary text-lg font-bold">
                ${solicitud.cotizacion_total.toLocaleString("es-CO")}
              </p>
            )}
            {/* Toggle: términos corporativos */}
            {solicitud.cotizacion_id && (
              <div className="flex items-center justify-between pt-1">
                <span className="text-xs text-text-muted" title="Incluye coordinador asignado, política de cancelación 50%, cronograma 24h y más">
                  Términos corporativos
                </span>
                <button
                  onClick={async () => {
                    await updateCotizacion(solicitud.cotizacion_id!, {
                      incluir_terminos_corporativos: !solicitud.incluir_terminos_corporativos,
                    });
                    await mutate();
                  }}
                  className={`relative w-8 h-4 rounded-full transition-colors focus:outline-none ${
                    solicitud.incluir_terminos_corporativos ? "bg-accent-purple" : "bg-border"
                  }`}
                  title={solicitud.incluir_terminos_corporativos ? "Desactivar términos corporativos" : "Activar términos corporativos en el PDF"}
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform ${
                      solicitud.incluir_terminos_corporativos ? "translate-x-4" : ""
                    }`}
                  />
                </button>
              </div>
            )}
          </div>
        </section>
      )}

      {/* ── DATOS RECOPILADOS ── */}
      {solicitud.datos_formulario && Object.keys(solicitud.datos_formulario).length > 0 && (
        <section className="p-4 space-y-2">
          <span className="text-xs uppercase tracking-wide text-text-muted font-medium">
            Datos del servicio
          </span>
          <div className="space-y-1">
            {Object.entries(solicitud.datos_formulario)
              .filter(([k, v]) => v != null && v !== "" && k !== "url_pdf")
              .map(([k, v]) => (
                <div key={k} className="flex gap-2 text-xs">
                  <span className="text-text-muted capitalize shrink-0 min-w-[70px]">
                    {k.replace(/_/g, " ")}:
                  </span>
                  <span className="text-text-secondary break-all">{String(v)}</span>
                </div>
              ))}
            {/* Botón ver PDF */}
            {typeof solicitud.datos_formulario.url_pdf === "string" && (
              <button
                onClick={() => setPdfUrl(solicitud.datos_formulario.url_pdf as string)}
                className="inline-flex items-center gap-1.5 mt-2 text-xs bg-accent-purple/15 hover:bg-accent-purple/25 text-accent-purple rounded-lg px-3 py-1.5 transition-colors font-medium"
              >
                <FileText size={12} />
                Ver PDF
              </button>
            )}
          </div>
        </section>
      )}

      {/* Modal visor PDF */}
      {pdfUrl && <PdfModal url={pdfUrl} onClose={() => setPdfUrl(null)} />}
    </div>
  );
}
