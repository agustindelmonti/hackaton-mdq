import { useCallback, useEffect, useState } from "react";
import {
  Send, X, Check, Plus, CircleDot, Clock, CheckCircle2, ChevronRight, Loader2,
} from "lucide-react";
import AngelaMark from "../components/AngelaMark";
import Avatar from "../components/Avatar";
import { api } from "../lib/api";
import { equipoReal } from "../lib/equipoReal";
import { toast } from "../lib/toastStore";
import { useT } from "../lib/i18n";

// ============================================================================
// TAREAS DEL EQUIPO — el bloque donde se reparte el trabajo.
// ----------------------------------------------------------------------------
// Tres cosas, en el orden en que se usan:
//
//   1. LO QUE ÁNGELA PROPONE. Cada propuesta sale de una señal real (un
//      traslado sin confirmar, un conteo abierto, una orden frenada) y viene
//      con LA PERSONA YA CALCULADA por rol y ubicación. El botón dice el
//      nombre: "Asignar a Néstor". Nada se manda solo.
//   2. ASIGNAR A MANO. "Néstor, contá la cámara 3." Dos campos y listo.
//   3. QUIÉN TIENE QUÉ. La pregunta que hoy se contesta por WhatsApp:
//      «¿alguien confirmó lo de Chapadmalal?».
//
// El destinatario la ve en SU pantalla (y en su celular), la marca hecha, y
// quien la asignó lo ve acá. Ese ida y vuelta es la diferencia entre un tablero
// y una herramienta.
// ============================================================================

const TONO_PRIORIDAD = {
  hoy: { cls: "bg-rojo/10 text-rojo", Icon: CircleDot },
  semana: { cls: "bg-oro/15 text-oro-tinta", Icon: Clock },
  cuando_puedas: { cls: "bg-papel-hondo text-tinta-suave", Icon: Clock },
};

