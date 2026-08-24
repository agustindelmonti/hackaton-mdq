import { useEffect, useState } from "react";
import {
  Snowflake, Warehouse, TriangleAlert, Sprout, MapPin, ArrowRight,
  ShieldCheck, PackageCheck, Plus, Pencil, Trash2, Loader2, FlaskConical, Factory,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import UbicacionForm from "../components/UbicacionForm";
import { api } from "../lib/api";
import { num, peso, pesoCorto } from "../lib/format";
import { useT } from "../lib/i18n";
import { useSession } from "../lib/auth";
import { toast } from "../lib/toastStore";

// ============================================================================
// N02 · LA VISTA ÚNICA — cuatro ubicaciones, una sola verdad.
// ----------------------------------------------------------------------------
// El brief lo dice sin vueltas: «Nadie tiene una visión única y confiable de
// cuánto stock hay y dónde está en un momento dado». Hasta hoy eso vivía en una
// planilla que editaban cuatro personas a la vez.
//
// Esta pantalla es esa visión. Y tiene una decisión de diseño que importa: lo
// primero que se ve NO es el total lindo, es lo que está en discusión. Un total
// que nadie puede defender no sirve de nada; el número que vale es el que
// sobrevive a que alguien pregunte «¿y esto está verificado?».
// ============================================================================

// Mismo mapa tipo→ícono que el resto de las vistas del mapa de operación
// (ver TIPOS_UBICACION en UbicacionForm.jsx): elegir el tipo en el formulario
// ES elegir el ícono, acá y en MapaOperacion.jsx.
const ICONO = {
  frigorifico: Snowflake, galpon: Warehouse, campo: Sprout,
  laboratorio: FlaskConical, planta: Factory,
};

const COLOR = {
  verde: { borde: "border-salvia/30", chip: "bg-salvia/10 text-salvia", punto: "bg-salvia" },
  amarillo: { borde: "border-oro/35", chip: "bg-oro/10 text-oro", punto: "bg-oro" },
  rojo: { borde: "border-rojo/35", chip: "bg-rojo/10 text-rojo", punto: "bg-rojo" },
};

export default function Ubicaciones({ onPreguntar }) {
  const t = useT();
  const { usuario } = useSession() || {};
  const puedeGestionar = Boolean(usuario?.features?.includes("gestion_ubicaciones"));
  const [d, setD] = useState(null);
  const [form, setForm] = useState(null); // null | "crear" | <ubicacion a editar>

  const recargar = () => api.ubicaciones().then(setD).catch(() => setD(false));
  useEffect(() => { recargar(); }, []);

  // Tres estados explícitos: null = todavía no sé (esqueleto), false = falló,
  // vacío = no hay datos. Mostrar el estado vacío antes de saber es mentir.
  if (d === null) return <Esqueleto />;
  if (d === false) return <p className="text-tinta-suave">{t("ubi.error")}</p>;

  const r = d.resumen || {};
  const ubis = d.ubicaciones || [];
  const enDiscusion = r.diferencias_abiertas > 0 || r.movimientos_sin_confirmar > 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-bold">{t("ubi.titulo")}</h1>
          <p className="mt-1 text-[0.95rem] text-tinta-suave">{t("ubi.subtitulo")}</p>
        </div>
        {puedeGestionar && (
          <button type="button" onClick={() => setForm("crear")}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-full bg-tinta px-4 py-2.5 text-[0.86rem] font-semibold text-crema active:scale-95">
            <Plus size={15} /> {t("ubi.nueva")}
          </button>
        )}
      </header>

      {form && (
        <UbicacionForm
          inicial={form === "crear" ? null : form}
          onCerrar={() => setForm(null)}
          onGuardado={recargar}
        />
      )}

      {/* El titular: el total, y ENSEGUIDA cuánto de ese total está en duda. */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Kpi
          icono={PackageCheck}
          valor={`${num(r.toneladas_total)} t`}
          etiqueta={t("ubi.kpi_stock")}
          nota={t("ubi.kpi_stock_nota", { lotes: num(r.lotes), ubis: r.ubicaciones })}
        />
        <Kpi
          icono={ShieldCheck}
          valor={pesoCorto(r.valor_total)}
          etiqueta={t("ubi.kpi_valor")}
          nota={t("ubi.kpi_valor_nota")}
        />
        <Kpi
          icono={TriangleAlert}
          tono={r.diferencias_abiertas ? "alerta" : "ok"}
          valor={num(r.diferencias_abiertas)}
          etiqueta={t("ubi.kpi_dif")}
          nota={r.diferencias_abiertas
            ? t("ubi.kpi_dif_nota", { kg: num(r.kg_en_diferencia), plata: pesoCorto(r.plata_en_diferencia) })
            : t("ubi.kpi_dif_ok")}
        />
        <Kpi
          icono={ArrowRight}
          tono={r.movimientos_sin_confirmar ? "alerta" : "ok"}
          valor={num(r.movimientos_sin_confirmar)}
          etiqueta={t("ubi.kpi_transito")}
          nota={r.movimientos_sin_confirmar
            ? t("ubi.kpi_transito_nota", { kg: num(r.kg_en_transito) })
            : t("ubi.kpi_transito_ok")}
        />
      </div>

      {enDiscusion && (
        <AngelaSays tone="atencion">
          {t("ubi.angela", {
            n: r.diferencias_abiertas,
            plata: peso(r.plata_en_diferencia),
            transito: num(r.kg_en_transito),
          })}{" "}
          <button
            type="button"
            onClick={() => onPreguntar?.(t("ubi.angela_pregunta"))}
            className="font-medium text-hielo underline underline-offset-2"
          >
            {t("ubi.angela_accion")}
          </button>
        </AngelaSays>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {ubis.map((u) => (
          <Tarjeta key={u.id} u={u} onPreguntar={onPreguntar}
            puedeGestionar={puedeGestionar}
            onEditar={() => setForm(u)}
            onEliminado={recargar} />
        ))}
      </div>
    </div>
  );
}

// --- una ubicación ----------------------------------------------------------
function Tarjeta({ u, onPreguntar, puedeGestionar, onEditar, onEliminado }) {
  const t = useT();
  const Icono = ICONO[u.tipo] || MapPin;
  const c = COLOR[u.estado] || COLOR.verde;
  const sinFrio = u.tipo === "galpon";
  const [confirmando, setConfirmando] = useState(false);
  const [eliminando, setEliminando] = useState(false);

  const eliminar = async () => {
    setEliminando(true);
    try {
      await api.ubicacionEliminar(u.id);
      toast(t("ubi.eliminar_ok"));
      onEliminado?.();
    } catch {
      toast(t("ubi.error_generico"), "error");
    }
    setEliminando(false);
    setConfirmando(false);
  };

  return (
    <section className={`overflow-hidden rounded-[var(--radius-card)] border ${c.borde} bg-superficie sombra-papel`}>
      <header className="flex items-start gap-3 border-b border-linea px-4 py-3">
        <span className="mt-0.5 shrink-0 rounded-lg bg-hielo/10 p-2 text-hielo">
          <Icono size={18} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 shrink-0 rounded-full ${c.punto}`} aria-hidden />
            <h2 className="truncate font-display text-[1.05rem] font-bold leading-tight">{u.nombre}</h2>
          </div>
          <p className="mt-0.5 truncate text-[0.78rem] text-tinta-suave">{u.direccion}</p>
        </div>
        <div className="shrink-0 text-right">
          <p className="plata text-xl font-medium">{num(u.toneladas)} t</p>
          <p className="text-[0.7rem] text-tinta-suave">{t("ubi.lotes", { n: num(u.lotes) })}</p>
        </div>
      </header>

      {puedeGestionar && (
        <div className="flex items-center gap-2 border-b border-linea bg-crema/40 px-4 py-1.5">
          {confirmando ? (
            <>
              <span className="flex-1 text-[0.76rem] text-rojo">
                {t("ubi.eliminar_confirmar", { nombre: u.nombre })}
              </span>
              <button type="button" onClick={eliminar} disabled={eliminando}
                className="rounded-full bg-rojo px-2.5 py-1 text-[0.74rem] font-semibold text-crema disabled:opacity-50">
                {eliminando ? <Loader2 size={12} className="animate-spin" /> : t("ubi.eliminar")}
              </button>
              <button type="button" onClick={() => setConfirmando(false)}
                className="text-[0.74rem] font-semibold text-tinta-suave">
                {t("ubi.cancelar")}
              </button>
            </>
          ) : (
            <>
              <button type="button" onClick={onEditar}
                className="flex items-center gap-1 rounded-full px-2 py-1 text-[0.74rem] font-semibold text-tinta-suave hover:bg-crema">
                <Pencil size={12} /> {t("ubi.editar")}
              </button>
              <button type="button" onClick={() => setConfirmando(true)}
                className="flex items-center gap-1 rounded-full px-2 py-1 text-[0.74rem] font-semibold text-rojo hover:bg-rojo/10">
                <Trash2 size={12} /> {t("ubi.eliminar")}
              </button>
            </>
          )}
        </div>
      )}

      <div className="space-y-3 px-4 py-3">
        {/* ocupación: cuánto queda de lugar, que es la pregunta del encargado */}
        <div>
          <div className="mb-1 flex items-baseline justify-between text-[0.78rem]">
            <span className="text-tinta-suave">{t("ubi.ocupacion")}</span>
            <span className="font-medium">{u.ocupacion_pct}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-linea">
            <div
              className={`h-full rounded-full ${u.ocupacion_pct > 90 ? "bg-oro" : "bg-hielo"}`}
              style={{ width: `${Math.min(100, u.ocupacion_pct || 0)}%` }}
            />
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-[0.75rem]">
          <span className="rounded-full bg-hielo/8 px-2 py-0.5 text-hielo">
            {peso(u.valor)}
          </span>
          {sinFrio ? (
            // El galpón no tiene frío y eso NO es un detalle: lo que entra ahí
            // corre a reloj natural y tiene que salir. Se dice en la tarjeta.
            <span className="rounded-full bg-oro/10 px-2 py-0.5 text-oro">
              {t("ubi.sin_frio")}
            </span>
          ) : (
            <span className="rounded-full bg-crema px-2 py-0.5 text-tinta-suave">
              {t("ubi.temp", { t: u.temp_objetivo })}
            </span>
          )}
          {u.camaras?.length > 0 && (
            <span className="text-tinta-suave">{u.camaras.join(" · ")}</span>
          )}
        </div>

        {u.diferencias_abiertas > 0 && (
          <button
            type="button"
            onClick={() => onPreguntar?.(t("ubi.pregunta_dif", { u: u.nombre }))}
            className="flex w-full items-center gap-2 rounded-lg border border-rojo/25 bg-rojo/[0.04] px-3 py-2 text-left transition hover:bg-rojo/[0.07]"
          >
            <TriangleAlert size={15} className="shrink-0 text-rojo" />
            <span className="flex-1 text-[0.82rem]">
              {t("ubi.dif_abiertas", {
                n: u.diferencias_abiertas, kg: num(u.kg_en_diferencia),
              })}
            </span>
            <ArrowRight size={14} className="shrink-0 text-rojo" />
          </button>
        )}

        {u.ya_brotados > 0 && (
          // Lo que YA brotó no es una advertencia: es plata que ya cambió de
          // categoría. Va con su número y su valor, no mezclado con lo que
          // todavía se puede salvar.
          <div className="flex items-center gap-2 rounded-lg border border-oro/30 bg-oro/[0.05] px-3 py-2 text-[0.82rem]">
            <Sprout size={14} className="shrink-0 text-oro" />
            <span className="flex-1">{t("ubi.ya_brotados", { n: u.ya_brotados })}</span>
            <span className="plata shrink-0 text-oro">{pesoCorto(u.ya_brotados_valor)}</span>
          </div>
        )}

        {u.por_brotar_45d?.length > 0 && (
          // El reloj real del negocio: la semilla no vence, brota. Un lote que
          // brota antes de despacharse deja de ser semilla de su categoría.
          <div className="rounded-lg border border-linea bg-crema/60 px-3 py-2">
            <p className="mb-1 flex items-center gap-1.5 text-[0.75rem] font-semibold text-tinta-suave">
              <Sprout size={13} /> {t("ubi.por_brotar")}
            </p>
            <ul className="space-y-0.5 text-[0.8rem]">
              {u.por_brotar_45d.slice(0, 3).map((l) => (
                <li key={l.codigo} className="flex justify-between gap-2">
                  <span className="truncate">{l.lote}</span>
                  <span className={`shrink-0 tabular-nums ${l.dias <= 0 ? "text-rojo" : l.dias <= 20 ? "text-oro" : "text-tinta-suave"}`}>
                    {l.dias <= 0 ? t("ubi.brotado") : t("ubi.dias", { n: l.dias })}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}

// --- piezas chicas ----------------------------------------------------------
function Kpi({ icono: Icono, valor, etiqueta, nota, tono = "neutro" }) {
  const color = tono === "alerta" ? "text-rojo" : tono === "ok" ? "text-salvia" : "text-tinta";
  return (
    <div className="rounded-[var(--radius-card)] border border-linea bg-superficie px-4 py-3 sombra-papel">
      <div className="flex items-center gap-2 text-[0.72rem] uppercase tracking-wide text-tinta-suave">
        <Icono size={13} /> {etiqueta}
      </div>
      <p className={`plata mt-1 text-2xl font-medium ${color}`}>{valor}</p>
      <p className="mt-0.5 text-[0.75rem] leading-snug text-tinta-suave">{nota}</p>
    </div>
  );
}

function Esqueleto() {
  return (
    <div className="space-y-6" aria-busy="true">
      <div className="h-9 w-72 animate-pulse rounded bg-linea" />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-24 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="h-56 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
        ))}
      </div>
    </div>
  );
}
