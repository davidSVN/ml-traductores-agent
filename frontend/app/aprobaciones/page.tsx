"use client";

import { useState } from "react";
import { SolicitudList } from "@/components/aprobaciones/SolicitudList";
import { SolicitudChatWindow } from "@/components/aprobaciones/SolicitudChatWindow";
import { SolicitudInfoPanel } from "@/components/aprobaciones/SolicitudInfoPanel";
import { MessageSquareDashed } from "lucide-react";

export default function AprobacionesPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex h-screen overflow-hidden bg-background">

      {/* Col 1 — Lista (siempre visible en md+, oculta en mobile si hay chat) */}
      <div className={`
        ${selectedId ? "hidden md:flex" : "flex"}
        flex-col w-full md:w-72 shrink-0 border-r border-border
      `}>
        <SolicitudList selectedId={selectedId} onSelect={setSelectedId} />
      </div>

      {/* Col 2 — Chat (flex-1, sin bordes propios) */}
      <div className={`
        ${selectedId ? "flex" : "hidden md:flex"}
        flex-col flex-1 min-w-0 overflow-hidden
      `}>
        {selectedId ? (
          <>
            {/* Volver — solo mobile */}
            <div className="md:hidden px-4 py-2 border-b border-border bg-surface shrink-0">
              <button onClick={() => setSelectedId(null)} className="text-text-muted text-sm hover:text-text-primary">
                ← Volver
              </button>
            </div>
            <SolicitudChatWindow solicitudId={selectedId} />
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-text-muted gap-3">
            <MessageSquareDashed size={40} className="opacity-30" />
            <p className="text-sm">Selecciona una solicitud</p>
          </div>
        )}
      </div>

      {/* Col 3 — Info panel (solo md+, solo cuando hay selección) */}
      {selectedId && (
        <div className="hidden md:flex flex-col w-72 shrink-0 border-l border-border">
          <SolicitudInfoPanel solicitudId={selectedId} />
        </div>
      )}

    </div>
  );
}
