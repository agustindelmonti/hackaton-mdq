import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ReactFlow, Background, Controls, useNodesState, useEdgesState,
  Handle, Position, MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Snowflake, Warehouse, FlaskConical, Sprout, Ship, Users, Package,
  Globe, Anchor, Lock, ArrowRight, X, Route, Eye, EyeOff, Factory,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import { api } from "../lib/api";
import { num, peso, pesoCorto, fecha } from "../lib/format";
import { useT } from "../lib/i18n";

// ============================================================================
// EL MAPA DE LA OPERACIÓN — Papasud en el medio de sus cuatro ubicaciones.
// ----------------------------------------------------------------------------
// El orden es el del negocio y va de izquierda a derecha:
//
//     DE DÓNDE VIENE   →   PLANTA   →      DÓNDE ESTÁ      →      ADÓNDE VA
//   laboratorio in vitro    MdP        ┌────┬────┐          órdenes de carga
//   los cinco campos                   │ TL │ TR │          clientes
//                                      ├──[PAPASUD]──┤      puerto · país
//                                      │ BL │ BR │
//                                      └────┴────┘
//
// La planta va ENTRE el campo y el cuadro: el kilo no salta a la cámara.
//
// POR QUÉ LAS CUATRO UBICACIONES EN CUADRO Y NO EN COLUMNA. Porque los
// traslados son ENTRE ellas: en una columna, doce flechas de ida y vuelta se
// cruzan y no se lee ninguna. En cuadro, cada par de cámaras comparte un
// corredor propio y la flecha punteada de los kilos sin confirmar se ve desde
// la otra punta de la sala. Y el medio del cuadro es el único lugar donde el
// logo de la empresa no es decoración: es la respuesta a "¿de quién es todo
// esto?".
//
// GOTCHA de React Flow v12: los nodos TIENEN que pasar por useNodesState —
// pasarlos como prop plana los deja invisibles.
// ============================================================================

// --- la grilla del centro ---------------------------------------------------
const W = { origen: 202, planta: 228, centro: 292, orden: 188, cliente: 208 };
// El hueco entre las dos columnas del cuadro no es estético: es el corredor por
// donde pasan los traslados. Con 46 px las flechas eran un garabato; con 200 el
// logo entra en el medio y las flechas se leen.
const COL = {
  origen: 0, planta: 230, gridL: 490, gridR: 982, orden: 1350, cliente: 1596,
};
const GRID_Y = [0, 232];                       // fila de arriba / fila de abajo
const CENTRO_MEDIO = { x: (COL.gridL + COL.gridR + W.centro) / 2, y: GRID_Y[1] / 2 + 78 };
const EJE_Y = CENTRO_MEDIO.y;                  // todas las columnas se centran acá

const ICONO = {
  laboratorio: FlaskConical, campo: Sprout, ubicacion: Snowflake,
  planta: Factory, frigorifico: Snowflake,
  orden: Ship, cliente: Users, puerto: Anchor, pais: Globe, galpon: Warehouse,
};

const TONO = {
  verde: { borde: "#2f7d5b", fondo: "#f2f8f5" },
  amarillo: { borde: "#de7c1a", fondo: "#fdf7ef" },
  rojo: { borde: "#d2372b", fondo: "#fdf3f2" },
  neutro: { borde: "#ddd9d2", fondo: "#ffffff" },
};

// Los cuatro lados, para que un traslado entre cámaras salga por donde
// corresponde y no dibuje un rulo.
const LADOS = [
  ["t", Position.Top], ["r", Position.Right],
  ["b", Position.Bottom], ["l", Position.Left],
];

function Handles({ centro, columna }) {
  if (centro) {
    return LADOS.map(([id, pos]) => (
      <span key={id}>
        <Handle type="target" position={pos} id={`t-${id}`} style={{ opacity: 0 }} />
        <Handle type="source" position={pos} id={`s-${id}`} style={{ opacity: 0 }} />
      </span>
    ));
  }
  if (columna) {
    return (
      <>
        <Handle type="target" position={Position.Left} id="t-l" style={{ opacity: 0 }} />
        <Handle type="source" position={Position.Right} id="s-r" style={{ opacity: 0 }} />
        <Handle type="source" position={Position.Bottom} id="s-b" style={{ opacity: 0 }} />
        <Handle type="target" position={Position.Top} id="t-t" style={{ opacity: 0 }} />
      </>
    );
  }
  return (
    <>
      <Handle type="target" position={Position.Left} id="t-l" style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Right} id="s-r" style={{ opacity: 0 }} />
    </>
  );
}

