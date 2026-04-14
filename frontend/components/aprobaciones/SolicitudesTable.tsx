"use client";

import { useSolicitudes } from "@/lib/hooks/useSolicitudes";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { formatRelativeTime } from "@/lib/utils";
import { useState } from "react";

const TIPO_LABELS: Record<string, string> = {
  descuento_especial: "Descuento especial",
  consulta_precio: "Consulta precio",
  atencion_humana: "Atención humana",
  servicio_no_catalogado: "Servicio nuevo",
};

export function SolicitudesTable() {
  const [estado, setEstado] = useState<string | undefined>("pendiente");
  const { data, isLoading } = useSolicitudes(estado);

  return (
    <div className="space-y-4">
      <Tabs defaultValue="pendiente" onValueChange={(v) => setEstado(v === "todas" ? undefined : v)}>
        <TabsList className="bg-surface">
          <TabsTrigger value="pendiente">Pendientes</TabsTrigger>
          <TabsTrigger value="resuelta">Resueltas</TabsTrigger>
          <TabsTrigger value="todas">Todas</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-text-muted">Tipo</TableHead>
              <TableHead className="text-text-muted">Título</TableHead>
              <TableHead className="text-text-muted">Cliente</TableHead>
              <TableHead className="text-text-muted">Cotización</TableHead>
              <TableHead className="text-text-muted">Prioridad</TableHead>
              <TableHead className="text-text-muted">Estado</TableHead>
              <TableHead className="text-text-muted">Fecha</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i} className="border-border">
                  <TableCell colSpan={7}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.data.length === 0 ? (
              <TableRow className="border-border">
                <TableCell colSpan={7} className="text-center text-text-muted py-10">
                  Sin solicitudes {estado === "pendiente" ? "pendientes" : ""}
                </TableCell>
              </TableRow>
            ) : (
              data?.data.map((s) => (
                <TableRow key={s.id} className="border-border hover:bg-surfaceHover">
                  <TableCell>
                    <Badge variant="outline" className="border-border text-text-secondary text-xs">
                      {TIPO_LABELS[s.tipo] ?? s.tipo}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-text-primary text-sm">{s.titulo}</TableCell>
                  <TableCell className="text-text-secondary text-sm">{s.cliente_nombre ?? "—"}</TableCell>
                  <TableCell className="text-text-muted text-xs font-mono">{s.numero_cotizacion ?? "—"}</TableCell>
                  <TableCell>
                    <Badge
                      className={
                        s.prioridad === "alta"
                          ? "bg-red-900/30 text-red-300 border-0 text-xs"
                          : "bg-surface text-text-muted border-0 text-xs"
                      }
                    >
                      {s.prioridad ?? "normal"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        s.estado === "pendiente"
                          ? "bg-accent-orange/15 text-accent-orange border-0 text-xs"
                          : "bg-green-900/30 text-green-300 border-0 text-xs"
                      }
                    >
                      {s.estado}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-text-muted text-xs">{formatRelativeTime(s.created_at)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
