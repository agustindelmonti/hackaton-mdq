import { useEffect, useState } from "react";
import {
  Ship, FileText, Check, TriangleAlert, Lock, Download, ChevronRight,
  BadgeCheck, Link2,
} from "lucide-react";
import AngelaSays from "../components/AngelaSays";
import { api } from "../lib/api";
import { generarPdfDocumento } from "../lib/pdfDocumento";
import { useEmpresa } from "../lib/useEmpresa";
import { toast } from "../lib/toastStore";
import { num, fecha } from "../lib/format";
import { useT } from "../lib/i18n";

// ============================================================================
// N03 · EL COPILOTO DE LA CARPETA DE EXPORTACIÓN.
// ----------------------------------------------------------------------------
// «El sistema lee los requisitos documentales y los cruza con los datos de
//  trazabilidad de un lote específico para pre-completar lo que ya se sabe.»
//
// La decisión de diseño que sostiene toda la pantalla: CADA CAMPO MUESTRA DE
// DÓNDE SALIÓ. No "generado por el sistema" — «lote PS-202425-SPU-015»,
// «análisis del 14/03/2026», «cliente Southern Foods». Un documento que va a
// un organismo de control no puede tener campos de origen desconocido, y el
// valor del copiloto no es que escriba rápido: es que se pueda auditar.
//
// Lo segundo: el CONTROL CRUZADO. Que los kilos y los bultos digan lo mismo en
// la factura, el packing list y la solicitud del INASE es trivial cuando los
// tres salen de la misma fuente — y es la causa número uno de demora en aduana
// cuando cada uno se tipea aparte.
// ============================================================================

const ESTADO_CAMPO = {
  completo: { punto: "bg-salvia", texto: "text-tinta" },
  falta: { punto: "bg-rojo", texto: "text-rojo" },
  opcional: { punto: "bg-linea", texto: "text-tinta-suave" },
};

