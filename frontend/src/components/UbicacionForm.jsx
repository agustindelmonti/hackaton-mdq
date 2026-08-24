import { useState } from "react";
import { Snowflake, Warehouse, Sprout, FlaskConical, Factory, MapPin, X, Check, Loader2 } from "lucide-react";
import { api } from "../lib/api";
import { toast } from "../lib/toastStore";
import { useT } from "../lib/i18n";

// Alta/edición de un nodo del mapa de operación (N02). Un solo formulario para
// las dos vistas que lo usan (Ubicaciones.jsx y MapaOperacion.jsx): crear y
// editar comparten los mismos campos, sólo cambia si `inicial` viene poblado.
//
// El "tipo" hace doble función: además de agrupar la ubicación en las reglas
// de negocio (galpón = sin frío), ES el selector de ícono — elegir un tipo acá
// es lo que se ve reflejado en el ícono en TODAS las vistas (mismo mapa ICONO
// que ya usan Ubicaciones.jsx y MapaOperacion.jsx).
export const TIPOS_UBICACION = [
  { id: "frigorifico", icono: Snowflake },
  { id: "galpon", icono: Warehouse },
  { id: "campo", icono: Sprout },
  { id: "laboratorio", icono: FlaskConical },
  { id: "planta", icono: Factory },
  { id: "otro", icono: MapPin },
];

