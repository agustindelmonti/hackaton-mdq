import { useEffect, useState } from "react";
import { BrainIcon, CheckIcon, XIcon } from "lucide-react";
import { api } from "../../lib/api";
import { cn } from "../../lib/cn";
import { useT } from "../../lib/i18n";
import { field, ghostButton, mono } from "./surfaces";

// "Lo que recuerdo de vos, escrito en este turno" — la tarjeta que aparece
// debajo de una respuesta de Ángela cuando guardó (o ya sabía) algo que la
// persona dijo. El color no es decoración: violeta = Ángela lo escribió ahora
// (mismo significado que en el resto del producto — "acciones del agente");
// ámbar = lo propuso sola de algo mencionado al pasar y todavía espera que
// alguien la confirme (CLAUDE: nada queda como verdad sin un toque humano);
// gris = ya lo sabía, no cambió nada.
const ESTILO_CAMBIO = {
  added: "bg-violeta-suave text-violeta",
  updated: "bg-violeta-suave text-violeta",
  dudoso: "bg-oro/12 text-oro-tinta",
};

export function MemoryChips({ chips, onForget, onConfirm, className, ...props }) {
  const t = useT();
  if (!chips?.length) return null;
  const nuevos = chips.filter((c) => c.cambio !== "existing").length;

  return (
    <div
      data-slot="memory-chips"
      className={cn("flex w-full max-w-sm flex-col gap-2", className)}
      {...props}
    >
      <div className="flex items-center gap-1.5">
        <BrainIcon className="size-3.5 text-tinta-suave/50" />
        <span className={cn(mono, "text-tinta-suave/70")}>
          {nuevos > 0 ? t("memoria.recorde", { n: nuevos }) : t("memoria.titulo")}
        </span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {chips.map((chip) => (
          <span
            key={chip.id}
            className={cn(
              "flex items-center gap-1 rounded-full py-1 pr-1 pl-2.5 text-xs transition-colors duration-150",
              ESTILO_CAMBIO[chip.cambio] ?? cn(field, "text-tinta-suave"),
            )}
          >
            {chip.texto}
            {chip.cambio === "dudoso" && onConfirm && (
              <button
                type="button"
                aria-label={t("memoria.confirmar_title", { texto: chip.texto })}
                onClick={() => onConfirm(chip.id)}
                className={cn(ghostButton, "size-4")}
              >
                <CheckIcon className="size-2.5" />
              </button>
            )}
            <button
              type="button"
              aria-label={t("memoria.olvidar_title", { texto: chip.texto })}
              onClick={() => onForget?.(chip.id)}
              className={cn(ghostButton, "size-4")}
            >
              <XIcon className="size-2.5" />
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}

// Adaptador para assistant-ui: una tool-call de 'recordar_hecho' (LLM real o
// el atajo determinístico de "acordate que...") se pinta como UN chip propio,
// no como el disclosure genérico request/result de las demás tools — acá lo
// que importa es el HECHO, no el JSON de la llamada.
function chipDe(result) {
  const hecho = result?.hecho;
  if (!hecho) return null;
  const cambio = result.cambio === "existing" ? "existing"
    : hecho.confianza === "dudoso" ? "dudoso" : (result.cambio || "added");
  return { id: hecho.id, texto: hecho.texto, cambio };
}

export function MemoryChipsToolUI({ result }) {
  const [chip, setChip] = useState(() => chipDe(result));
  const [borrado, setBorrado] = useState(false);

  useEffect(() => {
    if (result) setChip(chipDe(result));
  }, [result]);

  if (!chip || borrado) return null;

  const confirmar = async (id) => {
    try {
      await api.hechoConfirmar(id);
      setChip((c) => (c ? { ...c, cambio: "added" } : c));
    } catch { /* si falla la red queda dudoso — se puede reintentar */ }
  };

  const olvidar = async (id) => {
    try {
      await api.hechoBorrar(id);
      setBorrado(true);
    } catch { /* si falla la red el chip queda como estaba */ }
  };

  return <MemoryChips chips={[chip]} onForget={olvidar} onConfirm={confirmar} />;
}
