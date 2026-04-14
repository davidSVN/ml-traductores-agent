import { MetricasGrid } from "@/components/metricas/MetricasGrid";

export default function MetricasPage() {
  return (
    <div className="p-6">
      <h1 className="text-text-primary text-xl font-bold mb-6">Métricas</h1>
      <MetricasGrid />
    </div>
  );
}
