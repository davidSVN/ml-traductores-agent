"use client";

import { useState } from "react";
import { SolicitudList } from "@/components/aprobaciones/SolicitudList";
import { SolicitudChatWindow } from "@/components/aprobaciones/SolicitudChatWindow";
import { SolicitudInfoPanel } from "@/components/aprobaciones/SolicitudInfoPanel";
import { MessageSquareDashed } from "lucide-react";

export default function AprobacionesPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex h-screen overflow-hidden">

      {/* Columna 1 — Lista de solicitudes (~280px) */}
      <div className={`${selectedId !== null ? "hidden" : "flex"} md:flex flex-col w-full md:w-72 shrink-0`}>
        <SolicitudList selectedId={selectedId} onSelect={(id) => { setSelectedId(id); }} />
      </div>

      {/* Columna 2 — Chat agente↔encargada (flex-1) */}
      <div className={`${selectedId !== null ? "flex" : "hidden"} md:flex flex-1 flex-col overflow-hidden border-l border-border`}>
        {selectedId ? (
          <>
            {/* Botón volver mobile */}
            <div className="md:hidden px-4 py-2 border-b border-border bg-surface shrink-0">
              <button
                onClick={() => setSelectedId(null)}
                className="text-text-muted text-sm hover:text-text-primary"
              >
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

      {/* Columna 3 — Info: cliente, contacto, cotización (~288px) */}
      {selectedId && (
        <div className="hidden md:block">
          <SolicitudInfoPanel solicitudId={selectedId} />
        </div>
      )}

    </div>
  );
}