export default function UbicacionForm({ inicial, onCerrar, onGuardado }) {
  const t = useT();
  const editando = Boolean(inicial?.id);
  const [nombre, setNombre] = useState(inicial?.nombre || "");
  const [tipo, setTipo] = useState(inicial?.tipo || "frigorifico");
  const [capacidad, setCapacidad] = useState(inicial?.capacidad_kg ?? "");
  const [tempObjetivo, setTempObjetivo] = useState(inicial?.temp_objetivo ?? "");
  const [tempTolerancia, setTempTolerancia] = useState(inicial?.temp_tolerancia ?? "");
  const [direccion, setDireccion] = useState(inicial?.direccion || "");
  const [camaras, setCamaras] = useState((inicial?.camaras || []).join(", "));
  const [enviando, setEnviando] = useState(false);

  const guardar = async () => {
    if (!nombre.trim()) { toast(t("ubi.nombre_requerido"), "error"); return; }
    setEnviando(true);
    const datos = {
      nombre: nombre.trim(),
      tipo,
      capacidad_kg: capacidad === "" ? null : Number(capacidad),
      temp_objetivo: tempObjetivo === "" ? null : Number(tempObjetivo),
      temp_tolerancia: tempTolerancia === "" ? null : Number(tempTolerancia),
      direccion: direccion.trim() || null,
      camaras: camaras.split(",").map((c) => c.trim()).filter(Boolean),
    };
    try {
      const guardada = editando
        ? await api.ubicacionEditar(inicial.id, datos)
        : await api.ubicacionCrear(datos);
      toast(t(editando ? "ubi.editar_ok" : "ubi.crear_ok"));
      onGuardado?.(guardada);
      onCerrar();
    } catch {
      toast(t("ubi.error_generico"), "error");
    }
    setEnviando(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-tinta/40 p-0 sm:items-center sm:p-4"
      onClick={onCerrar}>
      <div onClick={(e) => e.stopPropagation()}
        className="max-h-[88vh] w-full max-w-md overflow-y-auto rounded-t-[var(--radius-card)] border border-linea bg-crema p-5 pb-[max(1.25rem,env(safe-area-inset-bottom))] sombra-alta sm:rounded-[var(--radius-card)]">
        <div className="flex items-start justify-between gap-3">
          <h2 className="font-display text-[1.1rem] font-bold leading-tight">
            {t(editando ? "ubi.form_titulo_editar" : "ubi.form_titulo_crear")}
          </h2>
          <button onClick={onCerrar} className="text-tinta-suave hover:text-tinta"><X size={20} /></button>
        </div>

        <div className="mt-4 space-y-3">
          <div>
            <label className="mb-1 block text-[0.76rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {t("ubi.f_nombre")}<span className="ml-1 text-rojo">*</span>
            </label>
            <input value={nombre} onChange={(e) => setNombre(e.target.value)}
              className="min-h-11 w-full rounded-xl border border-linea bg-papel px-3.5 py-2.5 text-[0.92rem] outline-none focus:border-tinta/40" />
          </div>

          <div>
            <label className="mb-1 block text-[0.76rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {t("ubi.f_tipo")}
            </label>
            <div className="flex flex-wrap gap-1.5">
              {TIPOS_UBICACION.map(({ id, icono: Icono }) => (
                <button key={id} type="button" onClick={() => setTipo(id)}
                  className={`flex min-h-9 items-center gap-1.5 rounded-full border px-3 py-1.5 text-[0.82rem] font-semibold transition-colors ${
                    tipo === id ? "border-tinta bg-tinta text-crema" : "border-linea text-tinta-suave"}`}>
                  <Icono size={14} /> {t(`ubi.tipo_${id}`)}
                </button>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-[0.76rem] font-semibold uppercase tracking-wide text-tinta-suave">
                {t("ubi.f_capacidad")}
              </label>
              <input type="number" inputMode="decimal" value={capacidad}
                onChange={(e) => setCapacidad(e.target.value)}
                className="min-h-11 w-full rounded-xl border border-linea bg-papel px-3.5 py-2.5 text-[0.92rem] outline-none focus:border-tinta/40" />
            </div>
            <div>
              <label className="mb-1 block text-[0.76rem] font-semibold uppercase tracking-wide text-tinta-suave">
                {t("ubi.f_temp_objetivo")}
              </label>
              <input type="number" inputMode="decimal" value={tempObjetivo}
                onChange={(e) => setTempObjetivo(e.target.value)}
                className="min-h-11 w-full rounded-xl border border-linea bg-papel px-3.5 py-2.5 text-[0.92rem] outline-none focus:border-tinta/40" />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-[0.76rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {t("ubi.f_temp_tolerancia")}
            </label>
            <input type="number" inputMode="decimal" value={tempTolerancia}
              onChange={(e) => setTempTolerancia(e.target.value)}
              className="min-h-11 w-full rounded-xl border border-linea bg-papel px-3.5 py-2.5 text-[0.92rem] outline-none focus:border-tinta/40" />
          </div>

          <div>
            <label className="mb-1 block text-[0.76rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {t("ubi.f_direccion")}
            </label>
            <input value={direccion} onChange={(e) => setDireccion(e.target.value)}
              className="min-h-11 w-full rounded-xl border border-linea bg-papel px-3.5 py-2.5 text-[0.92rem] outline-none focus:border-tinta/40" />
          </div>

          <div>
            <label className="mb-1 block text-[0.76rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {t("ubi.f_camaras")}
            </label>
            <input value={camaras} onChange={(e) => setCamaras(e.target.value)}
              className="min-h-11 w-full rounded-xl border border-linea bg-papel px-3.5 py-2.5 text-[0.92rem] outline-none focus:border-tinta/40" />
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2">
          <button onClick={guardar} disabled={enviando}
            className="inline-flex min-h-11 items-center gap-1.5 rounded-full bg-tinta px-4 py-2.5 text-[0.88rem] font-semibold text-crema active:scale-95 disabled:opacity-40">
            {enviando ? <Loader2 size={15} className="animate-spin" /> : <Check size={15} />}
            {t(editando ? "ubi.guardar" : "ubi.crear_btn")}
          </button>
          <button onClick={onCerrar}
            className="min-h-11 rounded-full border border-linea px-4 py-2.5 text-[0.88rem] font-semibold text-tinta-suave">
            {t("ubi.cancelar")}
          </button>
        </div>
      </div>
    </div>
  );
}
