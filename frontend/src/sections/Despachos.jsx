import { useEffect, useState } from "react";
import {
  Ship, Truck, Lock, ShieldCheck, TriangleAlert, Ruler, FlaskConical,
  Sprout, PackageX, Check, ArrowRight,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import { api } from "../lib/api";
import { num, peso, pesoCorto, fecha } from "../lib/format";
import { useT } from "../lib/i18n";
import { toast } from "../lib/toastStore";

// ============================================================================
// EL FRENO DEL REMITO — la pantalla que existe por una sola frase del brief:
//
//   «Las diferencias entre lo que dice la planilla y lo que hay en la realidad
//    suelen descubrirse recién al momento de entregarle el pedido a un cliente.»
//
// El dolor no es el desorden: es el papelón. El camión en la playa, el cliente
// esperando, y ahí aparece que faltan dieciocho bolsones.
//
// Por eso acá el botón de emitir NO es un botón con una advertencia al lado.
// Cuando hay un bloqueo, el botón directamente no existe: en su lugar está el
// motivo, con el número exacto y qué hay que hacer para levantarlo. Un sistema
// que deja emitir igual "porque el usuario insistió" es el mismo sistema que
// tienen hoy, con más pasos.
// ============================================================================

const CONTROL = {
  sin_stock_verificado: { icono: PackageX, k: "desp.c_stock" },
  conteo_en_discusion: { icono: TriangleAlert, k: "desp.c_conteo" },
  analisis_vencido: { icono: FlaskConical, k: "desp.c_analisis" },
  sanidad_observada: { icono: FlaskConical, k: "desp.c_sanidad" },
  calibre_fuera_de_grado: { icono: Ruler, k: "desp.c_calibre" },
  pasado_de_brotacion: { icono: Sprout, k: "desp.c_brotacion" },
};

export default function Despachos({ onPreguntar, highlight }) {
  const t = useT();
  const [d, setD] = useState(null);
  const [emitiendo, setEmitiendo] = useState(null);

  const cargar = () => api.ordenesCarga().then(setD).catch(() => setD(false));
  useEffect(() => { cargar(); }, []);

  if (d === null) return <Esqueleto />;
  if (d === false) return <p className="text-tinta-suave">{t("desp.error")}</p>;

  const r = d.resumen || {};
  const ordenes = d.ordenes || [];

  const emitir = async (o, aceptarAdvertencias = false) => {
    setEmitiendo(o.numero);
    try {
      await api.ordenEmitir(o.numero, aceptarAdvertencias);
      toast(t("desp.emitida", { n: o.numero }));
      await cargar();
    } catch (e) {
      // El 409 del backend es el freno, no un error de red: se cuenta como tal.
      toast(t("desp.frenada"));
      await cargar();
    } finally {
      setEmitiendo(null);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl font-bold">{t("desp.titulo")}</h1>
        <p className="mt-1 text-[0.95rem] text-tinta-suave">{t("desp.subtitulo")}</p>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <Kpi valor={num(r.abiertas)} etiqueta={t("desp.kpi_abiertas")} />
        <Kpi
          valor={num(r.listas)}
          etiqueta={t("desp.kpi_listas")}
          tono={r.listas ? "ok" : "neutro"}
        />
        <Kpi
          valor={num(r.bloqueadas)}
          etiqueta={t("desp.kpi_bloqueadas")}
          tono={r.bloqueadas ? "alerta" : "ok"}
          nota={r.bloqueadas ? t("desp.kpi_bloq_nota", { kg: num(r.kg_bloqueado) }) : null}
        />
      </div>

      {r.bloqueadas > 0 && (
        <AngelaSays tone="urgente">{t("desp.angela_bloqueo", { n: r.bloqueadas })}</AngelaSays>
      )}

      <div className="space-y-4">
        {ordenes.map((o) => (
          <Orden
            key={o.numero}
            o={o}
            resaltada={highlight === `orden-${o.numero}`}
            emitiendo={emitiendo === o.numero}
            onEmitir={emitir}
            onPreguntar={onPreguntar}
          />
        ))}
      </div>

      {d.historial?.length > 0 && (
        <section>
          <h2 className="mb-2 font-display text-lg font-bold">{t("desp.historial")}</h2>
          <ul className="divide-y divide-linea overflow-hidden rounded-[var(--radius-card)] border border-linea bg-superficie">
            {d.historial.slice(0, 6).map((o) => (
              <li key={o.numero} className="flex flex-wrap items-center gap-2 px-4 py-2.5 text-[0.85rem]">
                <Check size={14} className="shrink-0 text-salvia" />
                <span className="font-medium">{o.numero}</span>
                <span className="min-w-0 flex-1 truncate text-tinta-suave">{o.cliente}</span>
                <span className="tabular-nums text-tinta-suave">{num(o.kg_total)} kg</span>
                <span className="text-[0.78rem] text-tinta-suave">{fecha(o.fecha)}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

// --- una orden de carga -----------------------------------------------------
function Orden({ o, resaltada, emitiendo, onEmitir, onPreguntar }) {
  const t = useT();
  const esExport = o.tipo === "exportacion";
  const Icono = esExport ? Ship : Truck;
  const bloqueada = !o.puede_emitirse;

  return (
    <article
      id={`orden-${o.numero}`}
      className={`overflow-hidden rounded-[var(--radius-card)] border bg-superficie sombra-papel transition
        ${bloqueada ? "border-rojo/35" : "border-salvia/30"}
        ${resaltada ? "ring-2 ring-hielo/40" : ""}`}
    >
      <header className="flex flex-wrap items-start gap-3 border-b border-linea px-4 py-3">
        <span className={`mt-0.5 shrink-0 rounded-lg p-2 ${bloqueada ? "bg-rojo/8 text-rojo" : "bg-salvia/10 text-salvia"}`}>
          <Icono size={18} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className="font-display text-[1.05rem] font-bold leading-tight">{o.numero}</h2>
            {esExport && (
              <span className="rounded-full bg-hielo/10 px-2 py-0.5 text-[0.7rem] text-hielo">
                {t("desp.exportacion")} · {o.pais}
              </span>
            )}
          </div>
          <p className="mt-0.5 truncate text-[0.85rem] text-tinta-suave">{o.cliente}</p>
        </div>
        <div className="shrink-0 text-right">
          <p className="plata text-lg font-medium">{num(o.kg_total)} kg</p>
          <p className="text-[0.7rem] text-tinta-suave">
            {o.bolsones_total} {t("desp.bolsones")}
          </p>
        </div>
      </header>

      <div className="space-y-3 px-4 py-3">
        <ul className="space-y-1 text-[0.85rem]">
          {(o.items || []).map((it) => (
            <li key={it.codigo} className="flex flex-wrap items-baseline gap-x-2">
              <span className="font-medium">{it.lote}</span>
              <span className="min-w-0 flex-1 truncate text-tinta-suave">
                {it.variedad} · {it.categoria_semilla} · {it.ubicacion} ({it.camara})
              </span>
              <span className="tabular-nums">{num(it.kg)} kg</span>
            </li>
          ))}
        </ul>

        {o.nota && <p className="text-[0.82rem] italic text-tinta-suave">{o.nota}</p>}

        {/* ------------------------------------------------------------------
            EL FRENO. Con bloqueos no hay botón de emitir: hay motivo y salida.
           ------------------------------------------------------------------ */}
        {bloqueada ? (
          <div className="rounded-lg border border-rojo/30 bg-rojo/[0.04] p-3">
            <p className="mb-2 flex items-center gap-2 font-display text-[0.95rem] font-bold text-rojo">
              <Lock size={15} /> {t("desp.bloqueada")}
            </p>
            <ul className="space-y-2">
              {o.bloqueos.map((b, i) => (
                <li key={i}><Motivo b={b} /></li>
              ))}
            </ul>
            <button
              type="button"
              onClick={() => onPreguntar?.(t("desp.pregunta_bloqueo", { n: o.numero }))}
              className="mt-3 flex items-center gap-1.5 text-[0.85rem] font-medium text-hielo underline underline-offset-2"
            >
              {t("desp.como_destrabo")} <ArrowRight size={13} />
            </button>
          </div>
        ) : (
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              disabled={emitiendo}
              onClick={() => onEmitir(o, o.advertencias?.length > 0)}
              className="flex items-center gap-1.5 rounded-lg bg-salvia px-3.5 py-2 text-[0.88rem] font-medium text-crema transition hover:bg-salvia/90 disabled:opacity-50"
            >
              <ShieldCheck size={15} />
              {emitiendo ? t("desp.emitiendo") : t("desp.emitir")}
            </button>
            <span className="text-[0.78rem] text-tinta-suave">
              {t("desp.controles_ok")}
            </span>
          </div>
        )}

        {/* Las advertencias no frenan mercado interno, pero se firman: quien
            acepta queda registrado en la auditoría. Nunca pasan por inercia. */}
        {o.advertencias?.length > 0 && (
          <div className="rounded-lg border border-oro/35 bg-oro/[0.05] p-3">
            <p className="mb-1.5 flex items-center gap-2 text-[0.85rem] font-semibold text-oro">
              <TriangleAlert size={14} /> {t("desp.advertencias")}
            </p>
            <ul className="space-y-1.5">
              {o.advertencias.map((a, i) => (
                <li key={i}><Motivo b={a} suave /></li>
              ))}
            </ul>
            <p className="mt-2 text-[0.75rem] text-tinta-suave">{t("desp.adv_firma")}</p>
          </div>
        )}
      </div>
    </article>
  );
}

// --- el motivo de un control, con su número exacto --------------------------
function Motivo({ b, suave }) {
  const t = useT();
  const c = CONTROL[b.control] || { icono: TriangleAlert, k: "desp.c_otro" };
  const Icono = c.icono;
  const color = suave ? "text-oro" : "text-rojo";

  // Cada control dice SU dato: los kilos que faltan, los días vencidos, los
  // milímetros fuera de rango. Un motivo sin número no ayuda a nadie.
  let detalle = "";
  if (b.control === "sin_stock_verificado") {
    detalle = t("desp.d_stock", {
      pedido: num(b.pedido_kg), disp: num(b.disponible_kg),
      falta: num(b.faltante_kg), bolsones: b.faltante_bolsones,
    });
  } else if (b.control === "conteo_en_discusion") {
    detalle = b.hipotesis?.texto || t("desp.d_conteo", { kg: num(b.diferencia_kg) });
  } else if (b.control === "analisis_vencido") {
    detalle = t("desp.d_analisis", { dias: b.dias, limite: b.limite_dias });
  } else if (b.control === "sanidad_observada") {
    detalle = t("desp.d_sanidad", {
      virus: b.virus_pct, max: b.virus_max_pct, cat: b.categoria,
    });
  } else if (b.control === "calibre_fuera_de_grado") {
    detalle = t("desp.d_calibre", {
      grado: b.grado, medido: b.medido_mm,
      min: b.rango_mm?.[0], max: b.rango_mm?.[1],
    });
  } else if (b.control === "pasado_de_brotacion") {
    detalle = t("desp.d_brotacion", { dias: b.dias_pasados });
  }

  return (
    <div className="flex gap-2">
      <Icono size={14} className={`mt-0.5 shrink-0 ${color}`} />
      <div className="min-w-0">
        <p className={`text-[0.85rem] font-medium ${color}`}>{t(c.k)}</p>
        <p className="text-[0.85rem] leading-snug text-tinta">{detalle}</p>
        {b.lote && <p className="text-[0.75rem] text-tinta-suave">{b.lote}</p>}
      </div>
    </div>
  );
}

function Kpi({ valor, etiqueta, nota, tono = "neutro" }) {
  const color = tono === "alerta" ? "text-rojo" : tono === "ok" ? "text-salvia" : "text-tinta";
  return (
    <div className="rounded-[var(--radius-card)] border border-linea bg-superficie px-4 py-3 sombra-papel">
      <p className="text-[0.72rem] uppercase tracking-wide text-tinta-suave">{etiqueta}</p>
      <p className={`plata mt-1 text-2xl font-medium ${color}`}>{valor}</p>
      {nota && <p className="mt-0.5 text-[0.75rem] text-tinta-suave">{nota}</p>}
    </div>
  );
}

function Esqueleto() {
  return (
    <div className="space-y-6" aria-busy="true">
      <div className="h-9 w-72 animate-pulse rounded bg-linea" />
      <div className="grid gap-3 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-20 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
        ))}
      </div>
      {[0, 1].map((i) => (
        <div key={i} className="h-56 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
      ))}
    </div>
  );
}