// --- el nodo de la empresa --------------------------------------------------
function NodoMarca({ data }) {
  return (
    <div
      className="pointer-events-none flex flex-col items-center justify-center rounded-2xl border-2 border-tinta/15 bg-superficie px-4 py-3 text-center"
      style={{ width: 190, background: "#fff", boxShadow: "0 8px 28px rgba(33,32,29,.16)" }}
    >
      {data.logo ? (
        <img src={data.logo} alt={data.etiqueta} className="h-12 w-auto" draggable="false" />
      ) : (
        <p className="font-display text-[1rem] font-bold leading-tight">{data.etiqueta}</p>
      )}
      <p className="mt-1.5 plata text-[0.86rem] font-medium leading-none">
        {num(data.metricas?.toneladas)} t
      </p>
      <p className="mt-0.5 text-[0.62rem] leading-tight text-tinta-suave">{data.subtitulo}</p>
    </div>
  );
}

// --- el nodo -----------------------------------------------------------------
function NodoOperacion({ data }) {
  const esPlanta = data.tipo === "planta";
  const esGalpon = data.tipo === "galpon" || data.tipo_sitio === "galpon";
  const Icono = esPlanta ? Factory
    : (esGalpon ? Warehouse : (ICONO[data.tipo] || Package));
  const t = esPlanta ? TONO.verde : (TONO[data.estado] || TONO.neutro);
  const esCuadro = data.tipo === "ubicacion";
  const esGrande = esCuadro || esPlanta;
  const apagado = data.atenuado;

  return (
    <div
      className="rounded-xl border-2 transition-opacity"
      style={{
        borderColor: data.resaltado ? "#2b7a8c" : (esPlanta ? "#2f7d5b" : t.borde),
        background: esPlanta ? "#f2f8f5" : t.fondo,
        width: esCuadro ? W.centro : data.ancho,
        padding: esCuadro ? "12px 14px" : "9px 11px",
        opacity: apagado ? 0.16 : 1,
        boxShadow: data.resaltado
          ? "0 0 0 3px rgba(43,122,140,.2)"
          : esPlanta ? "0 6px 22px rgba(47,125,91,.22)"
          : esCuadro ? "0 2px 12px rgba(33,32,29,.08)" : "0 1px 3px rgba(33,32,29,.05)",
      }}
    >
      <Handles centro={esCuadro} columna={esPlanta || data.tipo === "galpon"} />
      <div className="flex items-start gap-2">
        <Icono size={esGrande ? 19 : 15} className="mt-0.5 shrink-0 text-tinta-suave" />
        <div className="min-w-0 flex-1">
          <p className={`truncate font-display font-bold leading-tight ${esGrande ? "text-[1.02rem]" : "text-[0.95rem]"}`}>
            {data.etiqueta}
          </p>
          {data.subtitulo && (
            <p className="truncate text-[0.78rem] text-tinta-suave">{data.subtitulo}</p>
          )}
        </div>
        {data.bloqueada && <Lock size={14} className="mt-0.5 shrink-0 text-rojo" />}
      </div>

      {esGrande && data.metricas && (
        <>
          <div className="mt-2.5 flex items-baseline gap-2">
            <span className="plata text-[1.35rem] font-medium leading-none">
              {num(data.metricas.toneladas)} t
            </span>
            <span className="text-[0.74rem] text-tinta-suave">
              {data.metricas.lotes} lotes
            </span>
          </div>
          {data.tipo !== "planta" && data.tipo !== "galpon" && data.metricas.ocupacion_pct != null && (
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-linea">
            <div className="h-full rounded-full"
                 style={{ width: `${Math.min(100, data.metricas.ocupacion_pct || 0)}%`,
                          background: data.metricas.ocupacion_pct > 90 ? "#de7c1a" : "#2b7a8c" }} />
          </div>
          )}
          {esPlanta && (data.zonas || []).length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {data.zonas.map((z) => (
                <span key={z.id} className="rounded bg-salvia/10 px-1.5 py-0.5 text-[0.66rem] font-medium text-salvia">
                  {z.nombre}
                </span>
              ))}
            </div>
          )}
          <div className="mt-2 flex flex-wrap gap-1 text-[0.68rem]">
            {data.metricas.diferencias > 0 && (
              <span className="rounded bg-rojo/10 px-1.5 py-0.5 font-medium text-rojo">
                {data.metricas.diferencias} dif.
              </span>
            )}
            {data.metricas.por_brotar > 0 && (
              <span className="rounded bg-oro/10 px-1.5 py-0.5 text-oro">
                {data.metricas.por_brotar} por brotar
              </span>
            )}
            {data.metricas.ya_brotados > 0 && (
              <span className="rounded bg-linea px-1.5 py-0.5 text-tinta-suave">
                {data.metricas.ya_brotados} brotados
              </span>
            )}
          </div>
        </>
      )}

      {!esGrande && data.metricas && (
        <p className="mt-1 text-[0.76rem] tabular-nums text-tinta-suave">
          {data.metricas.toneladas != null && `${num(data.metricas.toneladas)} t`}
          {data.metricas.kg != null && `${num(data.metricas.kg)} kg`}
          {data.metricas.lotes != null && ` · ${data.metricas.lotes} lotes`}
          {data.metricas.ordenes != null && ` · ${data.metricas.ordenes} órd.`}
        </p>
      )}
    </div>
  );
}

