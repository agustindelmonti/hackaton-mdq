import { useEffect, useState } from "react";
import {
  Mic, Send, ArrowRight, Check, PackageCheck, TriangleAlert, Clock,
  MapPin, Loader2,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import { api } from "../lib/api";
import { num, fecha } from "../lib/format";
import { useT } from "../lib/i18n";
import { toast } from "../lib/toastStore";
import EstadoConexion, { ColaPendiente, enviarPendiente } from "../components/EstadoConexion";
import { interpretarLocal } from "../lib/interpretarLocal";
import {
  estaOnline, encolar, pendientes, guardarSnapshot, leerSnapshot,
  sincronizar, borrarDeLaCola,
} from "../lib/offline";

// ============================================================================
// N01 · EL STOCK SE MUEVE HABLANDO.
// ----------------------------------------------------------------------------
// «Los operarios registran movimientos mediante voz o texto, validando
//  automáticamente la disponibilidad para evitar discrepancias entre el origen
//  y el destino.»
//
// Dos decisiones que definen esta pantalla:
//
//  1. NADA SE GUARDA SIN QUE UN HUMANO CONFIRME. Lo que vuelve del dictado es
//     una PROPUESTA: se ve entera, con los kilos ya convertidos y el resultado
//     de la validación, antes de tocar el stock.
//  2. SI HAY VARIOS LOTES POSIBLES, ELIGE LA PERSONA. El sistema nunca desempata
//     solo — mover el lote equivocado son bolsones reales en una cámara real.
//
// Y la cola de "sin confirmar en destino" está arriba de todo a propósito: esos
// kilos no están en ningún lado, y son los que terminan en el papelón.
// ============================================================================

export default function Movimientos({ onPreguntar }) {
  const t = useT();
  const [d, setD] = useState(null);
  const [texto, setTexto] = useState("");
  const [prop, setProp] = useState(null);
  const [pensando, setPensando] = useState(false);
  const [elegido, setElegido] = useState(null);
  const [guardando, setGuardando] = useState(false);
  const [cola, setCola] = useState([]);
  const [sinRed, setSinRed] = useState(!estaOnline());

  const refrescarCola = () => pendientes().then(setCola).catch(() => {});

  // Con red: se traen los movimientos Y se guarda el snapshot del stock, que es
  // lo que permite seguir trabajando cuando la señal se corta. Sin red: se
  // muestra lo último que se sabe y se dice que es lo último que se sabe.
  const cargar = async () => {
    refrescarCola();
    try {
      const datos = await api.movimientos({ limite: 40 });
      setD(datos);
      setSinRed(false);
      try {
        const snap = await api.snapshotOffline();
        await guardarSnapshot("stock", snap);
      } catch { /* el snapshot es un extra: si falla, el online sigue igual */ }
    } catch {
      const snap = await leerSnapshot("stock");
      setSinRed(true);
      setD(snap ? { resumen: {}, movimientos: [], sin_confirmar: [], offline: true }
                : false);
    }
  };
  useEffect(() => { cargar(); }, []);

  const interpretar = async (frase) => {
    const f = (frase ?? texto).trim();
    if (!f) return;
    setPensando(true); setProp(null); setElegido(null);
    try {
      if (estaOnline()) {
        setProp(await api.movimientoInterpretar(f));
        setSinRed(false);
      } else {
        throw new Error("sin red");
      }
    } catch {
      // SIN SEÑAL EL OPERARIO SIGUE TRABAJANDO: el mismo algoritmo determinista
      // corre en el celular, contra el último stock conocido.
      const snap = await leerSnapshot("stock");
      if (snap?.datos) {
        setProp(interpretarLocal(f, snap.datos));
        setSinRed(true);
      } else {
        toast(t("mov.fallo_interpretar"));
      }
    } finally {
      setPensando(false);
    }
  };

  const confirmar = async () => {
    if (!prop) return;
    const p = prop.propuesta;
    const codigo = elegido ?? p.codigo;
    if (!codigo || !p.kg) return;
    setGuardando(true);
    const payload = {
      codigo, kg: p.kg, destino: p.destino, tipo: p.tipo,
      origen_id: p.origen_id, nota: p.nota, canal: "texto",
    };
    try {
      if (!estaOnline()) throw new Error("sin red");
      await api.movimientoRegistrar(payload);
      toast(t("mov.registrado"));
      setTexto(""); setProp(null); setElegido(null);
      await cargar();
    } catch (err) {
      // Un 409 es el sistema frenando por falta de stock: eso NO se encola, se
      // le dice al operario en la cara. Lo que se encola es lo que no pudo
      // llegar por falta de señal.
      if (err && err.status === 409) {
        toast(t("mov.rechazado"));
      } else {
        await encolar({
          tipo_cola: "movimiento",
          payload,
          resumen: `${p.lote || t("mov.p_tipo")} · ${p.kg} kg · ${p.origen || "?"} → ${p.destino || "?"}`,
        });
        toast(t("mov.encolado"));
        setTexto(""); setProp(null); setElegido(null);
        refrescarCola();
      }
    } finally {
      setGuardando(false);
    }
  };

  const confirmarDestino = async (numero) => {
    try {
      if (!estaOnline()) throw new Error("sin red");
      await api.movimientoConfirmar(numero);
      toast(t("mov.confirmado", { n: numero }));
      await cargar();
    } catch (err) {
      if (err && err.status === 409) { toast(t("mov.fallo_confirmar")); return; }
      await encolar({
        tipo_cola: "confirmacion",
        payload: { numero },
        resumen: t("off.confirmar_de", { n: numero }),
      });
      toast(t("mov.encolado"));
      refrescarCola();
    }
  };

  if (d === null) return <Esqueleto />;
  if (d === false) return <p className="text-tinta-suave">{t("mov.error")}</p>;

  const r = d.resumen || {};
  const abiertos = d.sin_confirmar || [];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-3xl font-bold">{t("mov.titulo")}</h1>
        <p className="mt-1 text-[0.95rem] text-tinta-suave">{t("mov.subtitulo")}</p>
      </header>

      {/* Lo primero: decir la verdad sobre si hay señal y qué falta mandar. */}
      <EstadoConexion />
      {cola.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-[0.8rem] font-semibold uppercase tracking-wide text-tinta-suave">
            {t("off.cola_titulo", { n: cola.length })}
          </h2>
          <ColaPendiente
            items={cola}
            onReintentar={async (it) => {
              await borrarDeLaCola(it.id);
              refrescarCola();
              toast(t("off.descartado"));
            }}
          />
        </section>
      )}

      {/* --- lo que quedó en el aire: primero, siempre ------------------- */}
      {abiertos.length > 0 && (
        <section className="overflow-hidden rounded-[var(--radius-card)] border border-rojo/30 bg-superficie sombra-papel">
          <header className="flex items-center gap-2 border-b border-linea bg-rojo/[0.04] px-4 py-3">
            <Clock size={16} className="text-rojo" />
            <p className="flex-1 font-display text-[1rem] font-bold">
              {t("mov.sin_confirmar", { n: abiertos.length })}
            </p>
            <span className="plata text-[0.9rem] text-rojo">{num(r.kg_en_transito)} kg</span>
          </header>
          <ul className="divide-y divide-linea">
            {abiertos.map((m) => (
              <li key={m.numero} className="flex flex-wrap items-center gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="text-[0.9rem] font-medium">
                    {m.lote} · {num(m.kg)} kg ({m.bolsones} {t("mov.bolsones")})
                  </p>
                  <p className="mt-0.5 flex flex-wrap items-center gap-1 text-[0.8rem] text-tinta-suave">
                    {m.origen} <ArrowRight size={12} /> {m.destino}
                    <span className="ml-1">· {m.numero} · {fecha(m.fecha)}</span>
                  </p>
                </div>
                <span className={`shrink-0 rounded-full px-2 py-0.5 text-[0.72rem] ${m.vencido ? "bg-rojo/10 text-rojo" : "bg-oro/10 text-oro"}`}>
                  {t("mov.dias_transito", { n: m.dias_en_transito })}
                </span>
                <button
                  type="button"
                  onClick={() => confirmarDestino(m.numero)}
                  className="shrink-0 rounded-lg bg-tinta px-3 py-1.5 text-[0.82rem] font-medium text-crema transition hover:bg-tinta/90"
                >
                  {t("mov.confirmar_llegada")}
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {/* --- el dictado ---------------------------------------------------- */}
      <section className="rounded-[var(--radius-card)] border border-linea bg-superficie p-4 sombra-papel">
        <p className="mb-2 font-display text-[1.05rem] font-bold">{t("mov.registrar")}</p>
        <p className="mb-3 text-[0.85rem] text-tinta-suave">{t("mov.registrar_ayuda")}</p>
        <div className="flex gap-2">
          <input
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && interpretar()}
            placeholder={t("mov.placeholder")}
            className="min-w-0 flex-1 rounded-lg border border-linea bg-crema/50 px-3 py-2.5 text-[0.95rem] outline-none focus:border-hielo"
          />
          <button
            type="button"
            disabled={pensando || !texto.trim()}
            onClick={() => interpretar()}
            className="flex shrink-0 items-center gap-1.5 rounded-lg bg-tinta px-4 py-2.5 text-[0.9rem] font-medium text-crema transition hover:bg-tinta/90 disabled:opacity-40"
          >
            {pensando ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
            <span className="hidden sm:inline">{t("mov.interpretar")}</span>
          </button>
        </div>

        {/* ejemplos reales del piso: bajan la barrera de la primera vez */}
        <div className="mt-2 flex flex-wrap gap-1.5">
          {[t("mov.ej1"), t("mov.ej2"), t("mov.ej3")].map((e) => (
            <button
              key={e}
              type="button"
              onClick={() => { setTexto(e); interpretar(e); }}
              className="rounded-full border border-linea px-2.5 py-1 text-[0.78rem] text-tinta-suave transition hover:bg-crema"
            >
              {e}
            </button>
          ))}
        </div>

        {prop && (
          <Propuesta
            prop={prop}
            elegido={elegido}
            onElegir={setElegido}
            onConfirmar={confirmar}
            guardando={guardando}
            onCancelar={() => { setProp(null); setElegido(null); }}
          />
        )}
      </section>

      {/* --- el registro ---------------------------------------------------- */}
      <section>
        <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-display text-lg font-bold">{t("mov.historial")}</h2>
          <p className="text-[0.8rem] text-tinta-suave">
            {t("mov.resumen", { total: num(r.total), semana: num(r.ultimos_7_dias) })}
          </p>
        </div>
        <ul className="divide-y divide-linea overflow-hidden rounded-[var(--radius-card)] border border-linea bg-superficie">
          {(d.movimientos || []).map((m) => (
            <li key={m.numero} className="flex flex-wrap items-center gap-2 px-4 py-2.5 text-[0.85rem]">
              <span className={`shrink-0 rounded px-1.5 py-0.5 text-[0.7rem] ${
                m.tipo === "egreso" ? "bg-hielo/10 text-hielo"
                : m.tipo === "descarte" ? "bg-rojo/10 text-rojo"
                : m.tipo === "ingreso" ? "bg-salvia/10 text-salvia"
                : "bg-crema text-tinta-suave"}`}>
                {t(`mov.tipo_${m.tipo}`)}
              </span>
              <span className="font-medium">{m.lote}</span>
              <span className="min-w-0 flex-1 truncate text-tinta-suave">
                {m.origen} → {m.destino}
              </span>
              <span className="tabular-nums">{num(m.kg)} kg</span>
              <span className="shrink-0 text-[0.78rem] text-tinta-suave">
                {m.registrado_por} · {fecha(m.fecha)}
              </span>
              {m.estado === "en_transito" && (
                <Clock size={13} className="shrink-0 text-oro" aria-label={t("mov.en_transito")} />
              )}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

// --- la propuesta: lo que se entendió, antes de tocar el stock --------------
function Propuesta({ prop, elegido, onElegir, onConfirmar, guardando, onCancelar }) {
  const t = useT();
  const p = prop.propuesta || {};
  const v = prop.validacion;
  const varios = prop.faltantes?.includes("cual_lote");
  const rechazado = v && !v.ok;
  const listo = (p.codigo || elegido) && p.kg && p.destino && !rechazado;

  return (
    <div className="mt-4 rounded-lg border border-hielo/30 bg-hielo/[0.03] p-3">
      <p className="mb-2 flex items-center gap-2 text-[0.72rem] font-semibold uppercase tracking-wide text-tinta-suave">
        <PackageCheck size={13} /> {t("mov.entendi")}
        <span className="rounded-full bg-crema px-1.5 py-px text-[0.65rem] normal-case">
          {prop.motor === "claude" ? t("mov.motor_ia") : t("mov.motor_local")}
        </span>
      </p>

      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 text-[0.88rem]">
        <Dato k={t("mov.p_tipo")} v={t(`mov.tipo_${p.tipo}`)} />
        <Dato k={t("mov.p_cantidad")} v={p.kg ? `${num(p.kg)} kg (${p.bolsones} ${t("mov.bolsones")})` : "—"} />
        <Dato k={t("mov.p_origen")} v={p.origen || "—"} />
        <Dato k={t("mov.p_destino")} v={p.destino || "—"} />
      </dl>

      {/* Varios candidatos: NO desempata el sistema. */}
      {varios && (
        <div className="mt-3">
          <p className="mb-1.5 text-[0.85rem] font-medium">{t("mov.cual_lote")}</p>
          <ul className="space-y-1">
            {(prop.candidatos || []).map((c) => (
              <li key={c.codigo}>
                <button
                  type="button"
                  onClick={() => onElegir(c.codigo)}
                  className={`flex w-full flex-wrap items-center gap-2 rounded-lg border px-3 py-2 text-left text-[0.85rem] transition
                    ${elegido === c.codigo ? "border-hielo bg-hielo/8" : "border-linea hover:bg-crema"}`}
                >
                  <span className="font-medium">{c.lote}</span>
                  <span className="min-w-0 flex-1 truncate text-tinta-suave">
                    <MapPin size={11} className="mr-1 inline" />{c.ubicacion} · {c.camara}
                  </span>
                  <span className="tabular-nums text-tinta-suave">{num(c.stock)} kg</span>
                  {elegido === c.codigo && <Check size={14} className="text-hielo" />}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* El rechazo con su número: no se suaviza. */}
      {rechazado && (
        <div className="mt-3 flex gap-2 rounded-lg border border-rojo/30 bg-rojo/[0.05] p-2.5">
          <TriangleAlert size={15} className="mt-0.5 shrink-0 text-rojo" />
          <div className="text-[0.85rem]">
            <p className="font-medium text-rojo">{t(`mov.rechazo_${v.motivo}`)}</p>
            {v.motivo === "sin_stock_suficiente" && (
              <p className="text-tinta">
                {t("mov.rechazo_detalle", {
                  pedido: num(v.pedido_kg), disp: num(v.disponible_kg), falta: num(v.faltante_kg),
                })}
              </p>
            )}
          </div>
        </div>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          disabled={!listo || guardando}
          onClick={onConfirmar}
          className="rounded-lg bg-salvia px-3.5 py-2 text-[0.88rem] font-medium text-crema transition hover:bg-salvia/90 disabled:opacity-40"
        >
          {guardando ? t("mov.guardando") : t("mov.confirmar")}
        </button>
        <button
          type="button"
          onClick={onCancelar}
          className="rounded-lg border border-linea px-3.5 py-2 text-[0.88rem] transition hover:bg-crema"
        >
          {t("mov.cancelar")}
        </button>
      </div>
    </div>
  );
}

const Dato = ({ k, v }) => (
  <>
    <dt className="text-tinta-suave">{k}</dt>
    <dd className="font-medium">{v}</dd>
  </>
);

function Esqueleto() {
  return (
    <div className="space-y-6" aria-busy="true">
      <div className="h-9 w-64 animate-pulse rounded bg-linea" />
      <div className="h-32 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
      <div className="h-40 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
    </div>
  );
}
