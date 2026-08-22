import { useEffect, useMemo, useState } from "react";
import {
  ReactFlow, Background, Controls, useNodesState, useEdgesState,
  Handle, Position, MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Snowflake, Warehouse, Sprout, Users, Factory, Scale, X, TriangleAlert,
  ArrowRight, ChevronDown, Route, Sparkles, FileSpreadsheet,
} from "lucide-react";
import { api } from "../lib/api";

// ============================================================================
// EL MAPA DE LA OPERACIÓN — con la planta en el medio, que es donde va.
// ----------------------------------------------------------------------------
// El mapa anterior mandaba los lotes del campo al frío y vendía desde el
// frigorífico. Un empleado de Papasud lo ve en dos segundos, porque falta la
// planta. Textual de la charla con los dueños:
//
//   «El camión viene a Mar del Plata, entra a la planta, se baja a la báscula,
//    el camión pesa, el que recibe toma el peso y los datos: camionero, qué
//    camión, producto, todo. Y lo vuelca a la primera planilla de recepción.»
//
//   «Lote → planta → cliente. Muchas veces va a la planta, va al frigorífico,
//    VUELVE A LA PLANTA y sale al cliente. Eso es muy común.»
//
//     CAMPOS      →     PLANTA MDP     ⇄     FRIGORÍFICOS   →   CLIENTES
//     pivote            (la báscula)         subcontratados
//     cuadrante         ── ida  ──▶
//     lote              ◀── vuelta ──
//
// EL IDA Y VUELTA SE DIBUJA DOS VECES, no como una flecha de doble punta: la
// ida pasa por arriba y la vuelta por abajo. Es el circuito que más usan y el
// que peor siguen; si se esconde en una línea, no se ve que son dos viajes,
// dos fletes y dos oportunidades de perder la cuenta.
//
// LA CÁMARA NO SE MUEVE AL TOCAR. Reencuadrar en cada clic desorienta, y más
// proyectado en una sala. `fitView` corre UNA vez, al cargar.
//
// GOTCHA React Flow v12: los nodos TIENEN que pasar por useNodesState — como
// prop plana quedan invisibles.
// ============================================================================

const COL = { campo: 0, planta: 400, frio: 830, cliente: 1190 };
const W = { campo: 230, planta: 320, frio: 250, cliente: 220 };
const EJE_Y = 300;

const ICONO = {
  campo: Sprout, planta: Factory, galpon: Warehouse,
  frigorifico: Snowflake, cliente: Users, cliente_grupo: Users,
};

const GRAVEDAD = {
  grave: { punto: "bg-rojo", texto: "text-rojo", borde: "border-rojo/40",
           fondo: "bg-rojo/[0.05]", label: "Grave" },
  atencion: { punto: "bg-oro", texto: "text-oro-tinta", borde: "border-oro/40",
              fondo: "bg-oro/[0.05]", label: "Para mirar" },
  menor: { punto: "bg-tinta/30", texto: "text-tinta-suave", borde: "border-tinta/12",
           fondo: "bg-tinta/[0.02]", label: "Menor" },
};

// El color de una flecha dice QUÉ tramo es, no cuánto pesa.
const SENTIDO = {
  ingreso: { color: "#63605a", label: "del campo a la planta" },
  directo_a_frio: { color: "#9a958c", label: "del campo al frío, sin pasar por planta" },
  ida: { color: "#2b7a8c", label: "de la planta al frío" },
  vuelta: { color: "#2f7d5b", label: "vuelve del frío a la planta" },
  entre_frios: { color: "#9a958c", label: "entre frigoríficos" },
  venta: { color: "#21201d", label: "venta" },
  venta_directa: { color: "#9a958c", label: "venta directa desde el campo" },
  perdido: { color: "#d2372b", label: "salió y la planilla no dice adónde" },
};

const nkg = (n) => `${Math.round(n || 0).toLocaleString("es-AR")} kg`;
const nnum = (n) => Math.round(n || 0).toLocaleString("es-AR");
const nt = (n) => `${(Math.round((n || 0) / 100) / 10).toLocaleString("es-AR")} t`;

