"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import type { ResolverSolicitudPayload } from "@/lib/types";

interface Props {
  accion: "aprobar" | "rechazar";
  onSubmit: (payload: ResolverSolicitudPayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export function PricingForm({ accion, onSubmit, onCancel, isLoading }: Props) {
  const [respuesta, setRespuesta] = useState("");

  const handleSubmit = async () => {
    await onSubmit({ accion, respuesta: respuesta || undefined });
  };

  const accionLabel = { aprobar: "Confirmar aprobación", rechazar: "Confirmar rechazo" }[accion];
  const accionColor = {
    aprobar: "bg-green-700 hover:bg-green-600 text-white",
    rechazar: "bg-red-800 hover:bg-red-700 text-white",
  }[accion];

  const placeholder = accion === "aprobar"
    ? "Nota para el cliente (opcional)..."
    : "Motivo del rechazo (opcional)...";

  return (
    <div className="border-t border-border bg-background p-4 space-y-3">
      <textarea
        value={respuesta}
        onChange={(e) => setRespuesta(e.target.value)}
        placeholder={placeholder}
        rows={2}
        className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted resize-none focus:outline-none focus:ring-1 focus:ring-accent-purple"
      />
      <div className="flex gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={onCancel}
          disabled={isLoading}
          className="text-text-muted hover:text-text-primary"
        >
          Cancelar
        </Button>
        <Button
          size="sm"
          onClick={handleSubmit}
          disabled={isLoading}
          className={accionColor}
        >
          {isLoading ? "Guardando..." : accionLabel}
        </Button>
      </div>
    </div>
  );
}