export default function TareasEquipo({ onCambio }) {
  const t = useT();
  // La nómina sale del endpoint del equipo (el mismo que usa "Ver como"), no de
  // /api/perfiles: el ENCARGADO también reparte trabajo y ese endpoint es del
  // dueño. Una lista sola para todo el sistema.
  const [equipo, setEquipo] = useState([]);
  useEffect(() => { equipoReal().then(setEquipo).catch(() => {}); }, []);
  const [sugeridas, setSugeridas] = useState(null);
  const [panorama, setPanorama] = useState(null);
  const [asignando, setAsignando] = useState(null);   // id de la sugerencia en curso
  const [descartadas, setDescartadas] = useState({});
  const [nueva, setNueva] = useState({ titulo: "", para: "" });
  const [creando, setCreando] = useState(false);

  const cargar = useCallback(() => {
    api.tareasSugeridas().then((d) => setSugeridas(d.sugeridas || [])).catch(() => setSugeridas([]));
    api.tareasPanorama().then(setPanorama).catch(() => setPanorama(null));
  }, []);
  useEffect(cargar, [cargar]);

  const asignar = async (s) => {
    setAsignando(s.id);
    try {
      await api.tareaCrear({
        titulo: s.titulo, para: s.para.username, origen: s.id,
        seccion: s.seccion, prioridad: s.prioridad, detalle: s.detalle,
      });
      toast(t("tareas.asignada", { nombre: s.para.nombre }));
      cargar();
      onCambio?.();
    } catch {
      toast(t("tareas.error"), "error");
    }
    setAsignando(null);
  };

  const crear = async (e) => {
    e?.preventDefault();
    if (!nueva.titulo.trim() || !nueva.para) return;
    setCreando(true);
    try {
      await api.tareaCrear({ titulo: nueva.titulo.trim(), para: nueva.para, prioridad: "semana" });
      const p = equipo.find((x) => x.username === nueva.para);
      toast(t("tareas.asignada", { nombre: p?.nombre || nueva.para }));
      setNueva({ titulo: "", para: "" });
      cargar();
      onCambio?.();
    } catch {
      toast(t("tareas.error"), "error");
    }
    setCreando(false);
  };

  const visibles = (sugeridas || []).filter((s) => !descartadas[s.id]);

  return (
    <section className="space-y-4">
      <div className="flex items-center gap-2">
        <AngelaMark size={22} />
        <h2 className="font-display text-[1.15rem] font-bold">{t("tareas.titulo")}</h2>
        <span className="ml-auto text-[0.78rem] text-tinta-suave">{t("tareas.vos_decidis")}</span>
      </div>

      {/* 1 · lo que Ángela propone */}
      <div className="overflow-hidden rounded-[var(--radius-card)] border border-linea bg-crema sombra-papel">
        <div className="flex items-center gap-2 border-b border-linea px-4 py-2.5">
          <h3 className="font-display text-[0.95rem] font-bold">{t("tareas.propone")}</h3>
          {visibles.length > 0 && (
            <span className="grid h-5 min-w-5 place-items-center rounded-full bg-papel-hondo px-1.5 text-[0.7rem] font-bold text-tinta-suave">
              {visibles.length}
            </span>
          )}
        </div>
        {sugeridas === null ? (
          <p className="px-4 py-3 text-[0.86rem] text-tinta-suave">{t("tareas.cargando")}</p>
        ) : visibles.length === 0 ? (
          <p className="px-4 py-3 text-[0.86rem] text-tinta-suave">{t("tareas.sin_propuestas")}</p>
        ) : (
          visibles.map((s) => {
            const p = TONO_PRIORIDAD[s.prioridad] || TONO_PRIORIDAD.semana;
            return (
              <div key={s.id} className="border-b border-linea/70 px-4 py-3 last:border-0">
                <div className="flex flex-wrap items-start gap-x-3 gap-y-2">
                  <span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[0.7rem] font-semibold ${p.cls}`}>
                    <p.Icon size={11} /> {t(`tareas.p_${s.prioridad}`)}
                  </span>
                  <div className="min-w-0 flex-1 basis-64">
                    <p className="text-[0.92rem] font-semibold leading-snug">{s.titulo}</p>
                    <p className="mt-0.5 text-[0.82rem] leading-snug text-tinta-suave">{s.detalle}</p>
                  </div>
                  <span className="flex shrink-0 items-center gap-1.5">
                    <button
                      onClick={() => asignar(s)}
                      disabled={asignando === s.id}
                      className="inline-flex items-center gap-1.5 rounded-full bg-tinta px-3.5 py-1.5 text-[0.8rem] font-semibold text-crema disabled:opacity-60"
                    >
                      {asignando === s.id ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />}
                      {t("tareas.asignar_a", { nombre: s.para.nombre })}
                    </button>
                    <button
                      onClick={() => setDescartadas((d) => ({ ...d, [s.id]: true }))}
                      title={t("tareas.descartar")}
                      className="grid h-7 w-7 place-items-center rounded-full border border-linea text-tinta-suave hover:text-tinta"
                    >
                      <X size={13} />
                    </button>
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* 2 · asignar a mano */}
        <form onSubmit={crear} className="rounded-[var(--radius-card)] border border-linea bg-superficie p-4">
          <h3 className="mb-2 font-display text-[0.95rem] font-bold">{t("tareas.crear_titulo")}</h3>
          <p className="mb-3 text-[0.82rem] leading-snug text-tinta-suave">{t("tareas.crear_sub")}</p>
          <input
            value={nueva.titulo}
            onChange={(e) => setNueva((n) => ({ ...n, titulo: e.target.value }))}
            placeholder={t("tareas.crear_ph")}
            className="mb-2 w-full rounded-xl border border-linea bg-papel px-3.5 py-2.5 text-[0.92rem] outline-none focus:border-tinta/40"
          />
          <div className="flex flex-wrap items-center gap-2">
            <select
              value={nueva.para}
              onChange={(e) => setNueva((n) => ({ ...n, para: e.target.value }))}
              className="min-h-11 flex-1 rounded-xl border border-linea bg-papel px-3 py-2 text-[0.9rem] outline-none"
            >
              <option value="">{t("tareas.elegir_persona")}</option>
              {equipo.filter((p) => p.rol !== "Dueño").map((p) => (
                <option key={p.username} value={p.username}>{p.nombre} · {p.rol}</option>
              ))}
            </select>
            <button
              type="submit"
              disabled={creando || !nueva.titulo.trim() || !nueva.para}
              className="inline-flex min-h-11 items-center gap-1.5 rounded-xl bg-tinta px-4 text-[0.86rem] font-semibold text-crema disabled:opacity-50"
            >
              <Plus size={15} /> {t("tareas.asignar")}
            </button>
          </div>
        </form>

        {/* 3 · quién tiene qué */}
        <div className="rounded-[var(--radius-card)] border border-linea bg-superficie p-4">
          <h3 className="mb-2 flex items-center gap-2 font-display text-[0.95rem] font-bold">
            {t("tareas.quien_tiene")}
            {panorama && (
              <span className="text-[0.78rem] font-normal text-tinta-suave">
                {t("tareas.resumen", { abiertas: panorama.abiertas, hechas: panorama.hechas })}
              </span>
            )}
          </h3>
          {!panorama || panorama.personas.length === 0 ? (
            <p className="text-[0.84rem] text-tinta-suave">{t("tareas.nadie_todavia")}</p>
          ) : (
            <ul className="space-y-2">
              {panorama.personas.map((g) => (
                <li key={g.username} className="flex items-start gap-2.5">
                  <Avatar persona={g} size={28} />
                  <div className="min-w-0 flex-1">
                    <p className="text-[0.88rem] font-semibold leading-tight">
                      {g.nombre}
                      <span className="ml-1.5 font-normal text-tinta-suave">
                        {g.abiertas > 0
                          ? t("tareas.abiertas_n", { n: g.abiertas })
                          : t("tareas.al_dia")}
                      </span>
                    </p>
                    {g.titulos.slice(0, 2).map((x, i) => (
                      <p key={i} className="truncate text-[0.78rem] text-tinta-suave">· {x}</p>
                    ))}
                    {g.hechas > 0 && (
                      <p className="mt-0.5 inline-flex items-center gap-1 text-[0.76rem] text-salvia">
                        <CheckCircle2 size={11} /> {t("tareas.hechas_n", { n: g.hechas })}
                      </p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
