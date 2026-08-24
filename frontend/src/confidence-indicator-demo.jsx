import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import ConfidenceIndicator from "./components/ConfidenceIndicator";
import { ConfidenceMarker } from "./components/assistant/confidence-marker";
import { useT } from "./lib/i18n";
import "./index.css";

// ============================================================================
// Standalone reference page for <ConfidenceIndicator> — every state, band,
// and anti-pattern guard from the pattern brief in one place, wired to real
// interaction (not screenshots). Dev-only: run `npm run dev` and open
// /confidence-indicator-demo.html — this entry is not part of the production
// bundle (not in vite.config.js's build inputs), by design: it's a worked
// example for the pattern, not a shipped route.
//
// The real, production integration lives in
// src/sections/Conciliacion.jsx (the "Causa más probable" badge on each
// stock discrepancy) — see FUERZA_REGLA there for how a real screen maps
// domain data onto this component today, and
// docs/motor-conciliacion-confianza.md for where the real calibrated
// score/sampleSize will come from once the Supabase engine is wired in.
// ============================================================================

const LEGEND = {
  high: "Esta regla acertó casi siempre en casos parecidos ya resueltos.",
  medium: "Es la explicación más probable, pero con poco historial todavía.",
  low: "Hay pocos casos parecidos y no acertaron seguido.",
  unverified: "Sin evidencia verificable, sin historial, o sin confirmar todavía.",
};

function Section({ title, note, children }) {
  return (
    <section className="mb-10">
      <h2 className="mb-1 text-lg font-bold">{title}</h2>
      {note && <p className="mb-3 max-w-2xl text-[0.85rem] text-tinta-suave">{note}</p>}
      <div className="flex flex-wrap items-start gap-4 rounded-2xl border border-linea bg-superficie p-4">
        {children}
      </div>
    </section>
  );
}

function Swatch({ label, children }) {
  return (
    <div className="flex min-w-[220px] flex-col gap-2 rounded-xl border border-linea/70 p-3">
      <p className="text-[0.7rem] font-semibold uppercase tracking-wide text-tinta-suave">{label}</p>
      {children}
    </div>
  );
}

