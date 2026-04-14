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
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { formatCurrency } from "@/lib/utils";
import type { Servicio } from "@/lib/types";

export function ServiciosTable() {
  const { data, isLoading } = useServicios();
  const servicios = (data?.data ?? []) as Servicio[];

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="border-border hover:bg-transparent">
            <TableHead className="text-text-muted">Nombre</TableHead>
            <TableHead className="text-text-muted">Categoría</TableHead>
            <TableHead className="text-text-muted">Idiomas</TableHead>
            <TableHead className="text-text-muted">Unidad</TableHead>
            <TableHead className="text-text-muted">Precio base</TableHead>
            <TableHead className="text-text-muted">Precio cliente</TableHead>
            <TableHead className="text-text-muted">Modalidad</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading ? (
            Array.from({ length: 6 }).map((_, i) => (
              <TableRow key={i} className="border-border">
                <TableCell colSpan={7}>
                  <Skeleton className="h-4 w-full" />
                </TableCell>
              </TableRow>
            ))
          ) : servicios.length === 0 ? (
            <TableRow className="border-border">
              <TableCell colSpan={7} className="text-center text-text-muted py-10">
                Sin servicios
              </TableCell>
            </TableRow>
          ) : (
            servicios.map((s) => (
              <TableRow key={s.id} className="border-border hover:bg-surfaceHover">
                <TableCell className="text-text-primary font-medium">{s.nombre}</TableCell>
                <TableCell>
                  <Badge variant="outline" className="border-border text-text-secondary text-xs capitalize">
                    {s.categoria}
                  </Badge>
                </TableCell>
                <TableCell className="text-text-secondary text-sm">
                  {s.idioma_origen} → {s.idioma_destino}
                </TableCell>
                <TableCell className="text-text-muted text-sm">{s.unidad_cobro}</TableCell>
                <TableCell className="text-text-secondary text-sm">{formatCurrency(s.precio_base)}</TableCell>
                <TableCell className="text-text-primary text-sm font-medium">{formatCurrency(s.precio_cliente)}</TableCell>
                <TableCell>
                  <Badge
                    className={
                      s.es_presencial
                        ? "bg-blue-900/30 text-blue-300 border-0 text-xs"
                        : "bg-green-900/30 text-green-300 border-0 text-xs"
                    }
                  >
                    {s.es_presencial ? "Presencial" : "Virtual"}
                  </Badge>
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
