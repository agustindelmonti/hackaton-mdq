import { cn } from "../../lib/cn";

export const field = "bg-papel-hondo";
export const mono = "font-mono text-[11px] tracking-tight tabular-nums";
export const inkButton =
  "bg-violeta text-crema transition-[opacity,scale] duration-150 hover:bg-violeta-hondo active:scale-[0.96]";
export const ghostButton =
  "flex items-center justify-center rounded-full text-tinta-suave outline-none transition-colors hover:bg-papel-hondo hover:text-tinta";

export function ShimmerLabel({ active = true, className, ...props }) {
  return (
    <span
      className={cn(active && "animate-pulse", className)}
      {...props}
    />
  );
}

export function SwapLabel({ active, children, className }) {
  return (
    <span className={cn("relative inline-grid", className)}>
      <span
        className={cn(
          "col-start-1 row-start-1 transition-opacity duration-300",
          active === 0 ? "opacity-100" : "pointer-events-none opacity-0",
        )}
      >
        {children[0]}
      </span>
      <span
        className={cn(
          "col-start-1 row-start-1 transition-opacity duration-300",
          active === 1 ? "opacity-100" : "pointer-events-none opacity-0",
        )}
      >
        {children[1]}
      </span>
    </span>
  );
}
