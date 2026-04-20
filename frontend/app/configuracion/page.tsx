"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { User, Building2, Mail, CreditCard, FileText, Save } from "lucide-react";

const DEFAULT_INFO = {
  correo_oficial: "mltraductores@gmail.com",
  nit: "",
  banco: "",
  numero_cuenta: "",
  tipo_cuenta: "Ahorros",
  titular_cuenta: "",
  instrucciones_pago:
    "50% anticipo al confirmar el servicio. 50% al finalizar. Transferencia bancaria o consignación.",
};

export default function ConfiguracionPage() {
  const [info, setInfo] = useState(DEFAULT_INFO);
  const [saved, setSaved] = useState(false);

  function handleChange(field: keyof typeof DEFAULT_INFO, value: string) {
    setInfo((prev) => ({ ...prev, [field]: value }));
    setSaved(false);
  }

  function handleSave() {
    // Fase 1: solo UI local. En fase posterior conectar a endpoint backend.
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-text-primary text-xl font-bold">Configuración</h1>

      {/* Perfil de usuario */}
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

      {/* Datos oficiales de ML Traductores */}
      <Card className="bg-surface border-border p-6 max-w-2xl">
        <div className="flex items-center gap-3 mb-6">
          <FileText size={18} className="text-accent-purple" />
          <h2 className="text-text-primary font-semibold text-base">
            Datos Oficiales de ML Traductores
          </h2>
        </div>
        <p className="text-text-muted text-xs mb-6">
          Esta información se usa en los mensajes del agente y en las cotizaciones. Manténla actualizada.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* Correo oficial */}
          <div>
            <label className="text-text-muted text-xs block mb-1">Correo oficial</label>
            <div className="flex items-center gap-2 bg-background border border-border rounded-md px-3 py-2">
              <Mail size={14} className="text-text-muted shrink-0" />
              <input
                type="email"
                value={info.correo_oficial}
                onChange={(e) => handleChange("correo_oficial", e.target.value)}
                className="bg-transparent text-text-primary text-sm outline-none w-full"
                placeholder="correo@empresa.com"
              />
            </div>
          </div>

          {/* NIT */}
          <div>
            <label className="text-text-muted text-xs block mb-1">NIT</label>
            <div className="flex items-center gap-2 bg-background border border-border rounded-md px-3 py-2">
              <Building2 size={14} className="text-text-muted shrink-0" />
              <input
                type="text"
                value={info.nit}
                onChange={(e) => handleChange("nit", e.target.value)}
                className="bg-transparent text-text-primary text-sm outline-none w-full"
                placeholder="900123456-7"
              />
            </div>
          </div>

          {/* Banco */}
          <div>
            <label className="text-text-muted text-xs block mb-1">Nombre del banco</label>
            <div className="flex items-center gap-2 bg-background border border-border rounded-md px-3 py-2">
              <CreditCard size={14} className="text-text-muted shrink-0" />
              <input
                type="text"
                value={info.banco}
                onChange={(e) => handleChange("banco", e.target.value)}
                className="bg-transparent text-text-primary text-sm outline-none w-full"
                placeholder="Bancolombia, Davivienda..."
              />
            </div>
          </div>

          {/* Número de cuenta */}
          <div>
            <label className="text-text-muted text-xs block mb-1">Número de cuenta</label>
            <div className="flex items-center gap-2 bg-background border border-border rounded-md px-3 py-2">
              <CreditCard size={14} className="text-text-muted shrink-0" />
              <input
                type="text"
                value={info.numero_cuenta}
                onChange={(e) => handleChange("numero_cuenta", e.target.value)}
                className="bg-transparent text-text-primary text-sm outline-none w-full"
                placeholder="000-000000-00"
              />
            </div>
          </div>

          {/* Tipo de cuenta */}
          <div>
            <label className="text-text-muted text-xs block mb-1">Tipo de cuenta</label>
            <div className="flex items-center gap-2 bg-background border border-border rounded-md px-3 py-2">
              <CreditCard size={14} className="text-text-muted shrink-0" />
              <select
                value={info.tipo_cuenta}
                onChange={(e) => handleChange("tipo_cuenta", e.target.value)}
                className="bg-transparent text-text-primary text-sm outline-none w-full"
              >
                <option value="Ahorros">Ahorros</option>
                <option value="Corriente">Corriente</option>
              </select>
            </div>
          </div>

          {/* Titular de la cuenta */}
          <div>
            <label className="text-text-muted text-xs block mb-1">Titular de la cuenta</label>
            <div className="flex items-center gap-2 bg-background border border-border rounded-md px-3 py-2">
              <User size={14} className="text-text-muted shrink-0" />
              <input
                type="text"
                value={info.titular_cuenta}
                onChange={(e) => handleChange("titular_cuenta", e.target.value)}
                className="bg-transparent text-text-primary text-sm outline-none w-full"
                placeholder="Nombre del titular"
              />
            </div>
          </div>

          {/* Instrucciones de pago — full width */}
          <div className="md:col-span-2">
            <label className="text-text-muted text-xs block mb-1">Instrucciones de pago</label>
            <textarea
              value={info.instrucciones_pago}
              onChange={(e) => handleChange("instrucciones_pago", e.target.value)}
              rows={3}
              className="w-full bg-background border border-border rounded-md px-3 py-2 text-text-primary text-sm outline-none resize-none"
              placeholder="Condiciones y forma de pago para incluir en cotizaciones..."
            />
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <p className="text-text-muted text-xs">
            En fase 4 estos datos se sincronizarán automáticamente con las plantillas de cotización.
          </p>
          <button
            onClick={handleSave}
            className="flex items-center gap-2 bg-accent-purple text-white text-sm font-medium px-4 py-2 rounded-md hover:bg-accent-purple/90 transition-colors"
          >
            <Save size={14} />
            {saved ? "Guardado" : "Guardar"}
          </button>
        </div>
      </Card>
    </div>
  );
}
