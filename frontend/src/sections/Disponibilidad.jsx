import { useEffect, useRef, useState } from "react";
import {
  Search, Mic, MicOff, Check, X, TriangleAlert, Snowflake, Warehouse,
  Factory, ChevronDown, FileSpreadsheet, Truck, Sparkles, Loader2,
} from "lucide-react";
import { api } from "../lib/api";

// ============================================================================
// «¿TENGO O NO TENGO?» — la pantalla que abre la demo.
// ----------------------------------------------------------------------------
// Sale de una frase textual del dueño:
//
//   «Estoy yendo a un campo y me dicen: che, necesito 1.200 bolsas de Spunta,
//    ¿tenés? Y digo: pará, tengo que anotarlo en el bloc de notas. […] Es tener
//    algo que diga: hay tanta vendida, hay tantas guardadas, tengo o no tengo.»
//
// De ahí salen las tres decisiones de esta pantalla:
//
//   1. LA RESPUESTA CORTA VA PRIMERO Y GRANDE. El dueño está manejando. Una
//      tabla no se lee al volante; una línea sí. El detalle está abajo, para el
//      que lo quiera.
//   2. TENER NO ES PODER VENDER. Lo comprometido y lo libre nunca comparten un
//      número. Es la resta que la planilla no hace y por la que se cae una venta.
//   3. TODO NÚMERO SE ABRE HASTA LA FILA DEL EXCEL. Cada corte trae sus remitos
//      y cada remito su solapa y su fila. Es literal lo que pidieron.
//
// EN CASTELLANO, A PROPÓSITO. Esta pantalla no pasa por el diccionario de i18n:
// las respuestas las arma el backend con el vocabulario de ellos —tolva, bolsón,
// sin chicas, retiro de frío— y traducirlas sería inventar un idioma que en la
// planta no se habla.
// ============================================================================

const EJEMPLOS = [
  "¿tengo 1.200 bolsas de Spunta?",
  "¿cuánta agata me queda en el galpón?",
  "necesito 6.000 kilos de asterix para exportación",
  "¿qué hay en dospanca?",
];

const ICONO_UBIC = { frigorifico: Snowflake, galpon: Warehouse, planta: Factory };

const nkg = (n) => `${Math.round(n || 0).toLocaleString("es-AR")} kg`;
const nnum = (n) => Math.round(n || 0).toLocaleString("es-AR");

export default function Disponibilidad({ onPreguntar }) {
  const [texto, setTexto] = useState("");
  const [cargando, setCargando] = useState(false);
  const [r, setR] = useState(null);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  const preguntar = async (q) => {
    const pregunta = (q ?? texto).trim();
    if (!pregunta) return;
    setTexto(pregunta);
    setCargando(true);
    setError(null);
    try {
      setR(await api.preguntar(pregunta));
    } catch (e) {
      setError(e.criollo || e.message);
      setR(null);
    } finally {
      setCargando(false);
    }
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl font-bold">¿Tengo o no tengo?</h1>
        <p className="mt-1 text-[0.95rem] text-tinta-suave">
          Preguntá como hablás. La respuesta sale del libro de movimientos —
          con el remito atrás.
        </p>
      </header>

      <Buscador
        texto={texto} setTexto={setTexto} onPreguntar={preguntar}
        cargando={cargando} inputRef={inputRef}
      />

      {!r && !cargando && (
        <div className="flex flex-wrap gap-2">
          {EJEMPLOS.map((e) => (
            <button
              key={e}
              onClick={() => preguntar(e)}
              className="min-h-[44px] rounded-full border border-tinta/10 bg-papel px-4
                         text-sm text-tinta-suave transition hover:border-salvia/40
                         hover:text-tinta"
            >
              {e}
            </button>
          ))}
        </div>
      )}

      {error && (
        <p className="rounded-xl border border-rojo/30 bg-rojo/5 p-4 text-rojo">{error}</p>
      )}

      {r && <Respuesta r={r} onPreguntar={onPreguntar} />}

      <SimularPedido />
    </div>
  );
}