const TIPOS_NODO = { operacion: NodoOperacion, marca: NodoMarca };

// Qué lado usa cada corredor del cuadro. Índices: 0=arriba-izq, 1=arriba-der,
// 2=abajo-izq, 3=abajo-der.
function ladosDelCorredor(a, b) {
  const filaA = a > 1, filaB = b > 1;
  const colA = a % 2, colB = b % 2;
  if (filaA === filaB) return colA < colB ? ["s-r", "t-l"] : ["s-l", "t-r"];
  if (colA === colB) return filaA < filaB ? ["s-b", "t-t"] : ["s-t", "t-b"];
  // LAS DIAGONALES NO CRUZAN POR EL MEDIO. Ahí está el logo, y una línea que
  // le pasa por encima al nombre de la empresa se lee como un error de dibujo.
  // Una rodea por arriba y la otra por abajo: quedan las dos separadas y el
  // centro limpio.
  const arriba = Math.min(a, b) === 0;
  return arriba ? ["s-t", "t-t", "smoothstep"] : ["s-b", "t-b", "smoothstep"];
}

export default function MapaOperacion({ onPreguntar }) {
  const t = useT();
  const [d, setD] = useState(null);
  const [foco, setFoco] = useState(null);         // el hallazgo iluminado
  const [detalle, setDetalle] = useState(null);   // el panel flotante
  const [genealogia, setGenealogia] = useState(null);
  const [todosLosIngresos, setTodosLosIngresos] = useState(false);

  useEffect(() => { api.mapa().then(setD).catch(() => setD(false)); }, []);

  // --- posiciones ----------------------------------------------------------
  const { nodosBase, aristasBase } = useMemo(() => {
    if (!d || !d.nodos) return { nodosBase: [], aristasBase: [] };

    const marca = d.nodos.find((n) => n.tipo === "marca");
    const planta = d.nodos.find((n) => n.tipo === "planta");
    const galpones = d.nodos.filter((n) => n.tipo === "galpon");
    const ubis = d.nodos.filter((n) => n.capa === "centro" && n.tipo === "ubicacion");
    const origen = d.nodos.filter((n) => n.capa === "origen");
    const ordenes = d.nodos.filter((n) => n.tipo === "orden");
    const salida = d.nodos.filter(
      (n) => n.capa === "destino" && n.tipo !== "orden");

    const nodos = [];
    const columna = (lista, x, ancho, alto) => {
      const y0 = EJE_Y - (lista.length * alto) / 2;
      lista.forEach((n, i) => nodos.push({
        id: n.id, type: "operacion", draggable: false,
        position: { x, y: y0 + i * alto },
        data: { ...n, ancho },
      }));
    };

    const idx = new Map(ubis.map((u, i) => [u.id, i]));

    columna(origen, COL.origen, W.origen, 84);
    if (planta) {
      nodos.push({
        id: planta.id, type: "operacion", draggable: false,
        position: { x: COL.planta, y: EJE_Y - 78 },
        data: { ...planta, ancho: W.planta },
      });
    }
    galpones.forEach((g, i) => nodos.push({
      id: g.id, type: "operacion", draggable: false,
      position: { x: COL.planta, y: EJE_Y + 96 + i * 100 },
      data: { ...g, ancho: W.planta },
    }));
    ubis.forEach((u, i) => nodos.push({
      id: u.id, type: "operacion", draggable: false,
      position: { x: i % 2 ? COL.gridR : COL.gridL, y: GRID_Y[i > 1 ? 1 : 0] },
      data: { ...u },
    }));
    // El hueco del cuadro es del logo, como en el mapa de siempre.
    if (marca) {
      nodos.push({
        id: marca.id, type: "marca", draggable: false, selectable: false,
        position: { x: CENTRO_MEDIO.x - 95, y: CENTRO_MEDIO.y - 52 },
        data: { ...marca },
        zIndex: 1200,
      });
    }
    columna(ordenes, COL.orden, W.orden, 90);
    columna(salida, COL.cliente, W.cliente, 84);

    // --- las aristas -------------------------------------------------------
    // Los traslados van de a PARES: Sierra→Batán y Batán→Sierra son el mismo
    // corredor. Doce flechas cruzadas se vuelven seis corredores legibles, y
    // el que tiene kilos sin confirmar se dibuja punteado y en rojo.
    const corredores = new Map();
    const otras = [];
    for (const a of d.aristas) {
      if (a.tipo !== "movimiento") { otras.push(a); continue; }
      const clave = [a.origen, a.destino].sort().join("|");
      const c = corredores.get(clave) || {
        ids: [], kg: 0, en_transito: 0, kg_en_transito: 0,
        origen: a.origen, destino: a.destino, numeros: [],
      };
      c.ids.push(a.id);
      c.kg += a.kg || 0;
      c.numeros.push(...(a.numeros_en_transito || []));
      if (a.en_transito) {
        // la dirección del corredor la manda el traslado sin confirmar: es lo
        // que hay que mirar
        c.en_transito += a.en_transito;
        c.kg_en_transito += a.kg_en_transito || 0;
        c.origen = a.origen; c.destino = a.destino;
      }
      corredores.set(clave, c);
    }

    const aristas = [];
    for (const c of corredores.values()) {
      const i = idx.get(c.origen), j = idx.get(c.destino);
      const [sh, th, forma] = (i != null && j != null) ? ladosDelCorredor(i, j) : ["s-r", "t-l"];
      const alerta = c.en_transito > 0;
      aristas.push({
        id: c.ids.join("+"),
        source: c.origen, target: c.destino,
        sourceHandle: sh, targetHandle: th,
        type: forma || "straight",
        animated: alerta,
        style: {
          stroke: alerta ? "#d2372b" : "#8fb6bf",
          strokeWidth: alerta ? 3 : Math.max(1.6, Math.min(5, c.kg / 40000)),
          strokeDasharray: alerta ? "7 5" : undefined,
        },
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16,
                     color: alerta ? "#d2372b" : "#8fb6bf" },
        label: alerta
          ? t("mapa.e_sin_confirmar", { kg: num(c.kg_en_transito) })
          : `${num(Math.round(c.kg / 1000))} t`,
        labelStyle: { fontSize: alerta ? 11 : 10, fontWeight: alerta ? 600 : 400,
                      fill: alerta ? "#d2372b" : "#6f6a61" },
        labelBgStyle: { fill: "#fff", fillOpacity: 0.92 },
        labelBgPadding: [4, 2],
        labelBgBorderRadius: 4,
        zIndex: alerta ? 6 : 1,
        data: { ...c, ids: c.ids, tipo: "movimiento" },
      });
    }

    const idsGalpon = new Set(galpones.map((g) => g.id));
    const idPlanta = planta?.id;
    for (const a of otras) {
      const esIngreso = a.tipo === "ingreso";
      if (esIngreso && !todosLosIngresos && !a.principal) continue;
      let sh = "s-r", th = "t-l";
      if (a.tipo === "desde_planta" && idsGalpon.has(a.destino)) {
        sh = "s-b";
        th = "t-t";
      } else if (a.tipo === "desde_planta" && a.origen === idPlanta) {
        const j = idx.get(a.destino);
        sh = "s-r";
        th = (j != null && j % 2 === 1) ? "t-t" : "t-l";
      } else if (esIngreso && a.destino === idPlanta) {
        sh = "s-r";
        th = "t-l";
      }
      aristas.push({
        id: a.id, source: a.origen, target: a.destino,
        sourceHandle: sh,
        targetHandle: th,
        type: "bezier",
        style: {
          stroke: a.tipo === "desde_planta" ? "#2f7d5b" : (a.alerta ? "#d2372b" : "#d0ccc4"),
          strokeWidth: a.tipo === "desde_planta" ? 1.7 : (a.alerta ? 2 : 1.3),
          strokeDasharray: a.alerta ? "5 4" : undefined,
        },
        markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12,
                     color: a.tipo === "desde_planta" ? "#2f7d5b" : (a.alerta ? "#d2372b" : "#c4c0b8") },
        data: { ...a, ids: [a.id] },
      });
    }
    return { nodosBase: nodos, aristasBase: aristas };
  }, [d, todosLosIngresos, t]);

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
      data: {
        ...n.data,
        // la marca nunca se apaga: es el centro del dibujo
        atenuado: n.type !== "marca" && !enCamino.has(n.id),
        resaltado: enCamino.has(n.id),
      },
    })));
    setEdges(aristasBase.map((a) => {
      const enCam = (a.data?.ids || [a.id]).some((x) => aristasCamino.has(x));
      const puntas = enCamino.has(a.source) && enCamino.has(a.target);
      return {
        ...a,
        animated: enCam || a.animated,
        style: {
          ...a.style,
          opacity: enCam || puntas ? 1 : 0.08,
          strokeWidth: enCam ? 4 : a.style.strokeWidth,
        },
      };
    }));
  }, [nodosBase, aristasBase, setNodes, setEdges]);

  // --- al tocar un nodo: cambia el panel, NO mueve la cámara ---------------
  const alTocarNodo = useCallback(async (_e, node) => {
    if (node.type === "marca") return;
    setDetalle(node.data);
    setGenealogia(null);
    if (node.data.tipo === "ubicacion" && node.data.grupos?.length) {
      const cod = node.data.grupos[0]?.codigos?.[0];
      if (cod) {
        try { setGenealogia(await api.genealogia(String(cod))); } catch { /* el panel igual sirve */ }
      }
    }
  }, []);

  if (d === null) return <Esqueleto />;
  if (d === false) return <p className="text-tinta-suave">{t("mapa.error")}</p>;

  const r = d.resumen || {};

  return (
    <div className="space-y-3">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">{t("mapa.titulo")}</h1>
          <p className="mt-1 max-w-[42rem] text-[0.95rem] text-tinta-suave">
            {d.regla || t("mapa.subtitulo")}
          </p>
        </div>
        <div className="flex flex-wrap gap-5 text-right">
          <Kpi valor={`${num(r.toneladas)} t`} etiqueta={t("mapa.k_stock")} />
          <Kpi valor={pesoCorto(r.valor)} etiqueta={t("mapa.k_valor")} />
          <Kpi valor={num(r.diferencias)} etiqueta={t("mapa.k_dif")}
               tono={r.diferencias ? "alerta" : "ok"} />
          <Kpi valor={`${num(r.kg_en_transito)} kg`} etiqueta={t("mapa.k_transito")}
               tono={r.kg_en_transito ? "alerta" : "ok"} />
        </div>
      </header>

      {/* los hallazgos: cada uno ilumina SU camino en el lienzo */}
      <div className="flex flex-wrap items-center gap-1.5">
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

      {/* la leyenda vive ARRIBA del lienzo: adentro le tapaba nodos y el ojo
          la buscaba justo cuando el mapa estaba lleno */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[0.74rem] text-tinta-suave">
        <span className="flex items-center gap-1.5">
          <svg width="26" height="8"><line x1="0" y1="4" x2="26" y2="4" stroke="#d2372b" strokeWidth="2.5" strokeDasharray="6 4" /></svg>
          {t("mapa.leyenda_transito")}
        </span>
        <span className="flex items-center gap-1.5">
          <svg width="26" height="8"><line x1="0" y1="4" x2="26" y2="4" stroke="#8fb6bf" strokeWidth="3" /></svg>
          {t("mapa.leyenda_traslado")}
        </span>
        <button type="button" onClick={() => setTodosLosIngresos((v) => !v)}
                className="flex items-center gap-1 rounded border border-linea px-1.5 py-0.5 transition hover:bg-crema">
          {todosLosIngresos ? <EyeOff size={11} /> : <Eye size={11} />}
          {todosLosIngresos ? t("mapa.solo_principal") : t("mapa.ver_ingresos")}
        </button>
        <span className="ml-auto">{t("mapa.toca_algo")}</span>
      </div>

      {/* el lienzo, a todo el ancho: el mapa entra entero sin zoom */}
      <div className="relative h-[38rem] overflow-hidden rounded-[var(--radius-card)] border border-linea bg-crema/40">
        <div className={`pointer-events-none absolute inset-x-0 top-0 z-10 grid border-b border-linea bg-superficie/85 px-6 py-1.5 backdrop-blur ${(d.capas || []).length > 3 ? "grid-cols-4" : "grid-cols-3"}`}>
          {(d.capas || []).map((c, i) => (
            <span key={c.id}
                  className={`text-[0.7rem] font-semibold uppercase tracking-wide text-tinta-suave ${i === 1 ? "text-center" : i === 2 ? "text-right" : ""}`}>
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
          onPaneClick={() => setDetalle(null)}
          fitView
          fitViewOptions={{ padding: 0.04 }}
          minZoom={0.3}
          maxZoom={1.6}
          nodesDraggable={false}
          proOptions={{ hideAttribution: true }}
        >
          <Background gap={24} size={1} color="#e4e1db" />
          <Controls position="bottom-right" showInteractive={false} />
        </ReactFlow>

        {/* el panel: flotante, para no comerle ancho al mapa cuando no hace falta */}
        {detalle && (
          <Panel detalle={detalle} genealogia={genealogia} onPreguntar={onPreguntar}
                 onCerrar={() => setDetalle(null)} t={t} />
        )}
      </div>
    </div>
  );
}

// --- el panel lateral -------------------------------------------------------
function Panel({ detalle, genealogia, onPreguntar, onCerrar, t }) {
  return (
    <aside className="absolute right-3 top-11 z-20 max-h-[calc(100%-3.5rem)] w-[21rem] space-y-3 overflow-y-auto rounded-[var(--radius-card)] border border-linea bg-superficie p-4 sombra-alta">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[0.68rem] uppercase tracking-wide text-tinta-suave">
            {t(`mapa.tipo_${detalle.tipo}`)}
          </p>
          <h2 className="font-display text-[1.05rem] font-bold leading-tight">{detalle.etiqueta}</h2>
          {detalle.subtitulo && (
            <p className="mt-0.5 text-[0.8rem] text-tinta-suave">{detalle.subtitulo}</p>
          )}
        </div>
        <button type="button" onClick={onCerrar} aria-label={t("mapa.cerrar")}
                className="shrink-0 rounded-lg p-1 text-tinta-suave transition hover:bg-crema">
          <X size={16} />
        </button>
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
      <div className="h-[38rem] animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
    </div>
  );
}
