"use client";

import { useEffect, useRef, useState } from "react";
import { Send, CheckCircle, XCircle, Edit3 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useSolicitudDetalle } from "@/lib/hooks/useSolicitudDetalle";
import { useMensajesInternos } from "@/lib/hooks/useMensajesInternos";
import { postMensajeInterno, resolverSolicitud } from "@/lib/api";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { PricingForm } from "./PricingForm";
import type { ResolverSolicitudPayload } from "@/lib/types";

interface Props {
  solicitudId: number;
}

const TIPO_LABELS: Record<string, string> = {
  aprobar_cotizacion: "Aprobar cotización",
  completar_cliente: "Completar cliente",
  consulta_precio: "Consulta precio",
  escalar_negociacion: "Negociación",
  otro: "Otro",
};

const ESTADO_COLORS: Record<string, string> = {
  pendiente: "bg-accent-orange/15 text-accent-orange border-0",
  aprobada: "bg-green-900/30 text-green-300 border-0",
  rechazada: "bg-red-900/30 text-red-300 border-0",
  modificada: "bg-blue-900/30 text-blue-300 border-0",
  cancelada: "bg-surface text-text-muted border-0",
};

type AccionActiva = "aprobar" | "rechazar" | "modificar" | null;

export function SolicitudChatWindow({ solicitudId }: Props) {
  const { data: solicitud, mutate: mutateSolicitud } = useSolicitudDetalle(solicitudId);
  const { data: mensajesData, mutate: mutateMensajes } = useMensajesInternos(solicitudId);

  const [texto, setTexto] = useState("");
  const [sending, setSending] = useState(false);
  const [accionActiva, setAccionActiva] = useState<AccionActiva>(null);
  const [resolving, setResolving] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensajesData?.mensajes.length]);

  const handleSend = async () => {
    const contenido = texto.trim();
    if (!contenido || sending) return;
    setSending(true);
    try {
      await postMensajeInterno(solicitudId, contenido);
      setTexto("");
      await mutateMensajes();
    } catch {
      // silently ignore, SWR revalida
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleResolver = async (payload: ResolverSolicitudPayload) => {
    setResolving(true);
    try {
      await resolverSolicitud(solicitudId, payload);
      setAccionActiva(null);
      await mutateSolicitud();
      await mutateMensajes();
    } catch {
      // silently ignore
    } finally {
      setResolving(false);
    }
  };

  const isPendiente = solicitud?.estado === "pendiente";

  if (!solicitud) {
    return (
      <div className="flex-1 flex flex-col min-h-0">
        <div className="p-4 border-b border-border space-y-2 shrink-0">
          <Skeleton className="h-5 w-1/2" />
          <Skeleton className="h-4 w-1/3" />
        </div>
        <div className="flex-1 min-h-0 p-4 space-y-3 overflow-y-auto">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-2/3" style={{ marginLeft: i % 2 === 0 ? 0 : "auto" }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-border bg-surface shrink-0">
        <div className="flex items-start gap-2">
          <div className="flex-1 min-w-0">
            <p className="text-text-primary font-medium text-sm leading-snug">{solicitud.titulo}</p>
            {solicitud.cliente_nombre && (
              <p className="text-text-muted text-xs mt-0.5">{solicitud.cliente_nombre}</p>
            )}
          </div>
          <div className="flex items-center gap-1.5 shrink-0">
            <Badge className={cn("text-xs", TIPO_LABELS[solicitud.tipo] ? "bg-accent-purple/20 text-accent-purple border-0" : "bg-surface text-text-muted border-0")}>
              {TIPO_LABELS[solicitud.tipo] ?? solicitud.tipo}
            </Badge>
            <Badge className={cn("text-xs", ESTADO_COLORS[solicitud.estado] ?? "bg-surface text-text-muted border-0")}>
              {solicitud.estado}
            </Badge>
          </div>
        </div>
      </div>

      {/* Mensajes */}
      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-4 space-y-3">
        {!mensajesData ? (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-2/3" />
            ))}
          </div>
        ) : mensajesData.mensajes.length === 0 ? (
          <div className="flex items-center justify-center h-full text-text-muted text-sm">
            Sin mensajes aún. Responde o toma una acción.
          </div>
        ) : (
          mensajesData.mensajes.map((m) => (
            <div
              key={m.id}
              className={cn("flex", m.origen === "encargada" ? "justify-end" : "justify-start")}
            >
              <div
                className={cn(
                  "max-w-[75%] rounded-2xl px-4 py-2.5 text-sm",
                  m.tipo_contenido === "accion"
                    ? "bg-green-900/20 border border-green-800/30 text-green-300 text-xs font-medium"
                    : m.origen === "encargada"
                    ? "bg-accent-purple/80 text-white"
                    : "bg-surface text-text-primary"
                )}
              >
                <p className="whitespace-pre-wrap break-words">{m.contenido}</p>
                <p className={cn("text-xs mt-1 opacity-60", m.origen === "encargada" ? "text-right" : "")}>
                  {formatRelativeTime(m.created_at ?? "")}
                </p>
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Acciones (solo si pendiente) */}
      {isPendiente && !accionActiva && (
        <div className="px-4 py-3 border-t border-border bg-surface shrink-0">
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={() => setAccionActiva("aprobar")}
              className="bg-green-800 hover:bg-green-700 text-white gap-1.5"
            >
              <CheckCircle size={14} />
              Aprobar
            </Button>
            <Button
              size="sm"
              onClick={() => setAccionActiva("modificar")}
              className="bg-accent-purple hover:bg-accent-purple/80 text-white gap-1.5"
            >
              <Edit3 size={14} />
              Modificar precio
            </Button>
            <Button
              size="sm"
              onClick={() => setAccionActiva("rechazar")}
              variant="ghost"
              className="text-red-400 hover:text-red-300 hover:bg-red-900/20 gap-1.5"
            >
              <XCircle size={14} />
              Rechazar
            </Button>
          </div>
        </div>
      )}

      {/* Formulario de acción */}
      {accionActiva && (
        <div className="shrink-0">
          <PricingForm
            solicitud={solicitud}
            accion={accionActiva}
            onSubmit={handleResolver}
            onCancel={() => setAccionActiva(null)}
            isLoading={resolving}
          />
        </div>
      )}

      {/* Input de mensaje */}
      <div className="px-4 py-3 border-t border-border bg-surface shrink-0">
        <div className="flex gap-2 items-end">
          <textarea
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe un mensaje... (Enter para enviar)"
            rows={1}
            className="flex-1 bg-background border border-border rounded-xl px-3 py-2 text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:ring-1 focus:ring-accent-purple max-h-28 overflow-y-auto"
            style={{ minHeight: "38px" }}
          />
          <Button
            size="icon"
            onClick={handleSend}
            disabled={!texto.trim() || sending}
            className="bg-accent-purple hover:bg-accent-purple/80 text-white shrink-0 h-9 w-9"
          >
            <Send size={14} />
          </Button>
        </div>
      </div>
    </div>
  );
}