// ---------------------------------------------------------------------------
// Los nodos del lienzo
// ---------------------------------------------------------------------------
function Puertos() {
  return (
    <>
      <Handle type="target" position={Position.Left} style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} style={{ opacity: 0 }} />
    </>
  );
}

function NodoMapa({ data }) {
  const Icon = ICONO[data.tipo] || Snowflake;
  const esPlanta = data.tipo === "planta";
  const alerta = data.alerta || (data.tipo === "frigorifico" && data.kg === 0);

  return (
    <div
      style={{ width: data.ancho }}
      className={`rounded-2xl border-2 px-4 py-3 text-left transition
        ${esPlanta ? "border-tinta bg-crema shadow-lg" : "bg-crema"}
        ${alerta ? "border-rojo/50" : esPlanta ? "" : "border-tinta/15"}
        ${data.apagado ? "opacity-25" : ""}
        ${data.encendido ? "ring-4 ring-violeta/30" : ""}`}
    >
      <Puertos />
      <div className="flex items-center gap-2">
        <Icon size={esPlanta ? 22 : 17}
              className={alerta ? "text-rojo" : esPlanta ? "text-tinta" : "text-tinta-suave"} />
        <span className={`flex-1 font-semibold leading-tight ${esPlanta ? "text-lg" : "text-[0.92rem]"}`}>
          {data.etiqueta}
        </span>
      </div>

      {esPlanta && data.bascula && (
        // La báscula no es un adorno: es donde nace el dato. Se dice.
        <span className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-tinta
                         px-2.5 py-1 text-[0.68rem] font-semibold text-crema">
          <Scale size={12} /> BÁSCULA
        </span>
      )}

      <p className={`mt-2 tabular-nums font-semibold ${esPlanta ? "text-2xl" : "text-lg"}`}>
        {nkg(data.kg)}
      </p>
      {data.subtitulo && (
        <p className="mt-0.5 text-[0.72rem] leading-snug text-tinta-suave">{data.subtitulo}</p>
      )}

      {data.comprometido > 0 && (
        <p className="mt-1.5 text-[0.72rem] text-oro-tinta">
          {nkg(data.comprometido)} comprometidos · {nkg(data.libre)} libres
        </p>
      )}
      {data.variedades?.length > 0 && (
        <p className="mt-1.5 truncate text-[0.72rem] text-tinta-suave">
          {data.variedades.slice(0, 3).map((v) => v.variedad || v).join(" · ")}
        </p>
      )}
    </div>
  );
}

const TIPOS_NODO = { mapa: NodoMapa };

