import { Card } from "@/components/ui/card";
import { User, Building2, Mail } from "lucide-react";

export default function ConfiguracionPage() {
  return (
    <div className="p-6">
      <h1 className="text-text-primary text-xl font-bold mb-6">Configuración</h1>

      <Card className="bg-surface border-border p-6 max-w-md">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-14 h-14 rounded-full bg-accent-purple/20 flex items-center justify-center text-accent-purple font-bold text-xl">
            ML
          </div>
          <div>
            <p className="text-text-primary font-semibold text-lg">María Luisa Trujillo</p>
            <p className="text-text-secondary text-sm">Directora Comercial</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <Building2 size={16} className="text-text-muted" />
            <div>
              <p className="text-text-muted text-xs">Empresa</p>
              <p className="text-text-primary text-sm">ML Traductores</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <User size={16} className="text-text-muted" />
            <div>
              <p className="text-text-muted text-xs">Rol</p>
              <p className="text-text-primary text-sm">Administradora del panel</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Mail size={16} className="text-text-muted" />
            <div>
              <p className="text-text-muted text-xs">Canal del agente</p>
              <p className="text-text-primary text-sm">WhatsApp Business API</p>
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-border">
          <p className="text-text-muted text-xs">
            Panel v1.0 · Autenticación y configuración avanzada disponibles en fase 4.
          </p>
        </div>
      </Card>
    </div>
  );
}
