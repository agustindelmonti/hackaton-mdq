import { CheckIcon, ChevronRightIcon } from "lucide-react";
import { cn } from "../../lib/cn";
import { field, mono, ShimmerLabel, SwapLabel } from "./surfaces";

export function ToolCall({
  label,
  activeLabel,
  query,
  request,
  result,
  running,
  open,
  onOpenChange,
  className,
}) {
  return (
    <div data-slot="tool-call" className={cn("w-full max-w-sm", className)}>
      <button
        type="button"
        onClick={() => onOpenChange(!open)}
        className="group/trigger flex w-full items-center gap-2 rounded-md py-1 text-left text-[13.5px] text-tinta-suave outline-none transition-colors hover:text-tinta"
      >
        <ChevronRightIcon
          className={cn(
            "size-3.5 shrink-0 opacity-60 transition-transform duration-200",
            open && "rotate-90",
          )}
        />
        <SwapLabel active={running ? 0 : 1} className="text-start">
          <ShimmerLabel active={running} className="relative inline-block leading-none">
            {activeLabel}
          </ShimmerLabel>
          <>{label}</>
        </SwapLabel>
        {query && (
          <span className={cn(mono, "rounded-md bg-papel-hondo px-1.5 py-0.5 text-tinta-suave")}>
            {query}
          </span>
        )}
        <span className="ms-auto flex w-4 items-center justify-end">
          {!running && <CheckIcon className="size-3.5 text-salvia" />}
        </span>
      </button>
      {open && (
        <div className={cn(field, "mt-2 overflow-hidden rounded-2xl text-xs")}>
          <div className="px-3.5 pt-2.5 pb-2">
            <p className={cn(mono, "mb-1 text-tinta-suave")}>Request</p>
            <p className="font-mono text-tinta-suave">{request}</p>
          </div>
          <div className="mx-3.5 h-px bg-linea" />
          <div className="px-3.5 pt-2 pb-2.5">
            <p className={cn(mono, "mb-1 text-tinta-suave")}>Result</p>
            <p className="whitespace-pre-wrap text-tinta">{result}</p>
          </div>
        </div>
      )}
    </div>
  );
}
