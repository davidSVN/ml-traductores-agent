"use client";

import { useStats } from "@/lib/hooks/useStats";
import { StatCard } from "./StatCard";
import {
  MessageSquare,
  FileText,
  DollarSign,
  Bell,
  Users,
  TrendingUp,
} from "lucide-react";
import { formatCurrency } from "@/lib/utils";

export function MetricasGrid() {
  const { data, isLoading } = useStats();

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <StatCard
        label="Conversaciones activas"
        value={data?.conversaciones_activas ?? 0}
        icon={MessageSquare}
        isLoading={isLoading}
      />
      <StatCard
        label="Cotizaciones totales"
        value={data?.cotizaciones_total ?? 0}
        icon={FileText}
        isLoading={isLoading}
      />
      <StatCard
        label="Cotizaciones este mes"
        value={data?.cotizaciones_este_mes ?? 0}
        icon={TrendingUp}
        isLoading={isLoading}
        accent="orange"
      />
      <StatCard
        label="Ingresos totales"
        value={formatCurrency(data?.ingresos_total ?? 0)}
        icon={DollarSign}
        isLoading={isLoading}
        accent="orange"
      />
      <StatCard
        label="Ingresos este mes"
        value={formatCurrency(data?.ingresos_este_mes ?? 0)}
        icon={DollarSign}
        isLoading={isLoading}
      />
      <StatCard
        label="Solicitudes pendientes"
        value={data?.solicitudes_pendientes ?? 0}
        icon={Bell}
        isLoading={isLoading}
        accent="orange"
      />
    </div>
  );
}
