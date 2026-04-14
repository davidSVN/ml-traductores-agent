"use client";

import type { Conversacion } from "@/lib/types";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

interface Props {
  conv: Conversacion;
  isSelected: boolean;
  onClick: () => void;
}

export function ConversationItem({ conv, isSelected, onClick }: Props) {
  const initials = (conv.nombre_temporal ?? conv.telefono_whatsapp ?? "?")
    .split(" ")
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-start gap-3 px-4 py-3 text-left transition-colors border-b border-border",
        isSelected ? "bg-accent-purple/10" : "hover:bg-surfaceHover"
      )}
    >
      {/* Avatar */}
      <div className="w-10 h-10 rounded-full bg-accent-purple/20 flex items-center justify-center shrink-0 text-accent-purple font-semibold text-sm">
        {initials}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className="text-text-primary text-sm font-medium truncate">
            {conv.nombre_temporal ?? conv.telefono_whatsapp ?? "Desconocido"}
          </p>
          <span className="text-text-muted text-xs shrink-0">
            {formatRelativeTime(conv.ultimo_mensaje_at)}
          </span>
        </div>

        {conv.cliente_nombre && (
          <p className="text-text-secondary text-xs truncate">{conv.cliente_nombre}</p>
        )}

        <div className="flex items-center justify-between mt-0.5">
          <p className="text-text-muted text-xs truncate max-w-[160px]">
            {conv.ultimo_mensaje_preview ?? "Sin mensajes"}
          </p>
          {conv.mensajes_no_leidos > 0 && (
            <Badge className="bg-accent-orange text-white text-xs h-5 min-w-5 px-1 rounded-full">
              {conv.mensajes_no_leidos}
            </Badge>
          )}
        </div>
      </div>
    </button>
  );
}