// ---------------------------------------------------------------------------
export default function MapaOperacion({ onPreguntar }) {
  const [d, setD] = useState(null);
  const [foco, setFoco] = useState(null);        // el hallazgo iluminado
  const [abierto, setAbierto] = useState(null);  // el nodo del panel
  const [detalle, setDetalle] = useState(null);

  useEffect(() => { api.cerebroMapa().then(setD).catch(() => setD(false)); }, []);

  const encendidos = useMemo(() => {
    if (!foco || !d) return null;
    const h = (d.hallazgos.familias || [])
      .flatMap((f) => f.items).find((i) => i.id === foco);
    return h?.nodos?.length ? new Set(h.nodos) : null;
  }, [foco, d]);

  const { nodos, aristas } = useMemo(() => {
    if (!d?.nodos) return { nodos: [], aristas: [] };

    const porCapa = (c) => d.nodos.filter((n) => n.capa === c);
    const nodos = [];
    const columna = (lista, x, ancho, alto) => {
      const y0 = EJE_Y - (lista.length * alto) / 2;
      lista.forEach((n, i) => nodos.push({
        id: n.id, type: "mapa", draggable: false,
        // El tamaño va declarado: React Flow v12 esconde el nodo hasta que lo
        // MIDE, y si el ResizeObserver no llega a correr queda un lienzo en
        // blanco sin un solo error en consola. Declarándolo, no hay que medir.
        width: ancho, height: alto - 26,
        position: { x, y: y0 + i * alto },
        data: {
          ...n, ancho,
          encendido: encendidos?.has(n.id),
          apagado: encendidos ? !encendidos.has(n.id) : false,
        },
      }));
    };
    columna(porCapa("campo"), COL.campo, W.campo, 150);
    columna(porCapa("planta"), COL.planta, W.planta, 210);
    columna(porCapa("frio"), COL.frio, W.frio, 132);
    columna(porCapa("cliente"), COL.cliente, W.cliente, 108);

    const aristas = [];
    for (const a of d.aristas) {
      if (a.destino === "sin_destino") continue;   // se cuenta arriba, no se dibuja
      const s = SENTIDO[a.sentido] || SENTIDO.venta;
      // La ida sale por la derecha y entra por la izquierda; la vuelta sale por
      // abajo y entra por abajo. Así el circuito se ve como los dos viajes que es.
      const vuelta = a.sentido === "vuelta";
      const grueso = Math.max(1.5, Math.min(9, a.kg / 120000));
      aristas.push({
        id: a.id, source: a.origen, target: a.destino,
        // La vuelta se dibuja escalonada y en verde, la ida curva y en azul:
        // son dos viajes distintos y se tienen que ver como dos.
        type: vuelta ? "smoothstep" : "default",
        pathOptions: vuelta ? { offset: 46, borderRadius: 18 } : undefined,
        style: {
          stroke: s.color,
          strokeWidth: grueso,
          opacity: encendidos ? 0.12 : (a.sentido === "venta" ? 0.5 : 0.75),
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: s.color, width: 16, height: 16 },
        label: a.kg > 200000 ? nt(a.kg) : undefined,
        labelStyle: { fontSize: 11, fill: s.color, fontWeight: 600 },
        labelBgStyle: { fill: "#fbfbfa" },
      });
    }
    return { nodos, aristas };
  }, [d, encendidos]);

  const abrir = async (nid) => {
    setAbierto(nid);
    setDetalle(null);
    try { setDetalle(await api.cerebroNodo(nid)); } catch { setDetalle(false); }
  };

  if (d === null) return <Esqueleto />;
  if (d === false) {
    return <p className="text-tinta-suave">
      El mapa necesita la planilla importada. Corré
      <code className="mx-1 rounded bg-tinta/8 px-1.5 py-0.5">python data-papasud/planilla_real.py</code>
    </p>;
  }

  const r = d.resumen;

  return (
    <div className="space-y-5">
      <header>
        <h1 className="font-display text-3xl font-bold">El mapa de la operación</h1>
        <p className="mt-1 text-[0.95rem] text-tinta-suave">
          Del lote al cliente, pasando por la planta. {r.campos} campos ·
          {" "}{r.ubicaciones} lugares que guardan · {nnum(r.movimientos)} movimientos.
        </p>
      </header>

      <Kpis r={r} />
      <Hallazgos h={d.hallazgos} foco={foco} setFoco={setFoco}
                 onAbrir={abrir} onPreguntar={onPreguntar} />

      <div className="relative h-[620px] overflow-hidden rounded-2xl border
                      border-tinta/10 bg-papel-hondo">
        <Leyenda />
        {nodos.length > 0 && <Lienzo nodos={nodos} aristas={aristas} onAbrir={abrir} />}

        {abierto && (
          <PanelNodo detalle={detalle} onCerrar={() => { setAbierto(null); setDetalle(null); }}
                     onPreguntar={onPreguntar} onLote={(l) => abrir(`lote:${l}`)} />
        )}
      </div>
    </div>
  );
}


