import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow, Background, Controls, useNodesState, useEdgesState,
  Handle, Position, MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Snowflake, Factory, FlaskConical, Sprout, Users, Package,
  Scale, ArrowRightLeft, X, Route,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import { api } from "../lib/api";
import { num } from "../lib/format";

// ============================================================================
// EL MAPA REAL — la planta es el hub, no cuatro depósitos.
// ----------------------------------------------------------------------------
// Charla 22/08 con Papasud: la mercadería se hace en el campo, entra a planta
// (báscula → reclasificación → playa) y de ahí va a cliente o a frío. El frío
// es subcontratado y suele VOLVER a planta. Un lote, una variedad.
//
//     ORIGEN              HUB                 FRÍO              DESTINO
//   lab in vitro      recepción/báscula     Dospanca          Wemar-McCain
//   Santa Ana         PLANTA MdP            Pancani           Parmentier
//   Cayetano Chávez   reclasificación       Sasula
//   …                 playa de carga        Galpón MdP
// ============================================================================

const W = { origen: 210, hub: 300, frio: 200, destino: 196 };
const COL = { origen: 8, hub: 280, frio: 640, destino: 900 };
const EJE = 220;

const ICONO = {
  laboratorio: FlaskConical, campo: Sprout, planta: Factory,
  frigorifico: Snowflake, cliente: Users, marca: Package,
};

const COLOR_ARISTA = {
  ingreso_tolva: "#2b7a8c",
  envio_frio: "#6e6a63",
  retiro_frio: "#2f7d5b",
  entrega_cliente: "#2f7d5b",
  campo_a_frio: "#de7c1a",
  multiplicacion: "#c4c0b8",
};

function Handles() {
  return (
    <>
      <Handle type="target" position={Position.Left} id="t-l" style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} id="s-r" style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Top} id="t-t" style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} id="s-b" style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Bottom} id="t-b" style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Top} id="s-t" style={{ opacity: 0 }} />
    </>
  );
}

