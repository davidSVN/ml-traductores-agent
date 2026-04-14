import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline";
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
        variant === "outline"
          ? "border border-[#2a2a36] text-[#8888aa]"
          : "bg-[#7c5cbf]/20 text-[#7c5cbf]",
        className
      )}
      {...props}
    />
  );
}

export { Badge };
