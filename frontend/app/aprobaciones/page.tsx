"use client";

import { useState } from "react";
import { SolicitudList } from "@/components/aprobaciones/SolicitudList";
import { SolicitudChatWindow } from "@/components/aprobaciones/SolicitudChatWindow";
import { MessageSquareDashed } from "lucide-react";

export default function AprobacionesPage() {
  const [selectedId, setSelectedId] = useState<number | null>(null);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Panel izquierdo: lista */}
      <div className={`${selectedId !== null ? "hidden" : "flex"} md:flex flex-col w-full md:w-80 md:shrink-0`}>
        <SolicitudList selectedId={selectedId} onSelect={setSelectedId} />
      </div>

      {/* Panel derecho: chat */}
      <div className={`${selectedId !== null ? "flex" : "hidden"} md:flex flex-1 flex-col overflow-hidden`}>
        {selectedId ? (
          <>
            {/* Botón volver en mobile */}
            <div className="md:hidden px-4 py-2 border-b border-border bg-surface shrink-0">
              <button
                onClick={() => setSelectedId(null)}
                className="text-text-muted text-sm hover:text-text-primary"
              >
                ← Volver a la lista
              </button>
            </div>
            <SolicitudChatWindow solicitudId={selectedId} />
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-text-muted gap-3">
            <MessageSquareDashed size={40} className="opacity-30" />
            <p className="text-sm">Selecciona una solicitud para ver el detalle</p>
          </div>
        )}
      </div>
    </div>
  );
}