export default function Exportacion({ onPreguntar }) {
  const t = useT();
  const [lista, setLista] = useState(null);
  const [carpeta, setCarpeta] = useState(null);
  const [doc, setDoc] = useState(null);
  const [cargandoDoc, setCargandoDoc] = useState(false);

  useEffect(() => {
    api.exportacion().then((d) => {
      setLista(d);
      const primero = d.embarques?.[0];
      if (primero) api.exportacionCarpeta(primero.numero).then(setCarpeta).catch(() => {});
    }).catch(() => setLista(false));
  }, []);

  const abrir = async (docId) => {
    if (!carpeta) return;
    setCargandoDoc(true);
    try {
      setDoc(await api.exportacionDocumento(carpeta.orden, docId));
    } catch { /* el detalle del error ya lo muestra el cliente de API */ }
    finally { setCargandoDoc(false); }
  };

  if (lista === null) return <Esqueleto />;
  if (lista === false) return <p className="text-tinta-suave">{t("exp.error")}</p>;
  if (!lista.embarques?.length) {
    return (
      <div className="space-y-4">
        <Encabezado t={t} />
        <AngelaSays tone="ok">{t("exp.sin_embarques")}</AngelaSays>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Encabezado t={t} />

      {carpeta && (
        <>
          <Cabecera carpeta={carpeta} onPreguntar={onPreguntar} t={t} />
          <div className="grid gap-5 lg:grid-cols-[20rem_1fr]">
            <ListaDocumentos
              carpeta={carpeta}
              activo={doc?.id}
              onAbrir={abrir}
              t={t}
            />
            <div className="min-w-0">
              {cargandoDoc && <div className="h-96 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />}
              {!cargandoDoc && doc && <Documento doc={doc} carpeta={carpeta} t={t} />}
              {!cargandoDoc && !doc && (
                <div className="flex h-64 items-center justify-center rounded-[var(--radius-card)] border border-dashed border-linea text-[0.9rem] text-tinta-suave">
                  {t("exp.elegi_documento")}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

const Encabezado = ({ t }) => (
  <header>
    <h1 className="font-display text-3xl font-bold">{t("exp.titulo")}</h1>
    <p className="mt-1 text-[0.95rem] text-tinta-suave">{t("exp.subtitulo")}</p>
  </header>
);

// --- el embarque, y si la orden lo deja salir -------------------------------
function Cabecera({ carpeta, onPreguntar, t }) {
  const cc = carpeta.control_cruzado || {};
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-start gap-3 rounded-[var(--radius-card)] border border-linea bg-superficie px-4 py-3 sombra-papel">
        <span className="mt-0.5 shrink-0 rounded-lg bg-hielo/10 p-2 text-hielo"><Ship size={18} /></span>
        <div className="min-w-0 flex-1">
          <h2 className="font-display text-[1.05rem] font-bold">{carpeta.cliente}</h2>
          <p className="mt-0.5 text-[0.82rem] text-tinta-suave">
            {carpeta.orden} · {carpeta.pais} · {carpeta.incoterm} ·{" "}
            {carpeta.puerto} → {carpeta.destino_puerto}
          </p>
        </div>
        <div className="shrink-0 text-right">
          <p className="plata text-lg font-medium">{num(carpeta.kg_total)} kg</p>
          <p className="text-[0.72rem] text-tinta-suave">
            {carpeta.bultos} {t("exp.bultos")} · {carpeta.lotes.join(", ")}
          </p>
        </div>
      </div>

      {/* El embarque no sale si la orden de carga está frenada, por más que la
          carpeta esté completa. Decirlo acá evita la sorpresa en el puerto. */}
      {carpeta.orden_bloqueada && (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-rojo/30 bg-rojo/[0.05] px-3 py-2.5">
          <Lock size={15} className="shrink-0 text-rojo" />
          <span className="min-w-0 flex-1 text-[0.87rem]">{t("exp.orden_bloqueada")}</span>
          <button
            type="button"
            onClick={() => onPreguntar?.(t("exp.pregunta_bloqueo", { n: carpeta.orden }))}
            className="shrink-0 text-[0.83rem] font-medium text-rojo underline underline-offset-2"
          >
            {t("exp.ver_motivo")}
          </button>
        </div>
      )}

      {/* EL CONTROL CRUZADO: lo que ningún formulario chequea solo. */}
      <div className={`rounded-lg border px-3 py-2.5 ${cc.ok ? "border-salvia/30 bg-salvia/[0.05]" : "border-rojo/30 bg-rojo/[0.05]"}`}>
        <p className="flex items-center gap-2 text-[0.87rem] font-medium">
          <Link2 size={15} className={cc.ok ? "text-salvia" : "text-rojo"} />
          {cc.ok ? t("exp.cruzado_ok") : t("exp.cruzado_mal")}
        </p>
        <ul className="mt-1.5 grid gap-x-6 gap-y-0.5 text-[0.8rem] text-tinta-suave sm:grid-cols-2">
          {(cc.checks || []).map((c, i) => (
            <li key={i} className="flex items-center gap-1.5">
              {c.ok ? <Check size={12} className="shrink-0 text-salvia" />
                    : <TriangleAlert size={12} className="shrink-0 text-rojo" />}
              <span className="truncate">{c.que}</span>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}

// --- los seis papeles, con cuánto le falta a cada uno ------------------------
function ListaDocumentos({ carpeta, activo, onAbrir, t }) {
  return (
    <aside className="space-y-2">
      <div className="flex items-baseline justify-between">
        <h2 className="font-display text-lg font-bold">{t("exp.la_carpeta")}</h2>
        <span className="text-[0.8rem] text-tinta-suave">
          {t("exp.listos", { n: carpeta.listos, total: carpeta.total_documentos })}
        </span>
      </div>
      <ul className="space-y-1.5">
        {carpeta.documentos.map((d) => {
          const c = d.completitud;
          const listo = c.faltan === 0;
          return (
            <li key={d.id}>
              <button
                type="button"
                onClick={() => onAbrir(d.id)}
                className={`flex w-full items-center gap-2.5 rounded-lg border px-3 py-2.5 text-left transition
                  ${activo === d.id ? "border-hielo bg-hielo/[0.06]" : "border-linea hover:bg-crema"}`}
              >
                <span className={`shrink-0 rounded p-1.5 ${listo ? "bg-salvia/10 text-salvia" : "bg-oro/10 text-oro"}`}>
                  {listo ? <BadgeCheck size={15} /> : <FileText size={15} />}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-[0.88rem] font-medium">{d.titulo}</span>
                  <span className="block text-[0.75rem] text-tinta-suave">
                    {d.organismo} ·{" "}
                    {listo ? t("exp.completo") : t("exp.faltan", { n: c.faltan })}
                  </span>
                </span>
                <span className="shrink-0 text-[0.78rem] tabular-nums text-tinta-suave">{c.pct}%</span>
                <ChevronRight size={14} className="shrink-0 text-tinta-suave" />
              </button>
            </li>
          );
        })}
      </ul>
    </aside>
  );
}

// --- el documento, con la forma de un documento -----------------------------
function Documento({ doc, carpeta, t }) {
  const { empresa, logo } = useEmpresa();
  const [bajando, setBajando] = useState(false);
  const descargar = async () => {
    setBajando(true);
    try {
      await generarPdfDocumento({ doc, carpeta, empresa, logo, t });
    } catch {
      toast(t("exp.pdf_error"), "error");
    }
    setBajando(false);
  };

  return (
    <article className="overflow-hidden rounded-[var(--radius-card)] border border-linea bg-superficie sombra-papel">
      {/* EL MEMBRETE, IGUAL QUE EN EL PDF. Lo que se ve en pantalla y lo que
          sale impreso tienen que ser el mismo papel: si el dueño aprueba acá y
          después baja otra cosa, deja de confiar en los dos. */}
      <header className="border-b-2 border-[#1e2f6f] px-5 py-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            {logo ? (
              <img src={logo} alt={empresa || ""} className="h-10 w-auto" draggable="false" />
            ) : (
              <p className="font-display text-lg font-bold tracking-wide text-[#1e2f6f]">
                {(empresa || "Papasud S.A.").toUpperCase()}
              </p>
            )}
            <div className="text-[0.7rem] leading-tight text-tinta-suave">
              <p>CUIT 30-54187629-3 · RNCyFS N° 14.328</p>
              <p>Ruta 226 km 14,5 — Sierra de los Padres, Mar del Plata</p>
            </div>
          </div>
          <button
            type="button"
            onClick={descargar}
            disabled={bajando}
            className="flex shrink-0 items-center gap-1.5 rounded-lg border border-linea px-3 py-1.5 text-[0.83rem] transition hover:bg-crema disabled:opacity-60"
          >
            <Download size={14} /> {bajando ? t("exp.bajando") : t("exp.descargar")}
          </button>
        </div>
        <div className="mt-3 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="font-display text-xl font-bold">{doc.titulo}</h2>
          {doc.numero && (
            <span className="plata text-[0.9rem] font-medium">N° {doc.numero}</span>
          )}
        </div>
        {doc.subtitulo && (
          <p className="mt-0.5 text-[0.8rem] text-tinta-suave">{doc.subtitulo}</p>
        )}
      </header>

      <div className="space-y-5 px-5 py-4">
        {(doc.secciones || []).map((s) => (
          <section key={s.titulo}>
            <h3 className="mb-2 border-b border-linea pb-1 text-[0.72rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {s.titulo}
            </h3>
            <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
              {s.campos.map((c) => <Campo key={c.etiqueta} c={c} t={t} />)}
            </dl>
          </section>
        ))}

        {doc.items?.length > 0 && (
          <section>
            <h3 className="mb-2 border-b border-linea pb-1 text-[0.72rem] font-semibold uppercase tracking-wide text-tinta-suave">
              {t("exp.detalle")}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[30rem] text-[0.82rem]">
                <thead>
                  <tr className="border-b border-linea text-[0.68rem] uppercase tracking-wide text-tinta-suave">
                    {Object.keys(doc.items[0]).filter((k) => k !== "fuente").map((k) => (
                      <th key={k} className="px-2 py-1.5 text-left font-semibold">
                        {k.replace(/_/g, " ")}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {doc.items.map((it, i) => (
                    <tr key={i} className="border-b border-linea/60 last:border-0">
                      {Object.entries(it).filter(([k]) => k !== "fuente").map(([k, v]) => (
                        <td key={k} className="px-2 py-1.5 align-top">
                          {typeof v === "boolean" ? (v ? "Sí" : "No")
                            : typeof v === "number" ? num(v) : String(v ?? "—")}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {doc.totales?.length > 0 && (
          <section className="rounded-lg bg-crema/70 px-3 py-2.5">
            <dl className="grid gap-x-6 gap-y-1 sm:grid-cols-2">
              {doc.totales.map((c) => <Campo key={c.etiqueta} c={c} t={t} destacado />)}
            </dl>
          </section>
        )}

        {doc.pie?.length > 0 && (
          <section className="border-t border-linea pt-3">
            <dl className="grid gap-x-6 gap-y-2 sm:grid-cols-2">
              {doc.pie.map((c) => <Campo key={c.etiqueta} c={c} t={t} />)}
            </dl>
          </section>
        )}

        {doc.nota_legal && (
          <p className="border-t border-linea pt-3 text-[0.75rem] leading-snug text-tinta-suave">
            {doc.nota_legal}
          </p>
        )}
      </div>
    </article>
  );
}

// --- un campo, CON SU FUENTE ------------------------------------------------
function Campo({ c, t, destacado }) {
  const e = ESTADO_CAMPO[c.estado] || ESTADO_CAMPO.opcional;
  const valor = Array.isArray(c.valor) ? c.valor : c.valor == null ? null : [c.valor];
  return (
    <div className="min-w-0">
      <dt className="flex items-center gap-1.5 text-[0.72rem] text-tinta-suave">
        <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${e.punto}`} aria-hidden />
        {c.etiqueta}
      </dt>
      <dd className={`text-[0.88rem] ${destacado ? "font-medium" : ""} ${e.texto}`}>
        {valor
          ? (valor.length > 1
              ? <ul className="list-disc space-y-0.5 pl-4">
                  {valor.map((v, i) => <li key={i}>{String(v)}</li>)}
                </ul>
              : String(valor[0]))
          : <span className="italic">{c.obligatorio ? t("exp.falta") : "—"}</span>}
      </dd>
      {/* LA FUENTE: de dónde salió este dato. Es lo que hace auditable el papel. */}
      {c.fuente && (
        <p className="mt-0.5 text-[0.68rem] text-hielo">{t("exp.de")} {c.fuente}</p>
      )}
      {c.nota && <p className="mt-0.5 text-[0.68rem] italic text-tinta-suave">{c.nota}</p>}
    </div>
  );
}

function Esqueleto() {
  return (
    <div className="space-y-6" aria-busy="true">
      <div className="h-9 w-80 animate-pulse rounded bg-linea" />
      <div className="h-20 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
      <div className="grid gap-5 lg:grid-cols-[20rem_1fr]">
        <div className="h-80 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
        <div className="h-80 animate-pulse rounded-[var(--radius-card)] bg-linea/60" />
      </div>
    </div>
  );
}
