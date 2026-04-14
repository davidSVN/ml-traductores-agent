"use client";

import { useState } from "react";
import { useConversaciones } from "@/lib/hooks/useConversaciones";
import { ConversationItem } from "./ConversationItem";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Search } from "lucide-react";

interface Props {
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export function ConversationList({ selectedId, onSelect }: Props) {
  const [search, setSearch] = useState("");
  const [estado, setEstado] = useState<string | undefined>(undefined);

  const { data, isLoading } = useConversaciones({ search, estado });

  return (
    <div className="flex flex-col h-full border-r border-border w-80 shrink-0">
      {/* Header */}
      <div className="px-4 py-4 border-b border-border space-y-3">
        <h2 className="text-text-primary font-semibold">Conversaciones</h2>
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
          <Input
            placeholder="Buscar..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 bg-surface border-border text-text-primary placeholder:text-text-muted text-sm h-9"
          />
        </div>
        <Tabs defaultValue="todas" onValueChange={(v) => setEstado(v === "todas" ? undefined : v)}>
          <TabsList className="bg-surface w-full">
            <TabsTrigger value="todas" className="flex-1 text-xs">Todas</TabsTrigger>
            <TabsTrigger value="activa" className="flex-1 text-xs">Activas</TabsTrigger>
            <TabsTrigger value="cerrada" className="flex-1 text-xs">Cerradas</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3 px-4 py-3 border-b border-border">
              <Skeleton className="w-10 h-10 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-48" />
              </div>
            </div>
          ))
        ) : data?.data.length === 0 ? (
          <p className="text-center text-text-muted text-sm py-12">Sin conversaciones</p>
        ) : (
          data?.data.map((conv) => (
            <ConversationItem
              key={conv.id}
              conv={conv}
              isSelected={conv.id === selectedId}
              onClick={() => onSelect(conv.id)}
            />
          ))
        )}
      </div>

      {/* Pagination info */}
      {data && (
        <div className="px-4 py-2 border-t border-border">
          <p className="text-text-muted text-xs">{data.meta.total} conversaciones</p>
        </div>
      )}
    </div>
  );
}