// ---------------------------------------------------------------------------
// El lienzo vive aparte por una razón concreta de React Flow v12: `fitView`
// corre al MONTAR. Si el componente monta con la lista vacía y los nodos
// llegan después, el encuadre no ocurre nunca y React Flow los deja con
// `visibility: hidden` — un lienzo en blanco sin ningún error en consola.
//
// Montando el lienzo recién cuando hay nodos, el encuadre pasa una vez y
// después NO vuelve a pasar: tocar un nodo cambia el panel y no la cámara,
// que es lo que pidieron para no marear a nadie proyectando en vivo.
// ---------------------------------------------------------------------------
function Lienzo({ nodos, aristas, onAbrir }) {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState(nodos);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState(aristas);
  // Los cambios posteriores (encender el camino de un hallazgo) sólo tocan
  // `data`: no re-montan el lienzo, así que la cámara se queda quieta.
  useEffect(() => { setRfNodes(nodos); }, [nodos, setRfNodes]);
  useEffect(() => { setRfEdges(aristas); }, [aristas, setRfEdges]);

  return (
    <ReactFlow
      nodes={rfNodes} edges={rfEdges}
      onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
      nodeTypes={TIPOS_NODO}
      onNodeClick={(_, n) => onAbrir(n.id)}
      fitView
      fitViewOptions={{ padding: 0.1 }}
      minZoom={0.2} maxZoom={1.6}
      proOptions={{ hideAttribution: true }}
      nodesDraggable={false} nodesConnectable={false}
    >
      <Background gap={26} size={1} color="#e2e0da" />
      <Controls showInteractive={false} />
    </ReactFlow>
  );
}

