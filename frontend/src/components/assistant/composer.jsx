import { MicIcon, SquareIcon } from "lucide-react";
import { cn } from "../../lib/cn";
import { ghostButton, inkButton, mono, ShimmerLabel } from "./surfaces";

const BARS = Array.from({ length: 14 }, (_, i) => i);

function barHeight(bar, tick) {
  return 5 + Math.abs(Math.sin(bar * 1.35 + tick * 0.55)) * 13;
}

export function ComposerVoice({ recording, seconds, className, ...props }) {
  return (
    <div
      data-slot="composer-voice"
      data-recording={recording || undefined}
      className={cn("flex min-h-11 items-center gap-3 ps-3", className)}
      {...props}
    >
      {recording && (
        <span aria-hidden className="size-1.5 animate-pulse rounded-full bg-violeta" />
      )}
      <div className="flex h-6 items-center gap-[3px]" aria-hidden>
        {BARS.map((bar) => (
          <span
            key={bar}
            className={cn(
              "w-0.5 rounded-full transition-[height,background-color] duration-150",
              recording ? "bg-violeta/70" : "bg-linea",
            )}
            style={{ height: recording ? barHeight(bar, seconds * 10) : 3 }}
          />
        ))}
      </div>
      {recording ? (
        <span className={cn(mono, "tabular-nums text-tinta-suave")}>
          0:{String(seconds).padStart(2, "0")}
        </span>
      ) : (
        <ShimmerLabel className="relative text-[13px] text-tinta-suave">
          Transcribiendo
        </ShimmerLabel>
      )}
    </div>
  );
}

export function ComposerVoiceButton({ active, className, ...props }) {
  return (
    <button
      type="button"
      aria-label={active ? "Detener grabación" : "Dictar"}
      data-slot="composer-voice-button"
      className={cn(
        active
          ? cn(inkButton, "flex size-8 items-center justify-center rounded-full")
          : cn(ghostButton, "size-8"),
        className,
      )}
      {...props}
    >
      {active ? (
        <SquareIcon className="size-3 fill-current" />
      ) : (
        <MicIcon className="size-4" />
      )}
    </button>
  );
}
