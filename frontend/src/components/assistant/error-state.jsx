import { CircleAlertIcon, RefreshCwIcon } from "lucide-react";
import { cn } from "../../lib/cn";
import { ShimmerLabel } from "./surfaces";

export function ErrorState({ title, detail, retrying, onRetry, className, ...props }) {
  if (retrying) {
    return (
      <div
        data-slot="error-state"
        role="status"
        className={cn(
          "flex w-full max-w-sm items-center gap-2.5 text-sm",
          className,
        )}
        {...props}
      >
        <RefreshCwIcon className="size-3.5 shrink-0 animate-spin text-tinta-suave" />
        <ShimmerLabel className="relative inline-block text-tinta-suave">
          Reintentando
        </ShimmerLabel>
      </div>
    );
  }

  return (
    <div
      data-slot="error-state"
      role="alert"
      className={cn(
        "flex w-full max-w-sm items-start gap-2.5 rounded-2xl bg-rojo/10 px-4 py-3 text-sm",
        className,
      )}
      {...props}
    >
      <CircleAlertIcon className="mt-0.5 size-4 shrink-0 text-rojo" />
      <div>
        <p className="font-medium text-rojo">{title}</p>
        <p className="mt-0.5 text-[13px] leading-snug text-rojo-hondo/80">{detail}</p>
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="ms-auto flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium text-rojo transition-colors hover:bg-rojo/10"
      >
        <RefreshCwIcon className="size-3" />
        Reintentar
      </button>
    </div>
  );
}
