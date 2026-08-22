import { cn } from "../../lib/cn";
import { mono, ShimmerLabel } from "./surfaces";

export function ThinkingIndicator({ label, className, ...props }) {
  return (
    <div
      data-slot="thinking-indicator"
      className={cn("flex items-center gap-2.5 text-sm text-tinta-suave", className)}
      {...props}
    >
      <span
        aria-hidden
        className="size-1.5 shrink-0 animate-pulse rounded-full bg-violeta"
      />
      <ShimmerLabel className="relative inline-block leading-none">
        {label}
      </ShimmerLabel>
    </div>
  );
}