function NodoFlujo({ data }) {
  const Icono = ICONO[data.tipo] || Package;
  const esHub = data.tipo === "planta";
  const apagado = data.atenuado;
  return (
    <div
      className="rounded-xl border-2 transition-opacity"
      style={{
        borderColor: data.resaltado ? "#2b7a8c" : esHub ? "#2f7d5b" : "#ddd9d2",
        background: esHub ? "#f2f8f5" : "#fff",
        width: data.ancho,
        padding: esHub ? "12px 14px" : "9px 11px",
        opacity: apagado ? 0.16 : 1,
        boxShadow: esHub
          ? "0 4px 16px rgba(47,125,91,.16)"
          : "0 1px 3px rgba(33,32,29,.05)",
      }}
    >
      <Handles />
      <div className="flex items-start gap-2">
        <Icono size={esHub ? 20 : 15} className="mt-0.5 shrink-0 text-tinta-suave" />
        <div className="min-w-0 flex-1">
          <p className={`truncate font-display font-bold leading-tight ${esHub ? "text-[1.05rem]" : "text-[0.92rem]"}`}>
            {data.etiqueta}
          </p>
          {data.subtitulo && (
            <p className="truncate text-[0.74rem] text-tinta-suave">{data.subtitulo}</p>
          )}
        </div>
      </div>
      {data.metricas && (
        <p className="mt-1.5 text-[0.78rem] tabular-nums text-tinta-suave">
          {data.metricas.toneladas != null && `${num(data.metricas.toneladas)} t`}
          {data.metricas.kg != null && data.metricas.toneladas == null && `${num(Math.round(data.metricas.kg))} kg`}
          {data.metricas.lotes != null && ` · ${data.metricas.lotes} lotes`}
          {data.metricas.entregas != null && ` · ${data.metricas.entregas} entregas`}
        </p>
      )}
      {esHub && data.zonas && (
        <div className="mt-2 flex flex-wrap gap-1">
          {data.zonas.map((z) => (
            <span key={z.id} className="rounded bg-salvia/10 px-1.5 py-0.5 text-[0.66rem] font-medium text-salvia">
              {z.nombre}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

const TIPOS = { flujo: NodoFlujo };

function Kpi({ valor, etiqueta, tono }) {
  return (
    <div className="text-right">
      <p className={`plata text-[1.35rem] font-medium leading-none tabular-nums ${tono === "alerta" ? "text-rojo" : ""}`}>
        {valor}
      </p>
      <p className="mt-0.5 text-[0.7rem] text-tinta-suave">{etiqueta}</p>
    </div>
  );
}

function columna(lista, x, ancho, alto, y0) {
  return lista.map((n, i) => ({
    id: n.id, type: "flujo", draggable: false,
    position: { x, y: y0 + i * alto },
    data: { ...n, ancho },
  }));
}

export default function MapaFlujoPapasud({ onPreguntar }) {
  const [d, setD] = useState(null);
  const [foco, setFoco] = useState(null);
  const [detalle, setDetalle] = useState(null);

  useEffect(() => { api.mapaPapasud().then(setD).catch(() => setD(false)); }, []);

  const { nodosBase, aristasBase } = useMemo(() => {
    if (!d || !d.nodos) return { nodosBase: [], aristasBase: [] };
    const origen = d.nodos.filter((n) => n.capa === "origen");
    const planta = d.nodos.find((n) => n.tipo === "planta");
    const frios = d.nodos.filter((n) => n.tipo === "frigorifico");
    const destinos = d.nodos.filter((n) => n.capa === "destino");

    const nodos = [
      ...columna(origen, COL.origen, W.origen, 78, 8),
    ];
    if (planta) {
      nodos.push({
        id: planta.id, type: "flujo", draggable: false,
        position: { x: COL.hub, y: EJE - 40 },
        data: { ...planta, ancho: W.hub },
        zIndex: 8,
      });
    }
    nodos.push(...columna(frios, COL.frio, W.frio, 86, 16));
    nodos.push(...columna(destinos, COL.destino, W.destino, 90, EJE - destinos.length * 45));

    const aristas = (d.aristas || []).map((a) => {
      const color = COLOR_ARISTA[a.tipo] || "#c4c0b8";
      const esTolva = a.tipo === "ingreso_tolva";
      const esAtajo = a.tipo === "campo_a_frio" || (a.tipo === "entrega_cliente" && a.origen?.startsWith("campo"));
      return {
        id: a.id,
        source: a.origen, target: a.destino,
        sourceHandle: "s-r", targetHandle: "t-l",
        type: "bezier",
        style: {
          stroke: color,
          strokeWidth: esTolva ? Math.max(1.8, Math.min(5, a.kg / 80000)) : 1.6,
          strokeDasharray: esAtajo ? "6 4" : undefined,
        },
        markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color },
        label: a.kg ? `${num(Math.round(a.kg / 1000))} t` : undefined,
        labelStyle: { fontSize: 10, fill: "#6f6a61" },
        labelBgStyle: { fill: "#fff", fillOpacity: 0.9 },
        labelBgPadding: [3, 2],
        data: a,
      };
    });
    return { nodosBase: nodos, aristasBase: aristas };
  }, [d]);

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  useEffect(() => { setNodes(nodosBase); setEdges(aristasBase); },
    [nodosBase, aristasBase, setNodes, setEdges]);

  const iluminar = useCallback((h) => {
    if (!h) { setFoco(null); setNodes(nodosBase); setEdges(aristasBase); return; }
    setFoco(h.id);
    const enCamino = new Set(h.camino?.nodos || []);
    setNodes(nodosBase.map((n) => ({
      ...n,
      data: { ...n.data, atenuado: !enCamino.has(n.id), resaltado: enCamino.has(n.id) },
    })));
    setEdges(aristasBase.map((a) => {
      const puntas = enCamino.has(a.source) && enCamino.has(a.target);
      return { ...a, style: { ...a.style, opacity: puntas ? 1 : 0.08 } };
    }));
  }, [nodosBase, aristasBase, setNodes, setEdges]);

  if (d === null) {
    return <div className="h-[28rem] animate-pulse rounded-[var(--radius-card)] bg-crema/60" />;
  }
  if (d === false) {
    return <p className="text-tinta-suave">No pude armar el mapa del flujo.</p>;
  }

  const r = d.resumen || {};

  return (
    <div className="space-y-3">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">El flujo de la mercadería</h1>
          <p className="mt-1 max-w-[42rem] text-[0.95rem] text-tinta-suave">
            {d.regla}
          </p>
        </div>
        <div className="flex flex-wrap gap-5 text-right">
          <Kpi valor={`${num(Math.round((r.kg_en_planta || 0) / 1000))} t`} etiqueta="En planta" />
          <Kpi valor={`${num(Math.round((r.kg_en_frio || 0) / 1000))} t`} etiqueta="En frío" />
          <Kpi valor={num(r.recepciones)} etiqueta="Recepciones" />
          <Kpi valor={num(r.ordenes_carga)} etiqueta="Órdenes de carga" />
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-1.5">
        {(d.hallazgos || []).map((h) => (
          <button
            key={h.id}
            type="button"
            onClick={() => iluminar(foco === h.id ? null : h)}
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.78rem] transition
              ${foco === h.id ? "border-hielo bg-hielo/10 text-hielo" : "border-linea hover:bg-crema"}`}
          >
            <Route size={12} />
            {h.titulo}
          </button>
        ))}
        {foco && (
          <button type="button" onClick={() => iluminar(null)}
                  className="flex items-center gap-1 rounded-full border border-linea px-2.5 py-1 text-[0.78rem] text-tinta-suave">
            <X size={12} /> ver todo
          </button>
        )}
      </div>

      {foco && (
        <AngelaSays tone="atencion">
          {(d.hallazgos.find((h) => h.id === foco) || {}).detalle}
        </AngelaSays>
      )}

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[0.74rem] text-tinta-suave">
        <span className="flex items-center gap-1.5">
          <svg width="26" height="8"><line x1="0" y1="4" x2="26" y2="4" stroke="#2b7a8c" strokeWidth="3" /></svg>
          Tolva campo → planta
        </span>
        <span className="flex items-center gap-1.5">
          <svg width="26" height="8"><line x1="0" y1="4" x2="26" y2="4" stroke="#2f7d5b" strokeWidth="2.5" /></svg>
          Retiro de frío / entrega
        </span>
        <span className="flex items-center gap-1.5">
          <svg width="26" height="8"><line x1="0" y1="4" x2="26" y2="4" stroke="#de7c1a" strokeWidth="2" strokeDasharray="6 4" /></svg>
          Atajo (campo → frío o cliente)
        </span>
        <span className="ml-auto">Tocá un nodo para ver lotes y variedades</span>
      </div>

      <div className="relative h-[34rem] overflow-hidden rounded-[var(--radius-card)] border border-linea bg-crema/40">
        <div className="pointer-events-none absolute inset-x-0 top-0 z-10 grid grid-cols-4 border-b border-linea bg-superficie/85 px-4 py-1.5 backdrop-blur">
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
          nodeTypes={TIPOS}
          onNodeClick={(_e, node) => setDetalle(node.data)}
          onPaneClick={() => setDetalle(null)}
          fitView
          fitViewOptions={{ padding: 0.06 }}
          minZoom={0.28}
          maxZoom={1.6}
          nodesDraggable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={24} size={1} color="#e4e1db" />
          <Controls position="bottom-right" showInteractive={false} />
        </ReactFlow>

        {detalle && (
          <Panel detalle={detalle} onPreguntar={onPreguntar} onCerrar={() => setDetalle(null)} />
        )}
      </div>
    </div>
  );
}

function Panel({ detalle, onPreguntar, onCerrar }) {
  const grupos = detalle.grupos || [];
  const zonas = detalle.zonas || [];
  return (
    <aside className="absolute right-3 top-11 z-20 max-h-[calc(100%-3.5rem)] w-[22rem] space-y-3 overflow-y-auto rounded-[var(--radius-card)] border border-linea bg-superficie p-4 sombra-alta">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[0.68rem] uppercase tracking-wide text-tinta-suave">{detalle.tipo}</p>
          <h2 className="font-display text-[1.05rem] font-bold leading-tight">{detalle.etiqueta}</h2>
          {detalle.subtitulo && (
            <p className="mt-0.5 text-[0.8rem] text-tinta-suave">{detalle.subtitulo}</p>
          )}
        </div>
        <button type="button" onClick={onCerrar} className="shrink-0 rounded-lg p-1 text-tinta-suave hover:bg-crema">
          <X size={16} />
        </button>
      </div>

      {detalle.detalle && (
        <p className="rounded-lg bg-crema/70 px-3 py-2 text-[0.82rem] leading-snug">{detalle.detalle}</p>
      )}

      {detalle.metricas && (
        <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[0.82rem]">
          {Object.entries(detalle.metricas)
            .filter(([, v]) => v != null && typeof v !== "object")
            .map(([k, v]) => (
              <div key={k}>
                <dt className="text-[0.68rem] text-tinta-suave">{k.replaceAll("_", " ")}</dt>
                <dd className="tabular-nums font-medium">{typeof v === "number" ? num(v) : String(v)}</dd>
              </div>
            ))}
        </dl>
      )}

      {zonas.length > 0 && (
        <section>
          <h3 className="mb-1.5 flex items-center gap-1.5 text-[0.68rem] font-semibold uppercase tracking-wide text-tinta-suave">
            <Scale size={12} /> Estaciones de la planta
          </h3>
          <ul className="space-y-2">
            {zonas.map((z) => (
              <li key={z.id} className="rounded-lg border border-linea px-2.5 py-2">
                <p className="text-[0.82rem] font-semibold">{z.nombre}</p>
                <p className="text-[0.74rem] text-tinta-suave">{z.detalle}</p>
                {z.kg_ingresados != null && (
                  <p className="mt-1 text-[0.78rem] tabular-nums">{num(Math.round(z.kg_ingresados))} kg recibidos · {z.recepciones} camiones</p>
                )}
                {z.kg_embolsados != null && (
                  <p className="mt-1 text-[0.78rem] tabular-nums">{num(z.bolsas)} bolsas · {num(Math.round(z.kg_embolsados))} kg</p>
                )}
                {z.kg_envio_frio != null && (
                  <p className="mt-1 text-[0.78rem] tabular-nums">
                    a frío {num(Math.round(z.kg_envio_frio))} kg · retiro {num(Math.round(z.kg_retiro_frio))} kg
                  </p>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}

      {grupos.length > 0 && (
        <section>
          <h3 className="mb-1 text-[0.68rem] font-semibold uppercase tracking-wide text-tinta-suave">
            Por variedad · un lote, una sola
          </h3>
          <ul className="space-y-0.5 text-[0.82rem]">
            {grupos.map((g) => (
              <li key={g.variedad_id || g.variedad} className="flex justify-between gap-2">
                <span>{g.variedad} · {g.n ?? (Array.isArray(g.lotes) ? g.lotes.length : g.lotes)} lotes</span>
                <span className="tabular-nums text-tinta-suave">{num(Math.round(g.kg))} kg</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {onPreguntar && detalle.etiqueta && (
        <button
          type="button"
          onClick={() => onPreguntar(`¿cuánto hay en ${detalle.etiqueta}?`)}
          className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-linea px-3 py-2 text-[0.82rem] hover:bg-crema"
        >
          <ArrowRightLeft size={13} /> preguntar por este lugar
        </button>
      )}
    </aside>
  );
}