function Demo() {
  useT(); // se suscribe al store de idioma (no usado directo acá, ver Conciliacion.jsx para copy real)
  const [errorTries, setErrorTries] = useState(0);
  const [loadingDone, setLoadingDone] = useState(false);

  return (
    <main className="mx-auto max-w-4xl px-6 py-10 text-tinta">
      <header className="mb-8">
        <h1 className="font-display text-3xl font-bold">Confidence Indicators</h1>
        <p className="mt-1 max-w-2xl text-[0.95rem] text-tinta-suave">
          Referencia ejecutable de las dos formas del patrón: <code>ConfidenceIndicator</code>{" "}
          (badge/meter por ítem, secciones 1-5) y <code>ConfidenceMarker</code>{" "}
          (subrayado por tramo de texto, sección 6). Calibrados, con leyenda,
          hedging y los cuatro estados de interacción. Cada swatch de abajo es
          el componente real, no una captura.
        </p>
      </header>

      <Section
        title="1 · Estados de interacción"
        note="idle no renderiza nada (el consumidor decide cuándo hay algo que mostrar); loading es aria-live; error ofrece reintentar sin perder el lugar."
      >
        <Swatch label="idle">
          <ConfidenceIndicator state="idle" />
          <p className="text-[0.75rem] text-tinta-suave">(no renderiza nada — esperado)</p>
        </Swatch>
        <Swatch label="loading">
          <ConfidenceIndicator state="loading" />
        </Swatch>
        <Swatch label="error, con reintentar">
          <ConfidenceIndicator
            state="error"
            onRetry={() => setErrorTries((n) => n + 1)}
          />
          <p className="text-[0.75rem] text-tinta-suave">reintentado {errorTries} veces</p>
        </Swatch>
        <Swatch label="success (después de loading)">
          <button
            type="button"
            onClick={() => setLoadingDone((v) => !v)}
            className="mb-1 self-start rounded-lg border border-linea px-2 py-1 text-[0.72rem]"
          >
            {loadingDone ? "volver a loading" : "simular que terminó"}
          </button>
          <ConfidenceIndicator
            state={loadingDone ? "success" : "loading"}
            score={0.86}
            sampleSize={11}
            bounds={[0.58, 0.96]}
            tier={0}
            evidenceHref="#"
            legend={LEGEND}
          />
        </Swatch>
      </Section>

      <Section
        title="2 · Bandas calibradas (score real medido)"
        note="El texto siempre declara sobre cuántos casos se midió — nunca un número sin muestra al lado."
      >
        <Swatch label="alta — 11/13, Wilson [58%, 96%]">
          <ConfidenceIndicator
            score={0.86} sampleSize={11} bounds={[0.58, 0.96]} tier={0}
            evidenceHref="#" legend={LEGEND}
          />
        </Swatch>
        <Swatch label="media — 4/6">
          <ConfidenceIndicator
            score={0.67} sampleSize={4} tier={0}
            evidenceHref="#" legend={LEGEND}
          />
        </Swatch>
        <Swatch label="baja — 1/5">
          <ConfidenceIndicator
            score={0.2} sampleSize={5} tier={0}
            evidenceHref="#" legend={LEGEND}
          />
        </Swatch>
        <Swatch label="sin muestra (n=0)">
          <ConfidenceIndicator
            score={0.9} sampleSize={0} tier={0}
            evidenceHref="#" legend={LEGEND}
          />
          <p className="text-[0.72rem] text-tinta-suave">
            score alto pero sin casos resueltos → nunca miente con un % igual.
          </p>
        </Swatch>
      </Section>

      <Section
        title="3 · Variante meter"
        note="Usa el elemento nativo <meter> (semántica de accesibilidad incluida) en vez de una barra hecha a mano."
      >
        <Swatch label="meter, alta">
          <ConfidenceIndicator
            variant="meter" score={0.86} sampleSize={11} tier={0}
            evidenceHref="#" legend={LEGEND}
          />
        </Swatch>
        <Swatch label="meter, media, tamaño chico">
          <ConfidenceIndicator
            variant="meter" size="sm" score={0.55} sampleSize={6} tier={0}
            evidenceHref="#" legend={LEGEND}
          />
        </Swatch>
      </Section>

      <Section
        title="4 · Juicio del oficio, todavía sin medir (qualitativeBand)"
        note="Lo que usa HOY Conciliacion.jsx: la cascada de reglas de conciliacion.py tiene una fuerza conocida por el oficio, pero el sistema no la midió todavía contra casos reales. El componente lo etiqueta distinto de un score calibrado."
      >
        <Swatch label="alta (juicio)">
          <ConfidenceIndicator qualitativeBand="high" tier={0} evidenceHref="#" legend={LEGEND} />
        </Swatch>
        <Swatch label="media (juicio)">
          <ConfidenceIndicator qualitativeBand="medium" tier={0} evidenceHref="#" legend={LEGEND} />
        </Swatch>
        <Swatch label="baja (juicio)">
          <ConfidenceIndicator qualitativeBand="low" tier={0} evidenceHref="#" legend={LEGEND} />
        </Swatch>
      </Section>

      <Section
        title="5 · Los cuatro anti-patrones, forzados a propósito"
        note="Cada swatch de acá tiene un score y una banda pedidos en 'alta', y el componente los baja igual — porque falta lo que hace falta para confiar en 'alta'."
      >
        <Swatch label="sin evidencia → nunca verde">
          <ConfidenceIndicator score={0.95} sampleSize={20} tier={0} legend={LEGEND} />
          <p className="text-[0.72rem] text-tinta-suave">
            score .95, n=20, pero sin evidenceHref/onViewEvidence: cae a "sin confirmar".
          </p>
        </Swatch>
        <Swatch label="tier 3 (agente) → siempre tope ámbar/celeste">
          <ConfidenceIndicator score={0.95} sampleSize={20} tier={3} evidenceHref="#" legend={LEGEND} />
          <p className="text-[0.72rem] text-tinta-suave">
            una hipótesis de IA nunca se muestra como confirmada por sí sola.
          </p>
        </Swatch>
        <Swatch label="sin legend → warning en consola (dev)">
          <ConfidenceIndicator score={0.86} sampleSize={11} tier={0} evidenceHref="#" />
          <p className="text-[0.72rem] text-tinta-suave">
            abrí la consola: tira console.error y usa una leyenda genérica de repuesto.
          </p>
        </Swatch>
        <Swatch label="hedge nunca se esconde, ni en 'alta'">
          <ConfidenceIndicator score={0.97} sampleSize={40} tier={0} evidenceHref="#" legend={LEGEND} />
          <p className="text-[0.72rem] text-tinta-suave">
            el "medido sobre 40 casos" queda visible siempre, no sólo en las bandas dudosas.
          </p>
        </Swatch>
      </Section>

      <Section
        title="6 · ConfidenceMarker — el mismo patrón, por tramo de texto"
        note={
          <>
            Adaptado de assistant-ui.com/elements/confidence-marker: en vez de
            un badge por ítem, marca tramos DENTRO de un párrafo largo — pensado
            para el chat de Ángela (ver <code>meta.claims</code> en
            src/components/assistant/angela-thread.jsx). Tocá una claim en el
            celu para fijarla; en desktop alcanza con pasar el mouse o
            tabular con teclado.
          </>
        }
      >
        <ConfidenceMarker
          className="max-w-none"
          claims={[
            { id: "c1", text: "El lote 002 tiene 17.400 kg en Frigorífico Dospanca.", confidence: "grounded", basis: "conteo #482, 22/08" },
            { id: "c2", text: "Es probable que los 600 kg que faltan estén en San Cayetano, sin registrar todavía.", confidence: "inferred", basis: "movimiento M-2201, sin confirmar en destino" },
            { id: "c3", text: "No encontré ninguna nota del equipo que lo confirme.", confidence: "uncertain", basis: "busqué en las notas de los últimos 14 días" },
          ]}
        />
      </Section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Demo />
  </StrictMode>
);
