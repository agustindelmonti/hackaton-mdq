import { useId, useState } from "react";
import { cn } from "../../lib/cn";
import { useT } from "../../lib/i18n";
import { floating, mono } from "./surfaces";

// ============================================================================
// ConfidenceMarker — la otra mitad del patrón "Confidence Indicators", junto
// a ../ConfidenceIndicator.jsx (ver .claude/skills/confidence-indicators/).
// Ese componente marca UN ítem entero (una tarjeta, una hipótesis); este
// marca TRAMOS adentro de un texto largo — la respuesta de Ángela, un
// párrafo de análisis — sin obligar a partir la prosa en tarjetas.
//
// Adaptado del "Elements" de assistant-ui (assistant-ui.com/elements/
// confidence-marker), con tres cambios sobre el original:
//
//   1. Paleta de la casa en vez de emerald/amber/red: salvia/oro/rojo, la
//      MISMA terna que usa ConfidenceIndicator para high/medium/low — dos
//      componentes del mismo patrón no pueden usar dos idiomas de color.
//   2. Soporte táctil. El original es hover-only (mouseenter/leave +
//      focus/blur): en un celu, dentro de una cámara a 4°C con guantes, eso
//      no dispara nunca. Achica a tap-para-fijar: tocar una claim la deja
//      fijada hasta tocar otra o tocar afuera.
//   3. Uso no controlado por default. El original exige que el padre le dé
//      `hoveredId`/`onHover` — sin eso, ninguna claim reacciona nunca (el
//      botón dispara el evento, pero no hay estado que lo escuche). Acá
//      ambas props son opcionales: sin ellas, el componente lleva su propio
//      estado; con ellas, el padre manda (por ej. para sincronizar con un
//      panel de evidencia aparte).
//
// LAS CLAIMS LAS DECIDE EL BACKEND, NUNCA EL MODELO SOLO. Igual que
// ConfidenceIndicator: un LLM autocalificando su propia certeza oración por
// oración no está calibrado y engaña sistemáticamente (ver "cuándo NO usar"
// en la skill). `basis` tiene que apuntar a algo verificable — un número de
// movimiento, una nota, un conteo — no a "el modelo dice que sí".
// ============================================================================

const UNDERLINE = {
  grounded: "decoration-salvia/50",
  inferred: "decoration-oro/60",
  uncertain: "decoration-rojo/50 decoration-dotted",
};

const DOT = {
  grounded: "bg-salvia",
  inferred: "bg-oro",
  uncertain: "bg-rojo",
};

export function ConfidenceMarker({
  claims,
  hoveredId,
  onHover,
  className,
  ...props
}) {
  const t = useT();
  const basisId = useId();
  const [internalActive, setInternalActive] = useState("");
  const controlled = hoveredId !== undefined;
  const activeId = controlled ? hoveredId : internalActive;
  const setActive = controlled ? (onHover ?? (() => {})) : setInternalActive;

  const [pinnedId, setPinnedId] = useState("");
  const active = claims.find((claim) => claim.id === activeId);

  const preview = (id) => {
    if (pinnedId) return; // algo fijado por tap gana sobre el hover/focus
    setActive(id);
  };
  const togglePin = (id) => {
    const next = pinnedId === id ? "" : id;
    setPinnedId(next);
    setActive(next);
  };

  return (
    <div
      data-slot="confidence-marker"
      className={cn("flex w-full max-w-sm flex-col gap-2.5", className)}
      {...props}
    >
      <p className="text-[13.5px] leading-relaxed">
        {claims.map((claim) => (
          <button
            key={claim.id}
            type="button"
            aria-describedby={activeId === claim.id ? basisId : undefined}
            aria-pressed={pinnedId === claim.id}
            onMouseEnter={() => preview(claim.id)}
            onMouseLeave={() => preview("")}
            onFocus={() => preview(claim.id)}
            onBlur={() => preview("")}
            onClick={() => togglePin(claim.id)}
            className={cn(
              "focus-visible:ring-tinta/20 inline cursor-help rounded text-start underline decoration-2 underline-offset-[3px] transition-colors outline-none focus-visible:ring-1",
              UNDERLINE[claim.confidence],
              activeId === claim.id ? "text-tinta/95" : "text-tinta/70",
            )}
          >
            {claim.text}{" "}
          </button>
        ))}
      </p>

      <div className="flex min-h-9 items-start">
        {active && (
          <span
            id={basisId}
            role="status"
            className={cn(
              floating,
              mono,
              "fade-in zoom-in-95 animate-in flex items-center gap-1.5 rounded-full px-2.5 py-1.5 text-tinta-suave duration-150",
            )}
          >
            <span aria-hidden className={cn("size-1.5 rounded-full", DOT[active.confidence])} />
            {t(`conf.marker_${active.confidence}`)} · {active.basis}
          </span>
        )}
      </div>
    </div>
  );
}
