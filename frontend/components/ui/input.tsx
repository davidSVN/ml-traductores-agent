import * as React from "react";
import { cn } from "@/lib/utils";

export type InputProps = React.InputHTMLAttributes<HTMLInputElement>;

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        ref={ref}
        className={cn(
          "flex h-9 w-full rounded-lg border border-[#2a2a36] bg-[#1a1a22] px-3 py-1 text-sm text-[#f0f0f5] placeholder:text-[#555568] outline-none focus:border-[#7c5cbf] disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
          className
        )}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