// ---------------------------------------------------------------------------
// El buscador. Grande, con el dictado al lado: en el campo se pregunta hablando.
// ---------------------------------------------------------------------------
function Buscador({ texto, setTexto, onPreguntar, cargando, inputRef }) {
  const [escuchando, setEscuchando] = useState(false);
  const rec = useRef(null);

  // El dictado del navegador. Si no está —Firefox, o el celular sin permiso—
  // el botón no aparece: un botón que no hace nada es peor que ninguno.
  const hayVoz = typeof window !== "undefined" &&
    (window.SpeechRecognition || window.webkitSpeechRecognition);

  const dictar = () => {
    if (!hayVoz) return;
    if (escuchando) { rec.current?.stop(); return; }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const r = new SR();
    r.lang = "es-AR";
    r.interimResults = true;
    r.onresult = (ev) => {
      const dicho = Array.from(ev.results).map((x) => x[0].transcript).join("");
      setTexto(dicho);
      // Sólo se pregunta cuando el navegador da el resultado por final: lo que
      // se escucha a medias todavía puede cambiar de número.
      if (ev.results[ev.results.length - 1].isFinal) onPreguntar(dicho);
    };
    r.onend = () => setEscuchando(false);
    r.onerror = () => setEscuchando(false);
    rec.current = r;
    setEscuchando(true);
    r.start();
  };

  return (
    <div className="flex gap-2">
      <div className="relative flex-1">
        <Search className="pointer-events-none absolute left-4 top-1/2 h-5 w-5
                           -translate-y-1/2 text-tinta-suave" />
        <input
          ref={inputRef}
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && onPreguntar()}
          placeholder="necesito 1.200 bolsas de spunta, ¿tengo?"
          className="h-[60px] w-full rounded-2xl border border-tinta/12 bg-papel pl-12 pr-4
                     text-lg outline-none transition focus:border-salvia
                     focus:ring-2 focus:ring-salvia/20"
        />
      </div>
      {hayVoz && (
        <button
          onClick={dictar}
          aria-label={escuchando ? "Dejar de dictar" : "Preguntar hablando"}
          className={`grid h-[60px] w-[60px] shrink-0 place-items-center rounded-2xl border
                      transition ${escuchando
              ? "border-rojo bg-rojo text-white animate-pulse"
              : "border-tinta/12 bg-papel text-tinta-suave hover:border-salvia/40"}`}
        >
          {escuchando ? <MicOff className="h-6 w-6" /> : <Mic className="h-6 w-6" />}
        </button>
      )}
      <button
        onClick={() => onPreguntar()}
        disabled={cargando}
        className="h-[60px] shrink-0 rounded-2xl bg-salvia px-6 font-semibold text-white
                   transition hover:brightness-110 disabled:opacity-60"
      >
        {cargando ? <Loader2 className="h-5 w-5 animate-spin" /> : "Preguntar"}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
function Respuesta({ r, onPreguntar }) {
  const d = r.respuesta;
  const bloqueado = r.evaluacion?.resultado === "bloqueado";
  const alcanza = d?.alcanza;

  return (
    <div className="space-y-5">
      {/* Lo que la máquina escuchó. Que la persona lo confirme antes de creerle
          es lo que hace que un operario use esto en vez de llamar por teléfono. */}
      <p className="flex items-center gap-2 text-sm text-tinta-suave">
        <Sparkles className="h-4 w-4 shrink-0 text-salvia" />
        Entendí: <strong className="text-tinta">{r.entendido}</strong>
      </p>

      {r.interpretacion?.ambiguo?.variedad && (
        <Aviso tono="amarillo">
          La pregunta nombra {r.interpretacion.ambiguo.variedad.length} variedades
          ({r.interpretacion.ambiguo.variedad.join(", ")}). Elegí una — el sistema
          no desempata solo.
        </Aviso>
      )}
      {r.interpretacion?.ambiguo?.lote_variedad && (
        <Aviso tono="amarillo">{r.interpretacion.ambiguo.lote_variedad}</Aviso>
      )}

      {/* 1 · LA RESPUESTA CORTA. Grande, sola, y con el sí o el no adelante. */}
      <div className={`rounded-2xl border-2 p-5 sm:p-6 ${
        bloqueado || alcanza === false
          ? "border-rojo/40 bg-rojo/[0.04]"
          : alcanza === true
            ? "border-salvia/50 bg-salvia/[0.05]"
            : "border-tinta/10 bg-papel"}`}>
        <div className="flex items-start gap-3">
          {alcanza === true && <Check className="mt-1 h-7 w-7 shrink-0 text-salvia" />}
          {(alcanza === false || bloqueado) && <X className="mt-1 h-7 w-7 shrink-0 text-rojo" />}
          <p className="font-display text-xl font-semibold leading-snug sm:text-2xl">
            {r.titular}
          </p>
        </div>
        {d?.conversion && (
          <p className="mt-2 pl-10 text-sm text-tinta-suave">{d.conversion}</p>
        )}
      </div>

      {r.tipo === "venta_cliente" && <Ventas v={r.ventas} />}

      {d && (
        <>
          {/* 3 · Comprometido vs libre. Nunca en el mismo número. */}
          {d.comprometido > 0 && <Compromiso d={d} />}

          {/* 2 · Dónde está. */}
          <Bloque titulo="Dónde está">
            <div className="space-y-2">
              {d.resumen.por_ubicacion.map((u) => (
                <FilaUbicacion key={u.clave} u={u} total={d.hay} />
              ))}
            </div>
          </Bloque>

          {/* 4 · De qué lotes, con qué calibre. */}
          <div className="grid gap-4 lg:grid-cols-2">
            <Bloque titulo="De qué lotes">
              <div className="flex flex-wrap gap-2">
                {d.resumen.por_lote.slice(0, 14).map((l) => (
                  <button
                    key={l.clave}
                    onClick={() => onPreguntar?.(`qué queda del lote ${l.clave}`)}
                    className="rounded-lg border border-tinta/10 bg-papel px-3 py-2 text-left
                               text-sm transition hover:border-salvia/40"
                  >
                    <span className="font-semibold">lote {l.clave}</span>
                    <span className="ml-2 tabular-nums text-tinta-suave">{nkg(l.kg)}</span>
                  </button>
                ))}
              </div>
            </Bloque>
            <Bloque titulo="Con qué calibre">
              <div className="space-y-2">
                {d.resumen.por_calibre.map((c) => (
                  <div key={c.clave} className="flex items-center justify-between gap-3
                                                border-b border-tinta/5 pb-2 last:border-0">
                    <span className={c.clave === "sin clasificar"
                      ? "text-oro" : "text-tinta"}>{c.clave}</span>
                    <span className="tabular-nums font-semibold">{nkg(c.kg)}</span>
                  </div>
                ))}
              </div>
            </Bloque>
          </div>

          {/* 5 · De dónde sale cada número. */}
          <Evidencia d={d} />

          {d.advertencias?.map((a) => (
            <Aviso key={a.id} tono={a.id === "saldo_anterior" ? "amarillo" : "gris"}>
              {a.texto}
            </Aviso>
          ))}
        </>
      )}

      {r.evaluacion && <Bloqueo ev={r.evaluacion} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
function Compromiso({ d }) {
  const pct = d.hay ? Math.min(100, (d.comprometido / d.hay) * 100) : 0;
  return (
    <Bloque titulo="Tener no es lo mismo que poder vender">
      <div className="flex h-4 overflow-hidden rounded-full bg-tinta/8">
        <div className="bg-oro" style={{ width: `${pct}%` }} />
        <div className="flex-1 bg-salvia" />
      </div>
      <div className="mt-3 flex flex-wrap gap-x-8 gap-y-2 text-sm">
        <Dato color="bg-oro" label="Comprometido" valor={nkg(d.comprometido)} />
        <Dato color="bg-salvia" label="Libre para vender" valor={nkg(d.libre)} />
      </div>
      <ul className="mt-4 space-y-2">
        {d.pedidos_abiertos.map((p) => (
          <li key={p.id} className="flex flex-wrap items-center justify-between gap-2
                                    rounded-lg bg-tinta/[0.03] px-3 py-2 text-sm">
            <span>
              <strong>{p.cliente}</strong>
              <span className="text-tinta-suave"> · {p.variedad}
                {p.calibre ? ` ${p.calibre}` : ""} · entrega {p.entrega}</span>
            </span>
            <span className="tabular-nums font-semibold">{nkg(p.kg)}</span>
          </li>
        ))}
      </ul>
    </Bloque>
  );
}

function Dato({ color, label, valor }) {
  return (
    <span className="flex items-center gap-2">
      <span className={`h-3 w-3 rounded-full ${color}`} />
      <span className="text-tinta-suave">{label}</span>
      <strong className="tabular-nums">{valor}</strong>
    </span>
  );
}

function FilaUbicacion({ u, total }) {
  const pct = total ? (u.kg / total) * 100 : 0;
  return (
    <div className="rounded-xl border border-tinta/8 bg-papel p-3">
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-semibold capitalize">{u.clave.replace(/_/g, " ")}</span>
        <span className="tabular-nums text-lg font-semibold">{nkg(u.kg)}</span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-tinta/8">
        <div className="h-full bg-salvia" style={{ width: `${pct}%` }} />
      </div>
      <p className="mt-2 text-xs text-tinta-suave">
        {u.bolsas > 0 && <>{nnum(u.bolsas)} bolsas · </>}
        {u.kg_granel > 0 && <>{nkg(u.kg_granel)} a granel · </>}
        {u.remitos.length > 0
          ? <>remitos {u.remitos.slice(0, 5).join(", ")}
            {u.remitos.length > 5 && ` +${u.remitos.length - 5}`}</>
          : "sin remito registrado"}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// «Cada número verificable»: acá se abre hasta la fila del Excel de ellos.
// ---------------------------------------------------------------------------
function Evidencia({ d }) {
  const [abierto, setAbierto] = useState(false);
  const [partidas, setPartidas] = useState(null);
  const q = d.pregunta;

  const abrir = async () => {
    setAbierto(!abierto);
    if (partidas || abierto) return;
    try {
      const res = await api.cerebroPartidas({
        variedad: q.variedad, calibre: q.calibre,
        ubicacion: q.ubicacion, lote: q.lote,
      });
      setPartidas(res.partidas);
    } catch { setPartidas([]); }
  };

  return (
    <div className="rounded-2xl border border-tinta/10 bg-papel">
      <button
        onClick={abrir}
        className="flex min-h-[56px] w-full items-center justify-between gap-3 px-5 text-left"
      >
        <span className="flex items-center gap-2 font-semibold">
          <FileSpreadsheet className="h-5 w-5 text-salvia" />
          De dónde sale cada número
        </span>
        <ChevronDown className={`h-5 w-5 shrink-0 transition ${abierto ? "rotate-180" : ""}`} />
      </button>
      {abierto && (
        <div className="border-t border-tinta/8 px-5 py-4">
          {partidas === null && <p className="text-tinta-suave">Buscando…</p>}
          {partidas?.length === 0 && <p className="text-tinta-suave">Sin partidas.</p>}
          {partidas?.length > 0 && (
            <div className="-mx-2 overflow-x-auto">
              <table className="w-full min-w-[720px] text-sm">
                <thead className="text-left text-xs uppercase tracking-wide text-tinta-suave">
                  <tr>
                    <th className="px-2 py-2">Remito</th>
                    <th className="px-2 py-2">Fecha</th>
                    <th className="px-2 py-2">Lote</th>
                    <th className="px-2 py-2">Calibre</th>
                    <th className="px-2 py-2 text-right">Kilos</th>
                    <th className="px-2 py-2">Bolsa / hilo</th>
                    <th className="px-2 py-2">En la planilla</th>
                  </tr>
                </thead>
                <tbody>
                  {partidas.slice(0, 40).map((p) => (
                    <tr key={p.id} className="border-t border-tinta/5">
                      <td className="px-2 py-2 font-semibold">
                        {p.saldo_anterior ? <em className="text-oro">saldo anterior</em> : p.remito}
                      </td>
                      <td className="px-2 py-2 text-tinta-suave">{p.fecha || "—"}</td>
                      <td className="px-2 py-2">{p.lote}</td>
                      <td className="px-2 py-2">{p.calibre}</td>
                      <td className="px-2 py-2 text-right tabular-nums">{nkg(p.kg)}</td>
                      <td className="px-2 py-2 text-tinta-suave">
                        {[p.bolsa_color, p.hilo_color].filter(Boolean).join(" / ") || "—"}
                      </td>
                      <td className="px-2 py-2 text-xs text-tinta-suave">
                        {p.fuente
                          ? `${p.fuente.solapa} · fila ${p.fuente.fila_excel}`
                          : p.motivo_saldo}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// EL BLOQUEO CON ALTERNATIVA. No alcanza con frenar: hay que resolver.
// ---------------------------------------------------------------------------
function Bloqueo({ ev }) {
  if (ev.resultado !== "bloqueado") return null;
  return (
    <div className="space-y-4 rounded-2xl border-2 border-rojo/40 bg-rojo/[0.04] p-5">
      <div className="flex items-start gap-3">
        <TriangleAlert className="mt-0.5 h-6 w-6 shrink-0 text-rojo" />
        <div>
          <p className="font-display text-lg font-semibold">No se puede comprometer</p>
          <p className="mt-1 text-tinta-suave">{ev.motivo.texto}</p>
        </div>
      </div>

      <div>
        <p className="mb-3 font-semibold">De dónde sale lo que falta</p>
        <div className="space-y-3">
          {ev.alternativas.map((a) => <Alternativa key={a.ubicacion + a.preparacion} a={a} />)}
          {ev.alternativas.length === 0 && (
            <p className="text-tinta-suave">
              No hay de esa variedad y ese calibre en ninguna otra ubicación.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function Alternativa({ a }) {
  const Icono = ICONO_UBIC[a.tipo] || Warehouse;
  return (
    <div className="rounded-xl border border-tinta/10 bg-papel p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-semibold">
          <Icono className="h-5 w-5 text-salvia" />
          {a.nombre}
        </span>
        <span className="flex items-center gap-2">
          {a.listo
            ? <Chip tono="verde">listo para cargar</Chip>
            : <Chip tono="amarillo">hay que clasificar</Chip>}
          {a.dias > 0 && <Chip tono="gris">{a.dias} día{a.dias > 1 ? "s" : ""}</Chip>}
        </span>
      </div>

      <p className="mt-2 text-sm text-tinta-suave">
        <Truck className="mr-1 inline h-4 w-4" />{a.movimiento}
      </p>

      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-sm">
        <span>Libre <strong className="tabular-nums">{nkg(a.libre)}</strong></span>
        <span>Cubre <strong className="tabular-nums text-salvia">{nkg(a.cubre_kg)}</strong></span>
        {a.alcanza_solo && <span className="text-salvia">alcanza con este solo</span>}
      </div>

      {a.combinacion && (
        <p className="mt-2 rounded-lg bg-salvia/8 px-3 py-2 text-sm text-salvia">
          {a.combinacion.texto}
        </p>
      )}

      {a.compatibilidad?.notas?.map((n) => (
        <p key={n} className="mt-2 text-sm text-oro">· {n}</p>
      ))}

      <ul className="mt-3 space-y-1 text-sm">
        {a.lotes.filter((l) => l.toma_kg > 0).map((l) => (
          <li key={l.lote} className="flex flex-wrap items-center justify-between gap-2
                                      rounded-lg bg-tinta/[0.03] px-3 py-2">
            <span>
              <strong>lote {l.lote}</strong>
              <span className="text-tinta-suave">
                {" "}· {l.calibres.join(", ")}
                {l.campo && ` · campo ${l.campo.replace(/_/g, " ")}`}
                {l.remitos.length > 0 && ` · remitos ${l.remitos.slice(0, 3).join(", ")}`}
              </span>
            </span>
            <span className="tabular-nums font-semibold">
              {nkg(l.toma_kg)}{l.toma_bolsas > 0 && ` · ${nnum(l.toma_bolsas)} bolsas`}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Simular un pedido: el momento de la demo. Se pide, se frena, se resuelve.
// ---------------------------------------------------------------------------
function SimularPedido() {
  const [cat, setCat] = useState(null);
  const [f, setF] = useState({
    variedad: "asterix", cantidad: 6000, unidad: "kg",
    calibre: "exportacion", ubicacion: "planta_mdp", cliente: "parmentier",
  });
  const [ev, setEv] = useState(null);
  const [cargando, setCargando] = useState(false);

  useEffect(() => { api.cerebroCatalogo().then(setCat).catch(() => setCat(false)); }, []);

  const evaluar = async () => {
    setCargando(true);
    try { setEv(await api.pedidoEvaluar({ ...f, cantidad: Number(f.cantidad) })); }
    catch { setEv(null); }
    finally { setCargando(false); }
  };

  if (!cat) return null;
  const campo = "h-[52px] rounded-xl border border-tinta/12 bg-papel px-3 outline-none " +
                "focus:border-salvia";

  return (
    <div className="rounded-2xl border border-tinta/10 bg-papel p-5">
      <h2 className="font-display text-lg font-semibold">Antes de comprometer un pedido</h2>
      <p className="mt-1 text-sm text-tinta-suave">
        El control corre antes de la venta, no cuando el camión ya está en la playa.
      </p>

      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">
        <select className={campo} value={f.variedad}
                onChange={(e) => setF({ ...f, variedad: e.target.value })}>
          {cat.variedades.map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
        <input className={`${campo} tabular-nums`} type="number" value={f.cantidad}
               onChange={(e) => setF({ ...f, cantidad: e.target.value })} />
        <select className={campo} value={f.unidad}
                onChange={(e) => setF({ ...f, unidad: e.target.value })}>
          <option value="kg">kilos</option>
          <option value="bolsas">bolsas</option>
        </select>
        <select className={campo} value={f.calibre}
                onChange={(e) => setF({ ...f, calibre: e.target.value })}>
          <option value="">cualquier calibre</option>
          {cat.calibres.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <select className={campo} value={f.ubicacion}
                onChange={(e) => setF({ ...f, ubicacion: e.target.value })}>
          <option value="">de donde sea</option>
          {cat.ubicaciones.map((u) => <option key={u.id} value={u.id}>{u.nombre}</option>)}
        </select>
        <button onClick={evaluar} disabled={cargando}
                className="h-[52px] rounded-xl bg-tinta font-semibold text-papel
                           transition hover:brightness-125 disabled:opacity-60">
          {cargando ? "…" : "¿Se puede?"}
        </button>
      </div>

      {ev?.resultado === "se_puede" && (
        <div className="mt-4 rounded-xl border-2 border-salvia/50 bg-salvia/[0.05] p-4">
          <p className="flex items-start gap-2 font-semibold">
            <Check className="mt-0.5 h-5 w-5 shrink-0 text-salvia" />{ev.titular}
          </p>
          <ul className="mt-3 space-y-1 text-sm">
            {ev.origenes.filter((l) => l.toma_kg > 0).map((l) => (
              <li key={l.lote} className="flex justify-between gap-2 rounded-lg
                                          bg-tinta/[0.03] px-3 py-2">
                <span>lote {l.lote} · {l.ubicaciones.join(", ")}
                  {l.remitos.length > 0 && ` · remitos ${l.remitos.slice(0, 3).join(", ")}`}
                </span>
                <strong className="tabular-nums">{nkg(l.toma_kg)}</strong>
              </li>
            ))}
          </ul>
        </div>
      )}
      {ev?.resultado === "bloqueado" && <div className="mt-4"><Bloqueo ev={ev} /></div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
function Ventas({ v }) {
  return (
    <Bloque titulo="Camión por camión">
      <div className="space-y-2">
        {v.camion_por_camion.slice(0, 8).map((r) => (
          <div key={r.remito_id} className="rounded-xl border border-tinta/8 p-3">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="font-semibold">
                Remito {r.remito}
                <span className="ml-2 font-normal text-tinta-suave">
                  {r.fecha} · {r.transporte}{r.chofer ? ` (${r.chofer})` : ""}
                </span>
              </span>
              <span className="tabular-nums font-semibold">{nkg(r.kg)}</span>
            </div>
            {/* El camión arriba, los lotes que llevó abajo. Nunca al revés. */}
            <ul className="mt-2 space-y-1 text-sm text-tinta-suave">
              {r.lineas.map((l, i) => (
                <li key={i} className="flex flex-wrap justify-between gap-2">
                  <span>lote {l.lote} · {l.variedad} · {l.calibre}
                    {l.dtv && ` · DTV ${l.dtv}`}</span>
                  <span className="tabular-nums">{nkg(l.kg)}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </Bloque>
  );
}

// --- piezas chicas ---------------------------------------------------------
function Bloque({ titulo, children }) {
  return (
    <section className="rounded-2xl border border-tinta/10 bg-papel p-5">
      <h2 className="mb-3 font-display text-base font-semibold">{titulo}</h2>
      {children}
    </section>
  );
}

const TONO = {
  verde: "bg-salvia/12 text-salvia",
  amarillo: "bg-oro/12 text-oro",
  gris: "bg-tinta/8 text-tinta-suave",
};

function Chip({ tono = "gris", children }) {
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-semibold ${TONO[tono]}`}>
      {children}
    </span>
  );
}

function Aviso({ tono = "gris", children }) {
  return (
    <p className={`rounded-xl px-4 py-3 text-sm ${TONO[tono]}`}>{children}</p>
  );
}
