import { useEffect, useState } from "react";
import {
  Scale, ArrowRight, Wrench, Sprout, HelpCircle, Check,
  FileSearch, ChevronDown, ChevronRight,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import ConfidenceIndicator from "../components/ConfidenceIndicator";
import { api } from "../lib/api";
import { num, peso, pesoCorto, fecha } from "../lib/format";
import { useT } from "../lib/i18n";
import { toast } from "../lib/toastStore";

// ============================================================================
// N02 · LO DECLARADO CONTRA LO CONTADO — y por qué no coinciden.
// ----------------------------------------------------------------------------
// Cualquier sistema de stock puede pintar una fila en rojo. Lo que pide el
// brief es lo otro: «propone una hipótesis en lenguaje simple sobre cuál puede
// ser la causa más probable».
//
// La decisión de diseño de esta pantalla es que la hipótesis NO se presenta
// como una opinión del sistema: se presenta con LA EVIDENCIA AL LADO. Número de
// movimiento, fecha, quién lo cargó y por qué canal. Cualquiera puede abrir el
// detalle y verificarlo. Eso es lo que separa una corazonada de un hallazgo, y
// es lo que un auditor va a querer ver.
// ============================================================================

const CLASE = {
  movimiento_sin_confirmar: {
    icono: ArrowRight, tono: "rojo",
    borde: "border-rojo/30", fondo: "bg-rojo/[0.04]", texto: "text-rojo",
  },
  cantidad_mal_tipeada: {
    icono: Wrench, tono: "oro",
    borde: "border-oro/35", fondo: "bg-oro/[0.05]", texto: "text-oro",
  },
  merma_fisica: {
    icono: Sprout, tono: "oro",
    borde: "border-oro/35", fondo: "bg-oro/[0.05]", texto: "text-oro",
  },
  sin_explicacion: {
    icono: HelpCircle, tono: "rojo",
    borde: "border-rojo/30", fondo: "bg-rojo/[0.04]", texto: "text-rojo",
  },
  tara: {
    icono: Check, tono: "salvia",
    borde: "border-linea", fondo: "bg-crema/60", texto: "text-salvia",
  },
};

// La fuerza de cada regla, tal como está hoy: un juicio del oficio (cascada
// determinística de conciliacion.py), no todavía una estadística medida.
// Cuando el motor de docs/motor-conciliacion-confianza.md esté conectado,
// el backend va a mandar confianza_score/muestra_n reales por hipótesis y
// esta tabla deja de hacer falta — <ConfidenceIndicator> ya sabe mostrar esa
// versión medida en cuanto los datos lleguen (ver su prop `score`).
const FUERZA_REGLA = {
  movimiento_sin_confirmar: { tier: 0, qualitativeBand: "high" },
  cantidad_mal_tipeada: { tier: 0, qualitativeBand: "medium" },
  merma_fisica: { tier: 0, qualitativeBand: "medium" },
  sin_explicacion: { tier: 0, qualitativeBand: "low" },
};

export default function Conciliacion({ onPreguntar }) {
  const t = useT();
  const [d, setD] = useState(null);
  const [verTara, setVerTara] = useState(false);
  const [trabajando, setTrabajando] = useState(null);

  const cargar = () => api.conciliacion(false).then(setD).catch(() => setD(false));
  useEffect(() => { cargar(); }, []);

  if (d === null) return <Esqueleto />;
  if (d === false) return <p className="text-tinta-suave">{t("conc.error")}</p>;

  const r = d.resumen || {};
  const todas = d.diferencias || [];
  const abiertas = todas.filter((x) => x.hipotesis?.clase !== "tara");
  const taras = todas.filter((x) => x.hipotesis?.clase === "tara");

  // La acción de la hipótesis se ejecuta por el riel real, no por un atajo:
  // confirmar un movimiento es el MISMO endpoint que usa el operario.
  const ejecutar = async (dif) => {
    const acc = dif.hipotesis?.accion;
    if (!acc) return;
    setTrabajando(dif.numero);
    try {
      if (acc.tipo === "confirmar_movimiento") {
        await api.movimientoConfirmar(acc.numero);
        toast(t("conc.confirmado", { n: acc.numero }));
        await cargar();
      } else {
        // Corregir una carga o dar de baja por merma toca la verdad del stock:
        // eso no se aplica solo. Va al chat, donde queda el pedido de OK.
        onPreguntar?.(t("conc.pregunta_accion", { etiqueta: acc.etiqueta, lote: dif.lote }));
      }
    } catch {
      toast(t("conc.fallo"));
    } finally {
      setTrabajando(null);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl font-bold">{t("conc.titulo")}</h1>
        <p className="mt-1 text-[0.95rem] text-tinta-suave">{t("conc.subtitulo")}</p>
      </header>

      {abiertas.length === 0 ? (
        <AngelaSays tone="ok">{t("conc.todo_cierra")}</AngelaSays>
      ) : (
        <AngelaSays tone={r.sin_explicacion ? "urgente" : "atencion"}>
          {t("conc.angela", {
            n: abiertas.length,
            plata: peso(r.plata_en_diferencia),
            sin: r.sin_explicacion,
          })}
        </AngelaSays>
      )}

      <div className="space-y-3">
        {abiertas.map((dif) => (
          <Diferencia
            key={dif.numero}
            dif={dif}
            trabajando={trabajando === dif.numero}
            onEjecutar={() => ejecutar(dif)}
            onPreguntar={onPreguntar}
          />
        ))}
      </div>

      {/* Las taras existen y se muestran, pero no gritan: son diferencias que
          el encargado ya explicó una vez y le enseñó al sistema a no alertar.
          Esconderlas del todo sería tan malo como alertarlas. */}
      {taras.length > 0 && (
        <section className="rounded-[var(--radius-card)] border border-linea bg-crema/50">
          <button
            type="button"
            onClick={() => setVerTara((v) => !v)}
            className="flex w-full items-center gap-2 px-4 py-3 text-left"
          >
            {verTara ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
            <Check size={15} className="text-salvia" />
            <span className="flex-1 text-[0.88rem]">
              {t("conc.taras", { n: taras.length })}
            </span>
            <span className="text-[0.75rem] text-tinta-suave">{t("conc.taras_regla")}</span>
          </button>
          {verTara && (
            <ul className="space-y-1 border-t border-linea px-4 py-3 text-[0.82rem]">
              {taras.map((x) => (
                <li key={x.numero} className="flex flex-wrap justify-between gap-2">
                  <span className="text-tinta-suave">
                    {x.lote} · {x.ubicacion} · {x.camara}
                  </span>
                  <span className="tabular-nums">
                    {x.diferencia_kg > 0 ? "+" : ""}{num(x.diferencia_kg)} kg ({x.diferencia_pct}%)
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </div>
  );
}

// --- una diferencia, con su hipótesis y su evidencia ------------------------
function Diferencia({ dif, trabajando, onEjecutar, onPreguntar }) {
  const t = useT();
  const [verEvidencia, setVerEvidencia] = useState(false);
  const h = dif.hipotesis || {};
  const c = CLASE[h.clase] || CLASE.sin_explicacion;
  const Icono = c.icono;
  const falta = dif.diferencia_kg < 0;

  return (
    <article className={`overflow-hidden rounded-[var(--radius-card)] border ${c.borde} bg-superficie sombra-papel`}>
      <header className="flex flex-wrap items-start gap-3 border-b border-linea px-4 py-3">
        <span className={`mt-0.5 shrink-0 rounded-lg ${c.fondo} p-2 ${c.texto}`}>
          <Icono size={17} />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="font-display text-[1.02rem] font-bold leading-tight">{dif.lote}</h2>
          <p className="mt-0.5 text-[0.8rem] text-tinta-suave">
            {dif.producto} · {dif.ubicacion} ({dif.camara})
          </p>
        </div>
        <div className="shrink-0 text-right">
          <p className={`plata text-xl font-medium ${falta ? "text-rojo" : "text-oro"}`}>
            {falta ? "−" : "+"}{num(Math.abs(dif.diferencia_kg))} kg
          </p>
          <p className="text-[0.7rem] text-tinta-suave">{pesoCorto(dif.impacto_pesos)}</p>
        </div>
      </header>

      {/* declarado vs contado, uno al lado del otro: la comparación es el dato */}
      <div className="grid grid-cols-3 gap-px border-b border-linea bg-linea text-center">
        <Celda etiqueta={t("conc.declarado")} valor={`${num(dif.declarado_kg)} kg`} />
        <Celda etiqueta={t("conc.contado")} valor={`${num(dif.fisico_kg)} kg`} />
        <Celda
          etiqueta={t("conc.diferencia")}
          valor={`${dif.diferencia_bolsones > 0 ? "+" : ""}${dif.diferencia_bolsones} ${t("conc.bolsones")}`}
          tono={falta ? "rojo" : "oro"}
        />
      </div>

      <div className="space-y-3 px-4 py-3">
        <div>
          <div className="mb-1.5 flex flex-wrap items-start justify-between gap-2">
            <p className="flex items-center gap-1.5 text-[0.7rem] font-semibold uppercase tracking-wide text-tinta-suave">
              <FileSearch size={12} /> {t("conc.hipotesis")}
            </p>
            <ConfidenceIndicator
              size="sm"
              tier={FUERZA_REGLA[h.clase]?.tier ?? 0}
              qualitativeBand={FUERZA_REGLA[h.clase]?.qualitativeBand}
              onViewEvidence={() => setVerEvidencia((v) => !v)}
              legend={{
                high: t("conc.confianza_leyenda_alta"),
                medium: t("conc.confianza_leyenda_media"),
                low: t("conc.confianza_leyenda_baja"),
                unverified: t("conc.confianza_leyenda_sin_confirmar"),
              }}
            />
          </div>
          <p className="text-[0.92rem] leading-snug">{h.texto}</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {h.accion && (
            <button
              type="button"
              disabled={trabajando}
              onClick={onEjecutar}
              className="rounded-lg bg-tinta px-3 py-1.5 text-[0.85rem] font-medium text-crema transition hover:bg-tinta/90 disabled:opacity-50"
            >
              {trabajando ? t("conc.trabajando") : h.accion.etiqueta}
            </button>
          )}
          <button
            type="button"
            onClick={() => setVerEvidencia((v) => !v)}
            className="rounded-lg border border-linea px-3 py-1.5 text-[0.85rem] transition hover:bg-crema"
          >
            {verEvidencia ? t("conc.ocultar_evidencia") : t("conc.ver_evidencia")}
          </button>
          <button
            type="button"
            onClick={() => onPreguntar?.(t("conc.pregunta", { lote: dif.lote }))}
            className="text-[0.85rem] text-hielo underline underline-offset-2"
          >
            {t("conc.preguntar")}
          </button>
        </div>

        {/* LA EVIDENCIA. Esto es lo que convierte la hipótesis en un hallazgo:
            los datos crudos que la sostienen, para que cualquiera verifique. */}
        {verEvidencia && (
          <div className="rounded-lg border border-linea bg-crema/70 p-3">
            <p className="mb-2 text-[0.7rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {t("conc.evidencia_titulo")}
            </p>
            <Evidencia ev={h.evidencia} />
            <p className="mt-2 border-t border-linea pt-2 text-[0.75rem] text-tinta-suave">
              {t("conc.contado_por", { quien: dif.contado_por, fecha: fecha(dif.fecha) })}
            </p>
          </div>
        )}
      </div>
    </article>
  );
}

function Evidencia({ ev }) {
  const t = useT();
  if (!ev) return <p className="text-[0.85rem] text-tinta-suave">—</p>;
  const m = ev.movimiento;
  return (
    <div className="space-y-2 text-[0.85rem]">
      {m && (
        <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
          <Dato k={t("conc.ev_mov")} v={m.numero} />
          <Dato k={t("conc.ev_fecha")} v={fecha(m.fecha)} />
          <Dato k={t("conc.ev_kg")} v={`${num(m.kg)} kg (${m.bolsones} ${t("conc.bolsones")})`} />
          <Dato k={t("conc.ev_ruta")} v={`${m.origen} → ${m.destino}`} />
          <Dato k={t("conc.ev_quien")} v={`${m.registrado_por} · ${m.canal}`} />
          <Dato k={t("conc.ev_estado")} v={m.estado} />
        </dl>
      )}
      {ev.nota && (
        <blockquote className="border-l-2 border-hielo/40 pl-3 italic text-tinta-suave">
          «{ev.nota.texto}»
          <footer className="mt-0.5 not-italic text-[0.78rem]">
            — {ev.nota.autor}, {fecha(ev.nota.fecha)}
          </footer>
        </blockquote>
      )}
      {ev.regla && (
        <p className="text-tinta-suave">
          {t("conc.ev_regla")}: «{ev.regla.titulo || ev.regla.texto}»
        </p>
      )}
      {ev.buscado_en && (
        <p className="text-tinta-suave">
          {t("conc.ev_buscado")}: {ev.buscado_en.join(" · ")}
        </p>
      )}
    </div>
  );
}

const Dato = ({ k, v }) => (
  <>
    <dt className="text-tinta-suave">{k}</dt>
    <dd className="tabular-nums">{v}</dd>
  </>
);

function Celda({ etiqueta, valor, tono }) {
  const color = tono === "rojo" ? "text-rojo" : tono === "oro" ? "text-oro" : "text-tinta";
  return (
    <div className="bg-superficie px-3 py-2">
      <p className="text-[0.68rem] uppercase tracking-wide text-tinta-suave">{etiqueta}</p>
      <p className={`plata mt-0.5 text-[0.95rem] font-medium tabular-nums ${color}`}>{valor}</p>
    </div>
  );
}

function Esqueleto() {
  return (
    <div className="space-y-6" aria-busy="true">
      <div className="h-9 w-80 animate-pulse rounded bg-linea" />
      <div className="h-16 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-52 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
      ))}
    </div>
  );
}
