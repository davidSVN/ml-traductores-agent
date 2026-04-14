import { SolicitudesTable } from "@/components/aprobaciones/SolicitudesTable";
import { Bell } from "lucide-react";

export default function AprobacionesPage() {
  return (
    <div className="p-6">
      <h1 className="text-text-primary text-xl font-bold mb-2">Aprobaciones</h1>

      <div className="flex items-start gap-3 bg-accent-orange/10 border border-accent-orange/20 rounded-lg px-4 py-3 mb-6">
        <Bell size={16} className="text-accent-orange mt-0.5 shrink-0" />
        <p className="text-text-secondary text-sm">
          Aquí aparecen las solicitudes que el agente escala para su revisión. Responda directamente al cliente por WhatsApp una vez revisada cada solicitud.
        </p>
      </div>

      <SolicitudesTable />
    </div>
  );
}
