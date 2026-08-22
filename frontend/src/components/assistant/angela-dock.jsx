import { useCallback, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";

const WIDTH_KEY = "polpilot.angelaDockWidth";
const MIN_WIDTH = 300;
const MAX_WIDTH = 780;
const DEFAULT_WIDTH = 380;

function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n));
}

function useDockWidth() {
  const [width, setWidth] = useState(DEFAULT_WIDTH);

  useEffect(() => {
    const raw = window.localStorage.getItem(WIDTH_KEY);
    const n = raw ? Number(raw) : NaN;
    if (!Number.isFinite(n)) return;
    setWidth(clamp(n, MIN_WIDTH, MAX_WIDTH));
  }, []);

  const persist = useCallback((next) => {
    const w = clamp(next, MIN_WIDTH, MAX_WIDTH);
    setWidth(w);
    window.localStorage.setItem(WIDTH_KEY, String(Math.round(w)));
  }, []);

  return [width, setWidth, persist];
}

/** Panel lateral redimensionable (patrón Polfin). */
export function AngelaDock({ children }) {
  const [width, setWidth, persistWidth] = useDockWidth();
  const drag = useRef(null);

  const maxCap = () => Math.min(MAX_WIDTH, Math.round(window.innerWidth * 0.55));

  const onResizePointerDown = (event) => {
    event.preventDefault();
    drag.current = { startX: event.clientX, startW: width };
    event.currentTarget.setPointerCapture(event.pointerId);
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  const onResizePointerMove = (event) => {
    if (!drag.current) return;
    const next = drag.current.startW + (drag.current.startX - event.clientX);
    setWidth(clamp(next, MIN_WIDTH, maxCap()));
  };

  const onResizePointerUp = (event) => {
    if (!drag.current) return;
    const next = drag.current.startW + (drag.current.startX - event.clientX);
    persistWidth(clamp(next, MIN_WIDTH, maxCap()));
    drag.current = null;
    event.currentTarget.releasePointerCapture(event.pointerId);
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  };

  return (
    <motion.aside
      initial={{ x: 48, opacity: 0.5 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 48, opacity: 0.5 }}
      transition={{ type: "spring", stiffness: 320, damping: 34 }}
      className="relative flex h-full shrink-0 flex-col border-l border-linea bg-papel"
      style={{ width }}
    >
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label="Ancho del panel de Ángela"
        aria-valuemin={MIN_WIDTH}
        aria-valuemax={MAX_WIDTH}
        aria-valuenow={Math.round(width)}
        onPointerDown={onResizePointerDown}
        onPointerMove={onResizePointerMove}
        onPointerUp={onResizePointerUp}
        onPointerCancel={onResizePointerUp}
        className="absolute inset-y-0 -left-1 z-10 w-2 cursor-col-resize touch-none"
      >
        <span className="absolute inset-y-0 left-1 w-px bg-linea/60 transition-colors hover:bg-violeta/40" />
      </div>
      {children}
    </motion.aside>
  );
}
