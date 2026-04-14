"use client";

import { useState } from "react";
import { useClientes } from "@/lib/hooks/useClientes";
import { getContactos } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ChevronDown, ChevronRight, Search } from "lucide-react";
import type { Contacto } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function ClientesTable() {
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [contactosMap, setContactosMap] = useState<Record<number, Contacto[]>>({});

  const { data, isLoading } = useClientes({ search });

  async function handleExpand(clienteId: number) {
    if (expandedId === clienteId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(clienteId);
    if (!contactosMap[clienteId]) {
      const res = await getContactos(clienteId);
      setContactosMap((prev) => ({ ...prev, [clienteId]: res.data }));
    }
  }

  return (
    <div className="space-y-4">
      <div className="relative w-72">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
        <Input
          placeholder="Buscar empresa..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-8 bg-surface border-border text-text-primary placeholder:text-text-muted text-sm h-9"
        />
      </div>

      <div className="rounded-lg border border-border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="border-border hover:bg-transparent">
              <TableHead className="text-text-muted w-8"></TableHead>
              <TableHead className="text-text-muted">Empresa</TableHead>
              <TableHead className="text-text-muted">Tipo</TableHead>
              <TableHead className="text-text-muted">Ciudad</TableHead>
              <TableHead className="text-text-muted">Nivel</TableHead>
              <TableHead className="text-text-muted">Servicios</TableHead>
              <TableHead className="text-text-muted">Última cotización</TableHead>
              <TableHead className="text-text-muted">Contactos</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 8 }).map((_, i) => (
                <TableRow key={i} className="border-border">
                  <TableCell colSpan={8}>
                    <Skeleton className="h-4 w-full" />
                  </TableCell>
                </TableRow>
              ))
            ) : data?.data.length === 0 ? (
              <TableRow className="border-border">
                <TableCell colSpan={8} className="text-center text-text-muted py-10">
                  Sin clientes
                </TableCell>
              </TableRow>
            ) : (
              data?.data.map((c) => (
                <>
                  <TableRow
                    key={c.id}
                    className="border-border hover:bg-surfaceHover cursor-pointer"
                    onClick={() => handleExpand(c.id)}
                  >
                    <TableCell>
                      {expandedId === c.id ? (
                        <ChevronDown size={14} className="text-text-muted" />
                      ) : (
                        <ChevronRight size={14} className="text-text-muted" />
                      )}
                    </TableCell>
                    <TableCell className="text-text-primary font-medium">
                      {c.nombre_empresa ?? "—"}
                      {c.es_recurrente && (
                        <Badge className="ml-2 bg-accent-purple/20 text-accent-purple text-xs border-0">
                          Recurrente
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-text-secondary text-sm">{c.tipo_cliente ?? "—"}</TableCell>
                    <TableCell className="text-text-secondary text-sm">{c.ciudad ?? "—"}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="border-border text-text-secondary text-xs capitalize">
                        {c.nivel_precio ?? "nuevo"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-text-secondary text-sm">{c.servicios_confirmados ?? 0}</TableCell>
                    <TableCell className="text-text-secondary text-sm">{formatDate(c.ultima_cotizacion)}</TableCell>
                    <TableCell className="text-text-secondary text-sm">{c.contactos_count}</TableCell>
                  </TableRow>

                  {expandedId === c.id && (
                    <TableRow key={`${c.id}-contacts`} className="border-border bg-surface/50">
                      <TableCell colSpan={8} className="py-3 px-8">
                        {contactosMap[c.id] ? (
                          <div className="space-y-1">
                            {contactosMap[c.id].map((ct) => (
                              <div key={ct.id} className="flex items-center gap-4 text-sm">
                                <span className="text-text-primary font-medium w-40">{ct.nombre_completo}</span>
                                <span className="text-text-muted">{ct.cargo ?? "—"}</span>
                                <span className="text-text-secondary">{ct.email ?? "—"}</span>
                                <span className="text-text-muted">{ct.telefono ?? "—"}</span>
                                {ct.es_principal && (
                                  <Badge className="bg-accent-purple/15 text-accent-purple text-xs border-0">Principal</Badge>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : (
                          <Skeleton className="h-4 w-64" />
                        )}
                      </TableCell>
                    </TableRow>
                  )}
                </>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {data && (
        <p className="text-text-muted text-xs">{data.meta.total} clientes en total</p>
      )}
    </div>
  );
}