// ---------------------------------------------------------------------------
// La franja de arriba. Cuatro números grandes, no nueve chiquitos.
// ---------------------------------------------------------------------------
function Kpis({ r }) {
  const items = [
    { valor: nt(r.kg), etiqueta: "en las cámaras y la planta",
      nota: `${nnum(r.lotes)} lotes` },
    { valor: nkg(r.kg_sin_destino), etiqueta: "salieron y no se sabe adónde",
      nota: `${r.movimientos_sin_destino} retiros sin destino`, tono: "rojo" },
    { valor: nkg(r.comprometido), etiqueta: "comprometidos en pedidos abiertos",
      nota: "tener no es poder vender", tono: "oro" },
    { valor: nnum(r.graves), etiqueta: "hallazgos graves",
      nota: `de ${nnum(r.hallazgos)} en total` },
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((k) => (
        <div key={k.etiqueta} className="rounded-2xl border border-tinta/10 bg-crema p-4">
          <p className={`font-display text-3xl font-bold tabular-nums leading-none
            ${k.tono === "rojo" ? "text-rojo" : k.tono === "oro" ? "text-oro-tinta" : ""}`}>
            {k.valor}
          </p>
          <p className="mt-2 text-[0.85rem] font-medium leading-snug">{k.etiqueta}</p>
          <p className="mt-0.5 text-[0.75rem] text-tinta-suave">{k.nota}</p>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Los hallazgos. Uno arriba de todo, el resto agrupado, la cola escondida.
// ---------------------------------------------------------------------------
function Hallazgos({ h, foco, setFoco, onAbrir, onPreguntar }) {
  const [todas, setTodas] = useState(false);
  const familias = h.familias || [];
  if (!familias.length) return null;

  // Lo primero que se lee es lo que se puede evitar hoy: la venta que todavía
  // no se cayó. El resto es historia que hay que arreglar.
  const urgente = familias[0].gravedad === "grave" ? familias[0] : null;
  const resto = urgente ? familias.slice(1) : familias;
  const visibles = todas ? resto : resto.slice(0, 3);

  return (
    <div className="space-y-3">
      {urgente && (
        <BannerUrgente f={urgente} foco={foco} setFoco={setFoco}
                       onAbrir={onAbrir} onPreguntar={onPreguntar} />
      )}
      <div className="grid gap-3 md:grid-cols-3">
        {visibles.map((f) => (
          <TarjetaFamilia key={f.id} f={f} foco={foco} setFoco={setFoco} />
        ))}
      </div>
      {resto.length > 3 && (
        <button onClick={() => setTodas(!todas)}
                className="flex min-h-[44px] items-center gap-2 text-sm font-medium
                           text-tinta-suave hover:text-tinta">
          <ChevronDown size={16} className={todas ? "rotate-180" : ""} />
          {todas ? "Ver menos" : `Ver los otros ${resto.length - 3} grupos`}
        </button>
      )}
    </div>
  );
}

function BannerUrgente({ f, foco, setFoco, onAbrir, onPreguntar }) {
  const g = GRAVEDAD[f.gravedad];
  const d = f.destacado;
  return (
    <div className={`rounded-2xl border-2 ${g.borde} ${g.fondo} p-5`}>
      <div className="flex flex-wrap items-start gap-3">
        <TriangleAlert className="mt-0.5 h-6 w-6 shrink-0 text-rojo" />
        <div className="min-w-[16rem] flex-1">
          <p className="text-[0.75rem] font-semibold uppercase tracking-wider text-rojo">
            {f.titulo} · {f.cantidad}
          </p>
          <p className="mt-1 font-display text-xl font-semibold leading-snug">{d.titulo}</p>
          <p className="mt-1 text-[0.95rem] text-tinta-suave">{d.detalle}</p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {d.nodos?.length > 0 && (
            <button onClick={() => setFoco(foco === d.id ? null : d.id)}
                    className="min-h-[44px] rounded-xl border border-tinta/15 bg-crema px-4
                               text-sm font-medium hover:border-violeta/50">
              <Route size={15} className="mr-1.5 inline" />
              {foco === d.id ? "Apagar" : "Ver en el mapa"}
            </button>
          )}
          <button
            onClick={() => onPreguntar?.(
              `contame qué pasa con ${d.titulo.toLowerCase()} y qué puedo hacer`)}
            className="min-h-[44px] rounded-xl bg-violeta px-4 text-sm font-semibold text-crema">
            <Sparkles size={15} className="mr-1.5 inline" />
            Que me lo explique Ángela
          </button>
        </div>
      </div>
    </div>
  );
}

function TarjetaFamilia({ f, foco, setFoco }) {
  const [abierta, setAbierta] = useState(false);
  const g = GRAVEDAD[f.gravedad];
  return (
    <div className={`rounded-2xl border ${g.borde} bg-crema p-4`}>
      <div className="flex items-center gap-2">
        <span className={`h-2.5 w-2.5 shrink-0 rounded-full ${g.punto}`} />
        <span className="flex-1 font-semibold leading-tight">{f.titulo}</span>
        <span className="tabular-nums text-2xl font-bold">{f.cantidad}</span>
      </div>
      <p className="mt-1.5 text-[0.78rem] leading-snug text-tinta-suave">{f.que_significa}</p>
      <button onClick={() => setAbierta(!abierta)}
              className="mt-3 flex min-h-[40px] w-full items-center justify-between gap-2
                         rounded-lg bg-tinta/[0.03] px-3 text-left text-[0.8rem]">
        <span className="truncate">{f.destacado.titulo}</span>
        <ChevronDown size={14} className={`shrink-0 ${abierta ? "rotate-180" : ""}`} />
      </button>
      {abierta && (
        <ul className="mt-2 max-h-56 space-y-2 overflow-y-auto pr-1">
          {f.items.map((i) => (
            <li key={i.id}>
              <button
                onClick={() => setFoco(foco === i.id ? null : i.id)}
                className={`w-full rounded-lg px-3 py-2 text-left text-[0.78rem]
                            transition hover:bg-violeta/5
                            ${foco === i.id ? "bg-violeta/10" : ""}`}>
                <span className="font-medium">{i.titulo}</span>
                <span className="mt-0.5 block text-tinta-suave">{i.detalle}</span>
                {i.fuente?.fila_excel && (
                  <span className="mt-1 flex items-center gap-1 text-[0.7rem] text-hielo">
                    <FileSpreadsheet size={11} />
                    {i.fuente.solapa} · fila {i.fuente.fila_excel}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Leyenda() {
  return (
    <div className="pointer-events-none absolute left-3 top-3 z-10 rounded-xl border
                    border-tinta/10 bg-crema/95 px-3 py-2 text-[0.7rem] backdrop-blur">
      {["ida", "vuelta", "ingreso", "venta"].map((k) => (
        <span key={k} className="mr-3 inline-flex items-center gap-1.5">
          <span className="h-0.5 w-5 rounded" style={{ background: SENTIDO[k].color }} />
          {SENTIDO[k].label}
        </span>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// El panel. Se abre encima del lienzo y la cámara NO se mueve.
// ---------------------------------------------------------------------------
function PanelNodo({ detalle, onCerrar, onPreguntar, onLote }) {
  return (
    <aside className="absolute right-0 top-0 z-20 flex h-full w-full max-w-[27rem]
                      flex-col border-l border-tinta/12 bg-crema shadow-2xl">
      <div className="flex items-start justify-between gap-3 border-b border-tinta/8 p-4">
        <div>
          <h2 className="font-display text-xl font-bold leading-tight">
            {detalle?.titulo || "Abriendo…"}
          </h2>
          {detalle?.bascula && (
            <span className="mt-1.5 inline-flex items-center gap-1.5 rounded-full bg-tinta
                             px-2.5 py-1 text-[0.68rem] font-semibold text-crema">
              <Scale size={11} /> acá se pesa el camión
            </span>
          )}
          {detalle?.propia === false && (
            <p className="mt-1 text-[0.78rem] text-tinta-suave">
              subcontratado — se le paga por kilo movido
            </p>
          )}
        </div>
        <button onClick={onCerrar} aria-label="Cerrar"
                className="grid h-9 w-9 shrink-0 place-items-center rounded-lg
                           hover:bg-tinta/5"><X size={18} /></button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {detalle === null && <p className="text-tinta-suave">Buscando…</p>}
        {detalle === false && <p className="text-rojo">No se pudo abrir.</p>}
        {detalle && detalle.tipo === "campo" && <DetalleCampo d={detalle} onLote={onLote} />}
        {detalle && ["planta", "galpon", "frigorifico"].includes(detalle.tipo) &&
          <DetalleUbicacion d={detalle} onLote={onLote} />}
        {detalle && detalle.tipo === "lote" && <DetalleLote d={detalle} />}
        {detalle && detalle.tipo?.startsWith("cliente") && <DetalleCliente d={detalle} />}
      </div>

      {detalle && (
        <div className="border-t border-tinta/8 p-3">
          <button
            onClick={() => onPreguntar?.(`contame qué está pasando en ${detalle.titulo}`)}
            className="min-h-[48px] w-full rounded-xl bg-violeta text-sm font-semibold
                       text-crema">
            <Sparkles size={15} className="mr-1.5 inline" />
            Que Ángela me lo explique
          </button>
        </div>
      )}
    </aside>
  );
}

function DetalleCampo({ d, onLote }) {
  return (
    <div className="space-y-4">
      {d.nota && <p className="rounded-xl bg-oro/10 p-3 text-sm text-oro-tinta">{d.nota}</p>}
      {Object.entries(d.pivotes).map(([piv, lotes]) => (
        <div key={piv}>
          <p className="text-[0.72rem] font-semibold uppercase tracking-wider text-tinta-suave">
            {piv === "sin pivote declarado" ? piv : `Pivote ${piv}`} · {lotes.length} lotes
          </p>
        </div>
      ))}
      <div className="space-y-1.5">
        {d.lotes.map((l) => (
          <button key={l.lote} onClick={() => onLote(l.lote)}
                  className="flex w-full flex-wrap items-center justify-between gap-2
                             rounded-lg border border-tinta/8 px-3 py-2 text-left text-sm
                             hover:border-violeta/40">
            <span>
              <strong>lote {l.lote}</strong>
              <span className="text-tinta-suave">
                {" "}· {l.variedad}
                {l.pivote && ` · pivote ${l.pivote}`}
                {l.cuadrante && ` · cuadrante ${l.cuadrante}`}
              </span>
              {l.variedades_en_conflicto?.length > 1 && (
                <span className="mt-0.5 block text-[0.72rem] text-rojo">
                  la planilla le declara {l.variedades_en_conflicto.length} variedades:
                  {" "}{l.variedades_en_conflicto.join(", ")}
                </span>
              )}
            </span>
            <span className="tabular-nums text-tinta-suave">{nkg(l.kg_en_stock)}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function DetalleUbicacion({ d, onLote }) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3">
        <Dato label="Guardado" valor={nkg(d.kg)} />
        <Dato label="Libre" valor={nkg(Math.max(0, d.kg - d.comprometido))} />
      </div>
      {d.saldo_anterior_kg > 0 && (
        <p className="rounded-xl bg-oro/10 p-3 text-sm text-oro-tinta">
          {nkg(d.saldo_anterior_kg)} entraron antes de febrero 2026: la planilla no
          registra cuándo.
        </p>
      )}

      <Seccion titulo="Por variedad">
        {d.por_variedad.map((v) => (
          <Fila key={v.clave} izq={v.clave} der={nkg(v.kg)} />
        ))}
      </Seccion>

      <Seccion titulo={`La última jornada registrada · ${d.ultima_jornada.fecha || "—"}`}>
        {d.ultima_jornada.entro.length === 0 && d.ultima_jornada.salio.length === 0 && (
          <p className="text-sm text-tinta-suave">Sin movimientos ese día.</p>
        )}
        {d.ultima_jornada.entro.map((m) => (
          <Fila key={`e${m.movimiento}`} tono="salvia"
                izq={`entró · remito ${m.remito} · lote ${m.lote} · ${m.transporte || "—"}`}
                der={nkg(m.kg)} />
        ))}
        {d.ultima_jornada.salio.map((m) => (
          <Fila key={`s${m.movimiento}`} tono="hielo"
                izq={`salió → ${m.hacia} · remito ${m.remito} · lote ${m.lote}`}
                der={nkg(m.kg)} />
        ))}
      </Seccion>

      <Seccion titulo={`Qué tiene guardado · ${d.lotes.length} lotes`}>
        {d.lotes.map((l) => (
          <button key={l.lote} onClick={() => onLote(l.lote)}
                  className="flex w-full flex-wrap items-center justify-between gap-2
                             rounded-lg border border-tinta/8 px-3 py-2 text-left text-sm
                             hover:border-violeta/40">
            <span>
              <strong>lote {l.lote}</strong>
              <span className="text-tinta-suave"> · {l.variedad} · {l.calibres.join(", ")}</span>
              <span className="mt-0.5 block text-[0.72rem] text-tinta-suave">
                {l.dias_guardado != null && `hace ${l.dias_guardado} días · `}
                {l.colores.length > 0 && `${l.colores.join(" · ")} · `}
                {l.remitos.length > 0 && `remitos ${l.remitos.slice(0, 4).join(", ")}`}
              </span>
            </span>
            <span className="tabular-nums font-semibold">{nkg(l.kg)}</span>
          </button>
        ))}
      </Seccion>
    </div>
  );
}

function DetalleLote({ d }) {
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3">
        <Dato label="Variedad" valor={d.variedad || "—"} />
        <Dato label="En stock" valor={nkg(d.en_stock_kg)} />
        <Dato label="Pesado en báscula" valor={nkg(d.pesado_en_bascula_kg)} />
        <Dato label="Vendido" valor={nkg(d.vendido_kg)} />
      </div>
      {d.variedades_en_conflicto?.length > 1 && (
        <p className="rounded-xl bg-rojo/8 p-3 text-sm text-rojo">
          Un lote tiene UNA variedad. Este declara {d.variedades_en_conflicto.length}:
          {" "}{d.variedades_en_conflicto.join(", ")}.
        </p>
      )}
      {d.campo && (
        <p className="text-sm text-tinta-suave">
          Campo {d.campo.replace(/_/g, " ")}
          {d.pivote && ` · pivote ${d.pivote}`}
          {d.evidencia_campo && <> — <em>{d.evidencia_campo}</em></>}
        </p>
      )}

      <Seccion titulo="Dónde está hoy">
        {d.donde_esta.map((u) => <Fila key={u.ubicacion} izq={u.ubicacion} der={nkg(u.kg)} />)}
        {d.donde_esta.length === 0 && <p className="text-sm text-tinta-suave">Nada en cámara.</p>}
      </Seccion>

      <Seccion titulo={`El recorrido · ${d.etapas.length} movimientos`}>
        {d.etapas.map((e) => (
          <div key={e.movimiento} className="rounded-lg border border-tinta/8 px-3 py-2 text-sm">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="font-medium">
                {e.desde} <ArrowRight size={12} className="inline" /> {e.hacia}
              </span>
              <span className="tabular-nums font-semibold">{nkg(e.kg)}</span>
            </div>
            <p className="mt-0.5 text-[0.74rem] text-tinta-suave">
              {e.fecha} · remito {e.remito} · {e.transporte || "—"}
              {e.chofer && ` (${e.chofer})`}
              {e.dtv && ` · DTV ${e.dtv}`}
              {e.bolsas && ` · ${nnum(e.bolsas)} bolsas`}
              {(e.bolsa_color || e.hilo_color) &&
                ` · bolsa ${e.bolsa_color || "?"} / hilo ${e.hilo_color || "?"}`}
            </p>
            {e.anomalias?.length > 0 && (
              <p className="mt-1 text-[0.72rem] text-rojo">{e.anomalias.join(" · ")}</p>
            )}
            {e.fuente && (
              <p className="mt-1 text-[0.7rem] text-hielo">
                {e.fuente.solapa} · fila {e.fuente.fila_excel}
              </p>
            )}
          </div>
        ))}
      </Seccion>
    </div>
  );
}

function DetalleCliente({ d }) {
  if (d.tipo === "cliente_grupo") {
    return (
      <Seccion titulo={`${d.clientes.length} clientes`}>
        {d.clientes.map((c) => <Fila key={c.id} izq={c.nombre} der={nkg(c.kg)} />)}
      </Seccion>
    );
  }
  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3">
        <Dato label="Entregado" valor={nkg(d.kg)} />
        <Dato label="Camiones" valor={nnum(d.camiones)} />
      </div>
      <Seccion titulo="Por variedad">
        {d.por_variedad.map((v) => <Fila key={v.clave} izq={v.clave} der={nkg(v.kg)} />)}
      </Seccion>
      {/* El camión arriba, los lotes que llevó abajo. Nunca al revés. */}
      <Seccion titulo="Camión por camión">
        {d.camion_por_camion.map((r) => (
          <div key={r.remito_id} className="rounded-lg border border-tinta/8 px-3 py-2 text-sm">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="font-medium">Remito {r.remito}</span>
              <span className="tabular-nums font-semibold">{nkg(r.kg)}</span>
            </div>
            <p className="text-[0.74rem] text-tinta-suave">
              {r.fecha} · {r.transporte}{r.chofer && ` (${r.chofer})`}
              {r.dtvs.length > 0 && ` · DTV ${r.dtvs.join(", ")}`}
            </p>
            <ul className="mt-1 text-[0.74rem] text-tinta-suave">
              {r.lineas.map((l, i) => (
                <li key={i} className="flex justify-between gap-2">
                  <span>lote {l.lote} · {l.variedad} · {l.calibre}</span>
                  <span className="tabular-nums">{nkg(l.kg)}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </Seccion>
    </div>
  );
}

// --- piezas chicas ---------------------------------------------------------
function Dato({ label, valor }) {
  return (
    <div className="rounded-xl bg-tinta/[0.03] px-3 py-2">
      <p className="text-[0.72rem] text-tinta-suave">{label}</p>
      <p className="tabular-nums text-lg font-semibold leading-tight">{valor}</p>
    </div>
  );
}

function Seccion({ titulo, children }) {
  return (
    <section>
      <h3 className="mb-2 text-[0.72rem] font-semibold uppercase tracking-wider text-tinta-suave">
        {titulo}
      </h3>
      <div className="space-y-1.5">{children}</div>
    </section>
  );
}

function Fila({ izq, der, tono }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-tinta/5
                    pb-1.5 text-sm last:border-0">
      <span className={tono === "salvia" ? "text-salvia" : tono === "hielo" ? "text-hielo" : ""}>
        {izq}
      </span>
      <span className="shrink-0 tabular-nums font-semibold">{der}</span>
    </div>
  );
}

function Esqueleto() {
  return (
    <div className="space-y-4">
      <div className="h-9 w-72 animate-pulse rounded-lg bg-tinta/8" />
      <div className="grid gap-3 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-28 animate-pulse rounded-2xl bg-tinta/6" />
        ))}
      </div>
      <div className="h-[620px] animate-pulse rounded-2xl bg-tinta/6" />
    </div>
  );
}
