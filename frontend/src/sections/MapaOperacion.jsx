import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow, Background, Controls, useNodesState, useEdgesState,
  Handle, Position, MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Snowflake, Warehouse, FlaskConical, Sprout, Ship, Users, Package,
  CalendarRange, Globe, Anchor, Lock, ArrowRight, X, Route,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import { api } from "../lib/api";
import { num, peso, pesoCorto, fecha } from "../lib/format";
import { useT } from "../lib/i18n";

// ============================================================================
// EL MAPA DE LA OPERACIÓN — con el stock en el centro.
// ----------------------------------------------------------------------------
// Tres capas fijas, y el orden es el del negocio:
//
//     ORIGEN          →        CENTRO         →        DESTINO
//   laboratorio            LAS 4 UBICACIONES        órdenes · clientes
//   campos                 los lotes                puerto · país
//   campañas · variedades  movimientos
//
// El ojo va de izquierda a derecha y PASA OBLIGATORIAMENTE POR EL STOCK.
//
// POR QUÉ NO UN GRAFO DE FUERZAS. Se ve espectacular en una captura y se lee
// mal en vivo: los nodos se acomodan solos y la posición no significa nada. Si
// alguien pregunta «¿por qué ese nodo está ahí?», con un force-graph la
// respuesta honesta es «porque el algoritmo lo puso ahí». Acá es «porque eso es
// el origen y aquello el destino». La exploración libre vive en el Cerebro.
//
// GOTCHA de React Flow v12: los nodos TIENEN que pasar por useNodesState —
// pasarlos como prop plana los deja invisibles.
// ============================================================================

const COL = { origen: 40, centro: 560, destino: 1080 };
const ANCHO = { origen: 200, centro: 300, destino: 220 };

const ICONO = {
  laboratorio: FlaskConical, campo: Sprout, campania: CalendarRange,
  variedad: Package, ubicacion: Snowflake, orden: Ship, cliente: Users,
  puerto: Anchor, pais: Globe,
};

const TONO = {
  verde: { borde: "#2f7d5b", fondo: "#f2f8f5" },
  amarillo: { borde: "#de7c1a", fondo: "#fdf7ef" },
  rojo: { borde: "#d2372b", fondo: "#fdf3f2" },
  neutro: { borde: "#e9e7e2", fondo: "#ffffff" },
};

// --- el nodo ----------------------------------------------------------------
function NodoOperacion({ data }) {
  const Icono = ICONO[data.tipo] || Package;
  const t = TONO[data.estado] || TONO.neutro;
  const esCentro = data.capa === "centro";
  const apagado = data.atenuado;

  return (
    <div
      className="rounded-xl border-2 px-3 py-2.5 transition-opacity"
      style={{
        borderColor: data.resaltado ? "#2b7a8c" : t.borde,
        background: t.fondo,
        width: ANCHO[data.capa],
        opacity: apagado ? 0.22 : 1,
        boxShadow: data.resaltado
          ? "0 0 0 3px rgba(43,122,140,.18)"
          : esCentro ? "0 2px 10px rgba(33,32,29,.07)" : "none",
      }}
    >
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <div className="flex items-start gap-2">
        <Icono size={esCentro ? 17 : 14} className="mt-0.5 shrink-0 text-tinta-suave" />
        <div className="min-w-0 flex-1">
          <p className={`truncate font-display font-bold leading-tight ${esCentro ? "text-[0.95rem]" : "text-[0.82rem]"}`}>
            {data.etiqueta}
          </p>
          {data.subtitulo && (
            <p className="truncate text-[0.68rem] text-tinta-suave">{data.subtitulo}</p>
          )}
        </div>
        {data.bloqueada && <Lock size={13} className="mt-0.5 shrink-0 text-rojo" />}
      </div>

      {esCentro && data.metricas && (
        <>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="plata text-lg font-medium">{num(data.metricas.toneladas)} t</span>
            <span className="text-[0.68rem] text-tinta-suave">
              {data.metricas.lotes} lotes
            </span>
          </div>
          <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-linea">
            <div className="h-full rounded-full"
                 style={{ width: `${Math.min(100, data.metricas.ocupacion_pct || 0)}%`,
                          background: data.metricas.ocupacion_pct > 90 ? "#de7c1a" : "#2b7a8c" }} />
          </div>
          <div className="mt-1.5 flex flex-wrap gap-1 text-[0.62rem]">
            {data.metricas.diferencias > 0 && (
              <span className="rounded bg-rojo/10 px-1.5 py-px text-rojo">
                {data.metricas.diferencias} dif.
              </span>
            )}
            {data.metricas.por_brotar > 0 && (
              <span className="rounded bg-oro/10 px-1.5 py-px text-oro">
                {data.metricas.por_brotar} por brotar
              </span>
            )}
            {data.metricas.ya_brotados > 0 && (
              <span className="rounded bg-linea px-1.5 py-px text-tinta-suave">
                {data.metricas.ya_brotados} brotados
              </span>
            )}
          </div>
        </>
      )}

      {!esCentro && data.metricas && (
        <p className="mt-1 text-[0.7rem] tabular-nums text-tinta-suave">
          {data.metricas.toneladas != null && `${num(data.metricas.toneladas)} t`}
          {data.metricas.kg != null && `${num(data.metricas.kg)} kg`}
          {data.metricas.lotes != null && ` · ${data.metricas.lotes} lotes`}
          {data.metricas.ordenes != null && ` · ${data.metricas.ordenes} órd.`}
        </p>
      )}
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </div>
  );
}

