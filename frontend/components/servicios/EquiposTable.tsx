"use client";

import { useServicios } from "@/lib/hooks/useServicios";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/utils";
import type { Equipo } from "@/lib/types";

export function EquiposTable() {
  const { data, isLoading } = useServicios("equipo");
  const equipos = (data?.data ?? []) as Equipo[];

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="border-border hover:bg-transparent">
            <TableHead className="text-text-muted">Tipo de equipo</TableHead>
            <TableHead className="text-text-muted">Cantidad</TableHead>
            <TableHead className="text-text-muted">Días</TableHead>
            <TableHead className="text-text-muted">Precio proveedor</TableHead>
            <TableHead className="text-text-muted">Precio cliente</TableHead>
            <TableHead className="text-text-muted">Descripción</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <TableRow key={i} className="border-border">
                <TableCell colSpan={6}>
                  <Skeleton className="h-4 w-full" />
                </TableCell>
              </TableRow>
            ))
          ) : equipos.length === 0 ? (
            <TableRow className="border-border">
              <TableCell colSpan={6} className="text-center text-text-muted py-10">
                Sin equipos
              </TableCell>
            </TableRow>
          ) : (
            equipos.map((e) => (
              <TableRow key={e.id} className="border-border hover:bg-surfaceHover">
                <TableCell className="text-text-primary font-medium">{e.tipo_equipo}</TableCell>
                <TableCell className="text-text-secondary text-sm">
                  {e.cantidad_min}–{e.cantidad_max}
                </TableCell>
                <TableCell className="text-text-muted text-sm">{e.num_dias ?? "—"}</TableCell>
                <TableCell className="text-text-secondary text-sm">{formatCurrency(e.precio_proveedor)}</TableCell>
                <TableCell className="text-text-primary text-sm font-medium">{formatCurrency(e.precio_cliente)}</TableCell>
                <TableCell className="text-text-muted text-sm">{e.descripcion ?? "—"}</TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
