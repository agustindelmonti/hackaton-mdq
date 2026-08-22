import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { forceCollide, forceX, forceY } from "d3-force-3d";
import { Search, X, ArrowRight, Route } from "lucide-react";
import { api } from "../lib/api";
import { num, peso } from "../lib/format";
import { useT } from "../lib/i18n";

// ============================================================================
// EL CEREBRO — todo lo que el sistema sabe, y cómo se cruza.
// ----------------------------------------------------------------------------
// El MAPA responde una pregunta cerrada con tres capas fijas: de dónde viene,
// dónde está y adónde va cada kilo. Es la vista para decidir, y la posición de
// cada caja significa algo.
//
// El CEREBRO es lo de abajo: las 183 entidades individuales y las 753
// relaciones que las unen. Acá la posición NO significa nada — la calcula el
// layout de fuerzas — y eso está bien, porque esta vista no es para decidir: es
// para explorar y para contestar «¿qué más toca esto?». Los nodos muy
// conectados migran solos al centro y ese núcleo denso ES el negocio.
//
// NADA ACÁ ES INFERIDO. Cada línea es un campo declarado del lote (variedad,
// categoría, campaña, campo de origen, ubicación) o un renglón de una orden de
// carga. La trazabilidad de semilla fiscalizada obliga a declararlos todos.
//
// GOTCHAS que costaron caro y no hay que volver a pisar:
//  · El lienzo necesita PÍXELES, no %. Se mide con un callback ref, no con
//    useRef+useEffect: mientras el grafo carga el div no está montado y un
//    efecto con deps [] observaría null para siempre.
//  · Hay un frame donde los nodos todavía no tienen x/y. Dibujar con NaN tira
//    una excepción que se lleva puesto el componente entero: ese frame se
//    saltea.
// ============================================================================

const FONDO = "#14181f";
const BLANCO = "rgba(255,255,255,0.9)";

const FORMA = {
  ubicacion: "cuadrado", orden: "rombo", cliente: "triangulo",
  pais: "hexagono", lote: "circulo", variedad: "circulo",
  categoria: "circulo", campo: "circulo", campania: "circulo",
};

const normalizar = (s) => (s || "").normalize("NFD").replace(/\p{M}/gu, "").toLowerCase();

function useMedida() {
  const [caja, setCaja] = useState({ w: 0, h: 0 });
  const obs = useRef(null);
  const ref = useCallback((nodo) => {
    obs.current?.disconnect();
    if (!nodo || typeof ResizeObserver === "undefined") return;
    const medir = () => setCaja({ w: Math.round(nodo.clientWidth), h: Math.round(nodo.clientHeight) });
    medir();
    obs.current = new ResizeObserver(medir);
    obs.current.observe(nodo);
  }, []);
  useEffect(() => () => obs.current?.disconnect(), []);
  return { ref, ...caja };
}

function dibujarForma(ctx, tipo, x, y, r) {
  ctx.beginPath();
  switch (FORMA[tipo]) {
    case "cuadrado": ctx.rect(x - r, y - r, r * 2, r * 2); break;
    case "rombo":
      ctx.moveTo(x, y - r); ctx.lineTo(x + r, y);
      ctx.lineTo(x, y + r); ctx.lineTo(x - r, y); ctx.closePath(); break;
    case "triangulo":
      ctx.moveTo(x, y - r); ctx.lineTo(x + r, y + r * 0.8);
      ctx.lineTo(x - r, y + r * 0.8); ctx.closePath(); break;
    case "hexagono":
      for (let i = 0; i < 6; i++) {
        const a = (Math.PI / 3) * i - Math.PI / 6;
        const px = x + r * Math.cos(a), py = y + r * Math.sin(a);
        i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
      }
      ctx.closePath(); break;
    default: ctx.arc(x, y, r, 0, 2 * Math.PI);
  }
}

