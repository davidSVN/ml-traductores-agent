"use client";

import { CalendarCheck } from "lucide-react";
import { EventosTable } from "@/components/eventos-confirmados/EventosTable";

export default function EventosConfirmadosPage() {
  return (
    <div className="flex flex-col h-screen overflow-hidden">
      {/* Header */}
      <div className="px-6 py-5 border-b border-border bg-surface shrink-0">
        <div className="flex items-center gap-3">
          <CalendarCheck size={20} className="text-accent-purple" />
          <div>
            <h1 className="text-text-primary font-semibold text-base">Eventos confirmados</h1>
            <p className="text-text-muted text-xs mt-0.5">
              Cotizaciones aprobadas con detalle del evento y estado de facturación
            </p>
          </div>
        </div>
      </div>

      {/* Tabla */}
      <div className="flex-1 overflow-auto bg-background">
        <EventosTable />
      </div>
    </div>
  );
}
