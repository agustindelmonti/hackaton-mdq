import { useSyncExternalStore } from "react";
import { CloudOff, CloudUpload, RefreshCw, TriangleAlert, Check } from "lucide-react";
import { estadoConexion, sincronizar } from "../lib/offline";
import { api } from "../lib/api";
import { useT } from "../lib/i18n";

// ============================================================================
// EL CHIP DE CONEXIÓN — decir la verdad sobre dónde está cada cosa.
// ----------------------------------------------------------------------------
// Cuando no hay señal, lo peor que puede hacer una app es disimularlo. El
// operario tiene que saber tres cosas de un vistazo: si hay red, cuántos
// movimientos suyos todavía no llegaron al sistema, y si alguno quedó trabado.
//
// Por eso el chip no es decorativo y no desaparece cuando vuelve la conexión
// si todavía queda algo por mandar: se queda hasta que la cola está vacía.
// ============================================================================

// La función que sabe hablar con la API. Vive acá y no adentro de lib/offline
// para que ese módulo no dependa de los endpoints.
export const enviarPendiente = (item) => {
  if (item.tipo_cola === "movimiento") return api.movimientoRegistrar(item.payload);
  if (item.tipo_cola === "confirmacion") return api.movimientoConfirmar(item.payload.numero);
  return Promise.reject(new Error("tipo de item desconocido en la cola"));
};

export default function EstadoConexion({ compacto = false }) {
  const t = useT();
  const e = useSyncExternalStore(estadoConexion.subscribe, estadoConexion.getSnapshot);
  const { online, pendientes, conflictos, sincronizando } = e;

  // Con red y sin nada pendiente no hay nada que decir: el chip se calla.
  if (online && !pendientes && !conflictos && !sincronizando) return null;

  const tono = !online
    ? "border-oro/40 bg-oro/[0.08] text-oro"
    : conflictos
    ? "border-rojo/35 bg-rojo/[0.06] text-rojo"
    : "border-hielo/35 bg-hielo/[0.06] text-hielo";

  const Icono = !online ? CloudOff : conflictos ? TriangleAlert
    : sincronizando ? RefreshCw : CloudUpload;

  return (
    <div className={`flex flex-wrap items-center gap-2 rounded-lg border px-3 py-2 text-[0.83rem] ${tono}`}>
      <Icono size={15} className={`shrink-0 ${sincronizando ? "animate-spin" : ""}`} />
      <span className="min-w-0 flex-1">
        {!online
          ? (pendientes
              ? t("off.sin_red_con_cola", { n: pendientes })
              : t("off.sin_red"))
          : conflictos
          ? t("off.conflictos", { n: conflictos })
          : sincronizando
          ? t("off.sincronizando")
          : t("off.por_sincronizar", { n: pendientes })}
      </span>
      {online && pendientes > 0 && !sincronizando && (
        <button
          type="button"
          onClick={() => sincronizar(enviarPendiente)}
          className="shrink-0 rounded border border-current px-2 py-0.5 text-[0.78rem] font-medium"
        >
          {t("off.sincronizar_ya")}
        </button>
      )}
      {!compacto && !online && (
        <span className="w-full text-[0.75rem] opacity-80">{t("off.tranquilo")}</span>
      )}
    </div>
  );
}

/** La lista de lo que todavía no llegó al sistema. Va en la vista del operario. */
export function ColaPendiente({ items, onReintentar }) {
  const t = useT();
  if (!items?.length) return null;
  return (
    <ul className="divide-y divide-linea overflow-hidden rounded-lg border border-linea bg-crema/50">
      {items.map((it) => (
        <li key={it.id} className="flex flex-wrap items-center gap-2 px-3 py-2 text-[0.83rem]">
          {it.estado === "conflicto"
            ? <TriangleAlert size={14} className="shrink-0 text-rojo" />
            : <CloudUpload size={14} className="shrink-0 text-oro" />}
          <span className="min-w-0 flex-1">
            {it.resumen || t("off.item_generico")}
          </span>
          <span className={`shrink-0 text-[0.75rem] ${it.estado === "conflicto" ? "text-rojo" : "text-tinta-suave"}`}>
            {it.estado === "conflicto" ? t("off.trabado") : t("off.pendiente")}
          </span>
          {it.estado === "conflicto" && (
            <button
              type="button"
              onClick={() => onReintentar?.(it)}
              className="shrink-0 rounded border border-linea px-2 py-0.5 text-[0.75rem]"
            >
              {t("off.revisar")}
            </button>
          )}
        </li>
      ))}
    </ul>
  );
}