export default function CerebroSemilla({ onPreguntar }) {
  const t = useT();
  const { ref, w, h } = useMedida();
  const grafoRef = useRef(null);
  const [d, setD] = useState(null);
  const [foco, setFoco] = useState(null);
  const [q, setQ] = useState("");
  const [tipoOculto, setTipoOculto] = useState({});

  useEffect(() => { api.cerebro().then(setD).catch(() => setD(false)); }, []);

  const color = useMemo(
    () => Object.fromEntries((d?.tipos || []).map((x) => [x.id, x.color])), [d]);

  // El grafo que consume la librería. Se arma UNA vez por payload: react-force
  // muta los objetos (les mete x/y), así que rearmarlo en cada render reinicia
  // la simulación y el grafo tiembla sin parar.
  const gd = useMemo(() => {
    if (!d || !d.nodos) return { nodes: [], links: [] };
    const maxKg = Math.max(1, ...d.nodos.map((n) => n.kg || 0));
    const nodes = d.nodos.map((n) => ({
      ...n,
      // el radio es la RAÍZ de los kilos: con escala lineal un lote de 40 t
      // tapaba media pantalla y los chicos no se veían
      _r: 2.4 + 13 * Math.sqrt((n.kg || 0) / maxKg),
    }));
    const ids = new Set(nodes.map((n) => n.id));
    const links = d.aristas
      .filter((a) => ids.has(a.origen) && ids.has(a.destino))
      .map((a) => ({ ...a, source: a.origen, target: a.destino }));
    return { nodes, links };
  }, [d]);

  // vecinos del foco: para atenuar todo lo demás
  const vecinos = useMemo(() => {
    if (!foco) return null;
    const s = new Set([foco]);
    for (const l of gd.links) {
      const a = l.source.id || l.source, b = l.target.id || l.target;
      if (a === foco) s.add(b);
      if (b === foco) s.add(a);
    }
    return s;
  }, [foco, gd]);

  const resultados = useMemo(() => {
    const qq = normalizar(q.trim());
    if (qq.length < 2) return [];
    return gd.nodes
      .filter((n) => normalizar(n.etiqueta).includes(qq))
      .sort((a, b) => (b.kg || 0) - (a.kg || 0))
      .slice(0, 8);
  }, [q, gd]);

  // Encuadrar también por reloj: onEngineStop no siempre llega (si alguien
  // arrastra un nodo la simulación se recalienta y nunca "para"), y con el
  // grafo sin encuadrar la pantalla abre con una manchita en el medio.
  useEffect(() => {
    if (!gd.nodes.length) return;
    const id = setTimeout(() => grafoRef.current?.zoomToFit(700, 45), 3800);
    return () => clearTimeout(id);
  }, [gd]);

  useEffect(() => {
    const fg = grafoRef.current;
    if (!fg || !gd.nodes.length) return;
    fg.d3Force("charge")?.strength(-46).distanceMax(280);
    // Cada lote se pega a SU cámara (arista corta) y se suelta un poco de su
    // variedad o su categoría (arista larga): así los cuatro racimos se separan
    // y se ve de un vistazo cuánto cuelga de cada frigorífico.
    fg.d3Force("link")?.distance((l) => (
      l.rel === "traslado" ? 130 : l.rel === "esta_en" ? 20 : 46));
    fg.d3Force("collide", forceCollide((n) => n._r + 1.4).iterations(2));
    fg.d3Force("x", forceX(0).strength(0.045));
    fg.d3Force("y", forceY(0).strength(0.055));
  }, [gd]);

  const irA = (id) => {
    setFoco(id);
    const n = gd.nodes.find((x) => x.id === id);
    if (n && Number.isFinite(n.x)) grafoRef.current?.centerAt(n.x, n.y, 600);
    grafoRef.current?.zoom(2.4, 600);
  };

  if (d === null) return <Esqueleto />;
  if (d === false) return <p className="text-tinta-suave">{t("cerebro.error")}</p>;

  const r = d.resumen || {};
  const nodoFoco = gd.nodes.find((n) => n.id === foco);

  return (
    <div className="space-y-3">
      <header>
        <h1 className="font-display text-3xl font-bold">{t("cerebro.titulo")}</h1>
        <p className="mt-1 text-[0.95rem] text-tinta-suave">
          {t("cerebro.frase", {
            nodos: num(r.nodos), aristas: num(r.aristas),
            lotes: num(r.por_tipo?.lote), variedades: num(r.por_tipo?.variedad),
            categorias: num(r.por_tipo?.categoria), campos: num(r.por_tipo?.campo),
            movimientos: num(r.movimientos),
          })}
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <div className="flex items-center gap-2 rounded-full border border-linea bg-superficie px-3 py-1.5">
            <Search size={14} className="text-tinta-suave" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder={t("cerebro.buscar_ph")}
              className="w-56 bg-transparent text-[0.85rem] outline-none"
            />
            {q && (
              <button onClick={() => setQ("")} className="text-tinta-suave"><X size={13} /></button>
            )}
          </div>
          {resultados.length > 0 && (
            <ul className="absolute z-30 mt-1 w-72 overflow-hidden rounded-xl border border-linea bg-superficie sombra-alta">
              {resultados.map((n) => (
                <li key={n.id}>
                  <button
                    onClick={() => { irA(n.id); setQ(""); }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-left text-[0.83rem] hover:bg-crema"
                  >
                    <span className="h-2.5 w-2.5 shrink-0 rounded-full"
                          style={{ background: color[n.tipo] }} />
                    <span className="truncate">{n.etiqueta}</span>
                    <span className="ml-auto shrink-0 text-[0.72rem] text-tinta-suave">
                      {t(`cerebro.tipo_${n.tipo}`)}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* la leyenda ES el filtro: tocar un tipo lo apaga */}
        {(d.tipos || []).filter((x) => x.n > 0).map((x) => (
          <button
            key={x.id}
            onClick={() => setTipoOculto((s) => ({ ...s, [x.id]: !s[x.id] }))}
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.76rem] transition
              ${tipoOculto[x.id] ? "border-linea text-tinta-suave/50" : "border-linea hover:bg-crema"}`}
          >
            <span className="h-2.5 w-2.5 rounded-full"
                  style={{ background: tipoOculto[x.id] ? "transparent" : x.color,
                           border: `1.5px solid ${x.color}` }} />
            {t(`cerebro.tipo_${x.id}_p`)} <span className="tabular-nums text-tinta-suave">{x.n}</span>
          </button>
        ))}
      </div>

      <div className="relative h-[34rem] overflow-hidden rounded-[var(--radius-card)] border border-linea"
           style={{ background: FONDO }} ref={ref}>
        {w > 0 && (
          <ForceGraph2D
            ref={grafoRef}
            width={w} height={h}
            graphData={gd}
            backgroundColor={FONDO}
            cooldownTicks={320}
            // Cuando la simulación se aquieta, el grafo se encuadra solo. Sin
            // esto queda una manchita en el medio de un lienzo vacío y hay que
            // pedirle al jurado que haga zoom con la rueda.
            onEngineStop={() => grafoRef.current?.zoomToFit(700, 45)}
            minZoom={0.15} maxZoom={9}
            onNodeClick={(n) => setFoco(n.id === foco ? null : n.id)}
            onBackgroundClick={() => setFoco(null)}
            nodeLabel={(n) => `${n.etiqueta} · ${t(`cerebro.tipo_${n.tipo}`)}`}
            linkColor={(l) => {
              if (!vecinos) return l.rel === "traslado"
                ? "rgba(143,182,191,0.45)" : "rgba(255,255,255,0.07)";
              const a = l.source.id || l.source, b = l.target.id || l.target;
              return (a === foco || b === foco)
                ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.025)";
            }}
            linkWidth={(l) => {
              const a = l.source.id || l.source, b = l.target.id || l.target;
              if (foco && (a === foco || b === foco)) return 1.8;
              return l.rel === "traslado" ? 1.4 : 0.5;
            }}
            nodePointerAreaPaint={(n, c, ctx) => {
              if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) return;
              ctx.fillStyle = c;
              ctx.beginPath(); ctx.arc(n.x, n.y, n._r + 3.5, 0, 2 * Math.PI); ctx.fill();
            }}
            nodeCanvasObject={(n, ctx, escala) => {
              // el frame en que los nodos todavía no tienen posición: dibujar
              // con NaN lanza y se lleva puesto el componente
              if (!Number.isFinite(n.x) || !Number.isFinite(n.y)) return;
              if (tipoOculto[n.tipo]) return;
              const dentro = !vecinos || vecinos.has(n.id);
              ctx.save();
              if (!dentro) ctx.globalAlpha = 0.1;

              if (n.id === foco) {
                const g = ctx.createRadialGradient(n.x, n.y, n._r, n.x, n.y, n._r + 12);
                g.addColorStop(0, "#ffffff55");
                g.addColorStop(1, "#ffffff00");
                ctx.beginPath(); ctx.arc(n.x, n.y, n._r + 12, 0, 2 * Math.PI);
                ctx.fillStyle = g; ctx.fill();
              }

              dibujarForma(ctx, n.tipo, n.x, n.y, n._r);
              ctx.fillStyle = color[n.tipo] || "#8b8fa8";
              ctx.fill();
              ctx.lineWidth = Math.max(0.35, n._r * 0.12);
              ctx.strokeStyle = "rgba(0,0,0,0.55)";
              ctx.stroke();

              // el anillo es señal, no decoración: rojo = problema hoy
              if (n.estado === "rojo" || n.estado === "amarillo") {
                ctx.beginPath(); ctx.arc(n.x, n.y, n._r + 2.3, 0, 2 * Math.PI);
                ctx.strokeStyle = n.estado === "rojo" ? "#e2564a" : "#e0a13a";
                ctx.lineWidth = n.estado === "rojo" ? 1.3 : 0.95;
                ctx.stroke();
              }

              // el nombre sólo con zoom o en el foco: si no, es una mancha
              if (escala > 2.2 || n.id === foco || n._r > 6) {
                ctx.font = `${Math.max(2.6, 3.4)}px Hanken Grotesk, sans-serif`;
                ctx.textAlign = "center";
                ctx.fillStyle = BLANCO;
                ctx.fillText(n.etiqueta, n.x, n.y + n._r + 4.2);
              }
              ctx.restore();
            }}
          />
        )}

        {nodoFoco && (
          <aside className="absolute right-3 top-3 z-20 max-h-[calc(100%-1.5rem)] w-[19rem] space-y-2.5 overflow-y-auto rounded-[var(--radius-card)] border border-linea bg-superficie p-4 sombra-alta">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="flex items-center gap-1.5 text-[0.68rem] uppercase tracking-wide text-tinta-suave">
                  <span className="h-2 w-2 rounded-full" style={{ background: color[nodoFoco.tipo] }} />
                  {t(`cerebro.tipo_${nodoFoco.tipo}`)}
                </p>
                <h2 className="font-display text-[1.02rem] font-bold leading-tight">{nodoFoco.etiqueta}</h2>
                {nodoFoco.detalle && (
                  <p className="mt-0.5 text-[0.8rem] leading-snug text-tinta-suave">{nodoFoco.detalle}</p>
                )}
              </div>
              <button onClick={() => setFoco(null)} className="shrink-0 rounded p-1 text-tinta-suave hover:bg-crema">
                <X size={15} />
              </button>
            </div>

            {nodoFoco.kg > 0 && (
              <p className="plata text-[1.1rem] font-medium">{num(nodoFoco.kg)} kg</p>
            )}

            {nodoFoco.metricas && (
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-[0.8rem]">
                {Object.entries(nodoFoco.metricas)
                  .filter(([, v]) => v != null)
                  .map(([k, v]) => (
                    <div key={k}>
                      <dt className="text-[0.66rem] text-tinta-suave">{t(`cerebro.m_${k}`)}</dt>
                      <dd className="tabular-nums font-medium">
                        {k === "valor" ? peso(v)
                          // "Días hasta brotar: -270" no lo dice nadie: si el
                          // número es negativo el lote YA brotó, y eso es lo que
                          // hay que leer.
                          : k === "dias_hasta_brotacion" && v < 0
                            ? t("cerebro.ya_broto", { n: num(-v) })
                          : typeof v === "number" ? num(v) : String(v)}
                      </dd>
                    </div>
                  ))}
              </dl>
            )}

            <p className="text-[0.78rem] text-tinta-suave">
              {t("cerebro.conecta_con", { n: (vecinos?.size || 1) - 1 })}
            </p>

            <button
              type="button"
              onClick={() => onPreguntar?.(t("cerebro.pregunta", { que: nodoFoco.etiqueta }))}
              className="flex w-full items-center justify-center gap-1.5 rounded-lg border border-linea px-3 py-2 text-[0.83rem] transition hover:bg-crema"
            >
              {t("cerebro.preguntar")} <ArrowRight size={13} />
            </button>
          </aside>
        )}
      </div>

      <p className="flex items-start gap-1.5 text-[0.78rem] leading-snug text-tinta-suave">
        <Route size={13} className="mt-0.5 shrink-0" />
        {d.meta?.fuente}
      </p>
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
