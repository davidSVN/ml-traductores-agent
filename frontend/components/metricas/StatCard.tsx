import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string | number;
  icon: LucideIcon;
  isLoading?: boolean;
  accent?: "purple" | "orange";
}

export function StatCard({ label, value, icon: Icon, isLoading, accent = "purple" }: Props) {
  return (
    <Card className="bg-surface border-border p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-text-muted text-xs mb-1">{label}</p>
          {isLoading ? (
            <Skeleton className="h-7 w-24" />
          ) : (
            <p className="text-text-primary text-2xl font-bold">{value}</p>
          )}
        </div>
        <div
          className={`w-10 h-10 rounded-lg flex items-center justify-center ${
            accent === "orange" ? "bg-accent-orange/15" : "bg-accent-purple/15"
          }`}
        >
          <Icon
            size={20}
            className={accent === "orange" ? "text-accent-orange" : "text-accent-purple"}
          />
        </div>
      </div>
    </Card>
  );
}
