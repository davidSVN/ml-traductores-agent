"use client";

import { useEffect, useRef } from "react";
import { useMensajes } from "@/lib/hooks/useMensajes";
import { patchLeer } from "@/lib/api";
import { MessageBubble } from "./MessageBubble";
import { EmptyChat } from "./EmptyChat";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Phone } from "lucide-react";

interface Props {
  convId: number | null;
}

export function ChatWindow({ convId }: Props) {
  const { data, isLoading } = useMensajes(convId);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (convId) {
      patchLeer(convId).catch(() => {});
    }
  }, [convId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [data?.mensajes?.length]);

  if (!convId) return <EmptyChat />;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border flex items-center justify-between">
        {isLoading ? (
          <Skeleton className="h-5 w-48" />
        ) : (
          <div>
            <p className="font-semibold text-text-primary">
              {data?.conversacion.nombre_temporal ?? data?.conversacion.telefono_whatsapp ?? "—"}
            </p>
            <p className="text-text-muted text-xs flex items-center gap-1 mt-0.5">
              <Phone size={11} />
              {data?.conversacion.telefono_whatsapp}
              {data?.conversacion.cliente_nombre && (
                <span className="ml-2 text-text-secondary">· {data.conversacion.cliente_nombre}</span>
              )}
            </p>
          </div>
        )}
        {data?.conversacion.estado && (
          <Badge
            variant="outline"
            className={
              data.conversacion.estado === "activa"
                ? "border-green-600 text-green-400"
                : "border-border text-text-muted"
            }
          >
            {data.conversacion.estado}
          </Badge>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-3">
        {isLoading ? (
          Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className={`flex ${i % 2 === 0 ? "justify-start" : "justify-end"}`}>
              <Skeleton className="h-12 w-48 rounded-2xl" />
            </div>
          ))
        ) : data?.mensajes.length === 0 ? (
          <p className="text-center text-text-muted text-sm py-8">Sin mensajes aún</p>
        ) : (
          data?.mensajes.map((msg) => <MessageBubble key={msg.id} msg={msg} />)
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input area — solo lectura */}
      <div className="px-6 py-4 border-t border-border">
        <div className="bg-surface rounded-xl px-4 py-3 text-text-muted text-sm">
          Vista de solo lectura — el agente responde automáticamente por WhatsApp
        </div>
      </div>
    </div>
  );
}