const TIPOS_NODO = { operacion: NodoOperacion };

export default function MapaOperacion({ onPreguntar }) {
  const t = useT();
  const [d, setD] = useState(null);
  const [foco, setFoco] = useState(null);         // el hallazgo iluminado
  const [detalle, setDetalle] = useState(null);   // el panel lateral
  const [genealogia, setGenealogia] = useState(null);

  useEffect(() => { api.mapa().then(setD).catch(() => setD(false)); }, []);

  // --- posiciones: capas fijas, apiladas por capa ---------------------------
  const { nodosBase, aristasBase } = useMemo(() => {
    if (!d || !d.nodos) return { nodosBase: [], aristasBase: [] };
    const porCapa = { origen: [], centro: [], destino: [] };
    d.nodos.forEach((n) => (porCapa[n.capa] || porCapa.origen).push(n));

    const alto = { origen: 74, centro: 150, destino: 84 };
    const nodos = [];
    for (const capa of ["origen", "centro", "destino"]) {
      const lista = porCapa[capa];
      // se centran verticalmente entre sí para que las tres capas queden
      // ópticamente alineadas aunque tengan distinta cantidad de nodos
      const alturaTotal = lista.length * alto[capa];
      const y0 = 620 - alturaTotal / 2;
      lista.forEach((n, i) => {
        nodos.push({
          id: n.id,
          type: "operacion",
          position: { x: COL[capa], y: y0 + i * alto[capa] },
          data: { ...n },
          draggable: false,
        });
      });
    }

    const aristas = d.aristas.map((a) => ({
      id: a.id,
      source: a.origen,
      target: a.destino,
      // Los movimientos SIN CONFIRMAR van punteados: esos kilos salieron de
      // una cámara y nadie los vio llegar. Es el problema del brief, dibujado.
      animated: !!a.alerta,
      style: {
        stroke: a.alerta ? "#d2372b" : a.tipo === "movimiento" ? "#2b7a8c" : "#d8d5cf",
        strokeWidth: a.tipo === "movimiento"
          ? Math.max(1.2, Math.min(5, (a.kg || 0) / 60000)) : 1.2,
        strokeDasharray: a.alerta ? "6 4" : undefined,
      },
      markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14,
                   color: a.alerta ? "#d2372b" : "#c9c5be" },
      label: a.tipo === "movimiento" && a.en_transito
        ? `${num(a.kg_en_transito)} kg sin confirmar` : undefined,
      labelStyle: { fontSize: 10, fill: "#d2372b" },
      labelBgStyle: { fill: "#fff" },
      data: a,
    }));
    return { nodosBase: nodos, aristasBase: aristas };
  }, [d]);

  // GOTCHA React Flow v12: sin useNodesState los nodos quedan invisibles.
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => { setNodes(nodosBase); setEdges(aristasBase); },
    [nodosBase, aristasBase, setNodes, setEdges]);

  // --- iluminar el camino de un hallazgo -----------------------------------
  const iluminar = useCallback((h) => {
    if (!h) { setFoco(null); setNodes(nodosBase); setEdges(aristasBase); return; }
    setFoco(h.id);
    const enCamino = new Set(h.camino.nodos);
    const aristasCamino = new Set(h.camino.aristas);
    setNodes(nodosBase.map((n) => ({
      ...n,
      data: { ...n.data, atenuado: !enCamino.has(n.id), resaltado: enCamino.has(n.id) },
    })));
    setEdges(aristasBase.map((a) => ({
      ...a,
      animated: aristasCamino.has(a.id) || a.animated,
      style: {
        ...a.style,
        opacity: aristasCamino.has(a.id) ? 1
          : (enCamino.has(a.source) && enCamino.has(a.target)) ? 1 : 0.12,
        strokeWidth: aristasCamino.has(a.id) ? 3 : a.style.strokeWidth,
      },
    })));
  }, [nodosBase, aristasBase, setNodes, setEdges]);

  // --- al tocar un nodo: cambia el panel, NO mueve la cámara ---------------
  const alTocarNodo = useCallback(async (_e, node) => {
    setDetalle(node.data);
    setGenealogia(null);
    if (node.data.tipo === "ubicacion" && node.data.grupos?.length) {
      // el primer lote del grupo más grande, como muestra de la genealogía
      const cod = node.data.grupos[0]?.codigos?.[0];
      if (cod) {
        try { setGenealogia(await api.genealogia(String(cod))); } catch { /* sin genealogía el panel igual sirve */ }
      }
    }
  }, []);

  if (d === null) return <Esqueleto />;
  if (d === false) return <p className="text-tinta-suave">{t("mapa.error")}</p>;

  const r = d.resumen || {};

  return (
    <div className="space-y-4">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">{t("mapa.titulo")}</h1>
          <p className="mt-1 text-[0.95rem] text-tinta-suave">{t("mapa.subtitulo")}</p>
        </div>
        <div className="flex flex-wrap gap-4 text-right">
          <Kpi valor={`${num(r.toneladas)} t`} etiqueta={t("mapa.k_stock")} />
          <Kpi valor={pesoCorto(r.valor)} etiqueta={t("mapa.k_valor")} />
          <Kpi valor={num(r.diferencias)} etiqueta={t("mapa.k_dif")}
               tono={r.diferencias ? "alerta" : "ok"} />
          <Kpi valor={`${num(r.kg_en_transito)} kg`} etiqueta={t("mapa.k_transito")}
               tono={r.kg_en_transito ? "alerta" : "ok"} />
        </div>
      </header>

      {/* los hallazgos: cada uno ilumina SU camino en el lienzo */}
      <div className="flex flex-wrap gap-1.5">
        {(d.hallazgos || []).map((h) => (
          <button
            key={h.id}
            type="button"
            onClick={() => iluminar(foco === h.id ? null : h)}
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.78rem] transition
              ${foco === h.id
                ? "border-hielo bg-hielo/10 text-hielo"
                : "border-linea hover:bg-crema"}`}
          >
            <Route size={12} />
            {h.titulo}
          </button>
        ))}
        {foco && (
          <button type="button" onClick={() => iluminar(null)}
                  className="flex items-center gap-1 rounded-full border border-linea px-2.5 py-1 text-[0.78rem] text-tinta-suave">
            <X size={12} /> {t("mapa.ver_todo")}
          </button>
        )}
      </div>

      {foco && (
        <AngelaSays tone="atencion">
          {(d.hallazgos.find((h) => h.id === foco) || {}).detalle}
        </AngelaSays>
      )}

      <div className="grid gap-4 xl:grid-cols-[1fr_20rem]">
        {/* el lienzo */}
        <div className="relative h-[34rem] overflow-hidden rounded-[var(--radius-card)] border border-linea bg-crema/40">
          {/* los rótulos de capa: sin esto el orden hay que explicarlo */}
          <div className="pointer-events-none absolute inset-x-0 top-0 z-10 flex justify-around border-b border-linea bg-superficie/85 px-4 py-1.5 backdrop-blur">
            {(d.capas || []).map((c) => (
              <span key={c.id} className="text-[0.7rem] font-semibold uppercase tracking-wide text-tinta-suave">
                {c.titulo}
              </span>
            ))}
          </div>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={TIPOS_NODO}
            onNodeClick={alTocarNodo}
            fitView
            fitViewOptions={{ padding: 0.12 }}
            minZoom={0.2}
            maxZoom={1.4}
            proOptions={{ hideAttribution: true }}
          >
            <Background gap={22} size={1} color="#e4e1db" />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>

        {/* el panel: lo que sea que estés mirando */}
        <Panel detalle={detalle} genealogia={genealogia} onPreguntar={onPreguntar} t={t} />
      </div>
    </div>
  );
}

// --- el panel lateral -------------------------------------------------------
function Panel({ detalle, genealogia, onPreguntar, t }) {
  if (!detalle) {
    return (
      <aside className="flex h-full min-h-[12rem] items-center justify-center rounded-[var(--radius-card)] border border-dashed border-linea px-4 text-center text-[0.85rem] text-tinta-suave">
        {t("mapa.toca_algo")}
      </aside>
    );
  }
  return (
    <aside className="space-y-3 overflow-y-auto rounded-[var(--radius-card)] border border-linea bg-superficie p-4 sombra-papel xl:max-h-[34rem]">
      <div>
        <p className="text-[0.68rem] uppercase tracking-wide text-tinta-suave">
          {t(`mapa.tipo_${detalle.tipo}`)}
        </p>
        <h2 className="font-display text-[1.05rem] font-bold leading-tight">{detalle.etiqueta}</h2>
        {detalle.subtitulo && (
          <p className="mt-0.5 text-[0.8rem] text-tinta-suave">{detalle.subtitulo}</p>
        )}
      </div>

      {detalle.detalle && (
        <p className="rounded-lg bg-crema/70 px-3 py-2 text-[0.82rem] leading-snug">
          {detalle.detalle}
        </p>
      )}

      {detalle.metricas && (
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[0.82rem]">
          {Object.entries(detalle.metricas)
            .filter(([, v]) => v != null)
            .map(([k, v]) => (
              <div key={k}>
                <dt className="text-[0.68rem] text-tinta-suave">{t(`mapa.m_${k}`)}</dt>
                <dd className="tabular-nums font-medium">
                  {k === "valor" ? peso(v) : typeof v === "number" ? num(v) : String(v)}
                </dd>
              </div>
            ))}
        </dl>
      )}

      {detalle.camaras?.length > 0 && (
        <p className="text-[0.78rem] text-tinta-suave">{detalle.camaras.join(" · ")}</p>
      )}

      {detalle.grupos?.length > 0 && (
        <section>
          <h3 className="mb-1 text-[0.68rem] font-semibold uppercase tracking-wide text-tinta-suave">
            {t("mapa.por_variedad")}
          </h3>
          <ul className="space-y-0.5 text-[0.82rem]">
            {detalle.grupos.map((g) => (
              <li key={g.id} className="flex justify-between gap-2">
                <span className="truncate">{g.variedad}</span>
                <span className="shrink-0 tabular-nums text-tinta-suave">
                  {num(g.kg / 1000)} t · {g.lotes}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {detalle.requisitos_onpf?.length > 0 && (
        <section>
          <h3 className="mb-1 text-[0.68rem] font-semibold uppercase tracking-wide text-tinta-suave">
            {t("mapa.requisitos")}
          </h3>
          <ul className="list-disc space-y-0.5 pl-4 text-[0.8rem] text-tinta-suave">
            {detalle.requisitos_onpf.map((x) => <li key={x}>{x}</li>)}
          </ul>
        </section>
      )}

      {detalle.motivos?.length > 0 && (
        <div className="rounded-lg border border-rojo/25 bg-rojo/[0.04] px-3 py-2">
          <p className="text-[0.78rem] font-medium text-rojo">{t("mapa.frenada_por")}</p>
          <ul className="mt-0.5 text-[0.8rem]">
            {detalle.motivos.map((m) => <li key={m}>· {m.replace(/_/g, " ")}</li>)}
          </ul>
        </div>
      )}

      {/* LA GENEALOGÍA: el camino completo del lote, de meristema a contenedor */}
      {genealogia?.encontrado && (
        <section>
          <h3 className="mb-1.5 flex items-center gap-1.5 text-[0.68rem] font-semibold uppercase tracking-wide text-tinta-suave">
            <Route size={11} /> {t("mapa.genealogia", { lote: genealogia.lote })}
          </h3>
          <ol className="space-y-2 border-l border-linea pl-3">
            {genealogia.etapas.map((e) => (
              <li key={e.id} className="relative">
                <span className={`absolute -left-[1.02rem] top-1.5 h-1.5 w-1.5 rounded-full
                  ${e.alerta ? "bg-rojo" : "bg-hielo"}`} />
                <p className={`text-[0.82rem] font-medium ${e.alerta ? "text-rojo" : ""}`}>
                  {e.titulo}
                </p>
                <p className="text-[0.75rem] leading-snug text-tinta-suave">{e.detalle}</p>
                <p className="text-[0.68rem] text-tinta-suave">
                  {e.fecha ? fecha(e.fecha) + " · " : ""}{e.fuente}
                </p>
                {e.nota && (
                  <p className="mt-0.5 text-[0.7rem] italic text-rojo">{e.nota}</p>
                )}
              </li>
            ))}
          </ol>
        </section>
      )}

      <button
        type="button"
        onClick={() => onPreguntar?.(t("mapa.pregunta", { que: detalle.etiqueta }))}
        className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-linea px-3 py-2 text-[0.83rem] transition hover:bg-crema"
      >
        {t("mapa.preguntar")} <ArrowRight size={13} />
      </button>
    </aside>
  );
}

function Kpi({ valor, etiqueta, tono = "neutro" }) {
  const c = tono === "alerta" ? "text-rojo" : tono === "ok" ? "text-salvia" : "text-tinta";
  return (
    <div>
      <p className={`plata text-lg font-medium leading-none ${c}`}>{valor}</p>
      <p className="mt-0.5 text-[0.68rem] uppercase tracking-wide text-tinta-suave">{etiqueta}</p>
    </div>
  );
}

function Esqueleto() {
  return (
    <div className="space-y-4" aria-busy="true">
      <div className="h-9 w-72 animate-pulse rounded bg-linea" />
      <div className="h-[34rem] animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
    </div>
  );
}
