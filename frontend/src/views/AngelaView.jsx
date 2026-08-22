import { useCallback, useEffect, useRef, useState } from "react";
import { FileText, Paperclip, ChevronRight, Check, XCircle } from "lucide-react";
import { useAui, useAuiState } from "@assistant-ui/react";
import AngelaMark from "../components/AngelaMark";
import FacturaFlow from "../components/FacturaFlow";
import { textoFeed } from "../components/ActividadFeed";
import { AngelaThread, CameraComposerButton } from "../components/assistant/angela-thread";
import { fecha } from "../lib/format";
import { api } from "../lib/api";
import { angelaBus } from "../lib/angelaBus";
import { authStore } from "../lib/auth";
import { equipoStore } from "../lib/equipoStore";
import { vistaStore } from "../lib/vistaStore";
import { setAngelaOnDone, setAngelaRunContext } from "../lib/assistant/run-context";
import { useT } from "../lib/i18n";

// Chips: `lk` es lo que se MUESTRA y `enviarLk` la clave del payload que va al
// backend. El catálogo de roles es la única fuente y el texto sale del diccionario.
const CHIPS = [
  { lk: "rol.chip_panorama", enviarLk: "rol.chip_panorama" },
  { lk: "rol.chip_que_esta_trabado", enviarLk: "rol.chip_que_esta_trabado" },
  { lk: "rol.chip_dif_abiertas", enviarLk: "rol.chip_dif_abiertas" },
  { lk: "rol.chip_plata_parada", enviarLk: "rol.chip_plata_parada" },
];

// Chat de Ángela con assistant-ui (thread, tool-call disclosure, voz es-AR).
export default function AngelaView({
  saludoInicial,
  onNavigate,
  placeholderChips = CHIPS,
  inputInicial,
  user,
  onDatosCambiaron,
}) {
  const t = useT();
  const aui = useAui();
  const threadEmpty = useAuiState((s) => s.thread.isEmpty);
  const [modo, setModo] = useState(null);
  const [fotoAbierta, setFotoAbierta] = useState(false);
  const [feed, setFeed] = useState([]);
  const ultimaConsulta = useRef(null);

  useEffect(() => {
    setAngelaRunContext({
      token: authStore.getSnapshot()?.token ?? null,
      rol: user?.rol,
      nombre: user?.username,
    });
  }, [user]);

  useEffect(() => {
    api.actividad().then((a) => setFeed((a.feed || []).slice(0, 3))).catch(() => {});
  }, []);

  const aplicarAcciones = useCallback((acciones = []) => {
    if (!acciones.length) return;
    equipoStore.aplicarAcciones(acciones);
    for (const a of acciones) {
      if (a.type === "modify_view" && a.cambios) vistaStore.aplicar(a.cambios);
      if (a.type === "create_widget" && a.widget) vistaStore.agregarWidget(a.section, a.widget);
      if (a.type === "crear_pestana" && a.pestana) vistaStore.agregarPestana(a.pestana);
      if (a.type === "preferencia" && a.vista) vistaStore.hidratarServer({ vista: a.vista });
      if (a.type === "orden_home") vistaStore.aplicar({ ordenHome: a.orden });
    }
    if (acciones.some((a) => a.type === "saneado")) onDatosCambiaron?.();
    const nav = [...acciones].reverse().find((a) => a.type === "navigate");
    if (nav && onNavigate) onNavigate(nav.section, nav.highlight);
  }, [onNavigate, onDatosCambiaron]);

  useEffect(() => {
    setAngelaOnDone((result) => {
      setModo(result.modo);
      aplicarAcciones(result.acciones);
      if ((result.acciones || []).some((a) => a.type === "plan_progreso")) {
        onDatosCambiaron?.();
      }
    });
    return () => setAngelaOnDone(null);
  }, [aplicarAcciones, onDatosCambiaron]);

  useEffect(() => {
    const alTranscript = (p) => {
      aui.thread.append({
        role: "assistant",
        content: [{ type: "text", text: p.content }],
      });
    };
    angelaBus.drain().forEach(alTranscript);
    return angelaBus.subscribe(alTranscript);
  }, [aui]);

  useEffect(() => {
    if (inputInicial && inputInicial !== ultimaConsulta.current) {
      ultimaConsulta.current = inputInicial;
      aui.thread.append(inputInicial);
    }
  }, [inputInicial, aui]);

  const chips = placeholderChips.map((c) =>
    typeof c === "string"
      ? { enviar: c, label: c }
      : {
          enviar: c.enviar || t(c.enviarLk || c.lk),
          label: t(c.lk),
          lk: c.lk,
        },
  );

  const enviarOpcion = (texto) => aui.thread.append(texto);

  const renderExtras = (meta) => {
    if (!meta) return null;
    return (
      <>
        {meta.plan && <PlanChecklist plan={meta.plan} />}
        {meta.documento && <DocCard documento={meta.documento} t={t} />}
      </>
    );
  };

  return (
    <div className="flex h-full flex-col">
      <header className="flex items-center gap-3 pb-3 pt-1">
        <AngelaMark size={40} />
        <div>
          <h1 className="font-display text-xl font-bold leading-none">Ángela</h1>
          <p className="mt-0.5 flex items-center gap-1.5 text-[0.78rem] text-tinta-suave">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-salvia" />
            {modo === "simulado" ? t("angela.modo_datos") : t("angela.socia")}
          </p>
        </div>
      </header>

      {threadEmpty && feed.length > 0 && (
        <div className="mb-3 space-y-1.5">
          <p className="text-[0.68rem] font-semibold uppercase tracking-[0.14em] text-tinta-suave">
            {t("angela.ultimo")}
          </p>
          {feed.map((e, i) => (
            <div key={i} className="flex items-start gap-2.5 rounded-xl border border-linea bg-crema px-3 py-2 sombra-papel">
              <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${e.tipo === "staging" ? "bg-salvia" : "bg-oro"}`} />
              <span className="min-w-0 flex-1 text-[0.8rem] leading-snug text-tinta">{textoFeed(e, t)}</span>
              <span className="shrink-0 text-[0.7rem] text-tinta-suave">{fecha(e.cuando)}</span>
            </div>
          ))}
        </div>
      )}

      {threadEmpty && (
        <div className="mb-3 space-y-1.5">
          {authStore.tiene("cargar") && (
            <button
              type="button"
              onClick={() => setFotoAbierta(true)}
              className="flex w-full items-center gap-3 rounded-xl border border-linea bg-crema px-3 py-2.5 text-left sombra-papel transition-colors hover:border-violeta/40"
            >
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-violeta-suave text-violeta">
                <Paperclip size={16} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[0.85rem] font-semibold leading-tight">{t("angela.accion_foto")}</span>
                <span className="block text-[0.74rem] text-tinta-suave">{t("angela.accion_foto_sub")}</span>
              </span>
              <ChevronRight size={15} className="text-tinta-suave" />
            </button>
          )}
          {onNavigate && authStore.tiene("documentos") && (
            <button
              type="button"
              onClick={() => onNavigate("documentos")}
              className="flex w-full items-center gap-3 rounded-xl border border-linea bg-crema px-3 py-2.5 text-left sombra-papel transition-colors hover:border-violeta/40"
            >
              <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-violeta-suave text-violeta">
                <FileText size={16} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[0.85rem] font-semibold leading-tight">{t("angela.accion_doc")}</span>
                <span className="block text-[0.74rem] text-tinta-suave">{t("angela.accion_doc_sub")}</span>
              </span>
              <ChevronRight size={15} className="text-tinta-suave" />
            </button>
          )}
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-hidden">
        <AngelaThread
          placeholder={t("angela.ph_input")}
          suggestions={chips}
          emptyTitle={saludoInicial || t("angela.saludo_default")}
          emptyDetail={t("angela.socia")}
          onOpcion={enviarOpcion}
          renderExtras={renderExtras}
          extraComposer={
            authStore.tiene("cargar") ? (
              <CameraComposerButton onClick={() => setFotoAbierta(true)} title={t("foto.titulo")} />
            ) : null
          }
        />
      </div>

      {fotoAbierta && (
        <FacturaFlow
          onCerrar={() => setFotoAbierta(false)}
          onCargado={() => onDatosCambiaron?.()}
          onPreguntar={(texto) => { setFotoAbierta(false); enviarOpcion(texto); }}
        />
      )}
    </div>
  );
}

function DocCard({ documento, t }) {
  const [estado, setEstado] = useState("generando");
  const blobRef = useRef(null);
  useEffect(() => {
    let vivo = true;
    api.documentoPdf(documento)
      .then((b) => { if (vivo) { blobRef.current = b; setEstado("listo"); } })
      .catch(() => { if (vivo) setEstado("error"); });
    return () => { vivo = false; };
  }, [documento]);
  const bajar = () => {
    if (!blobRef.current) return;
    const url = URL.createObjectURL(blobRef.current);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${documento.tipo || "documento"}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="mt-2.5 flex items-center gap-3 rounded-xl border border-linea bg-papel px-3 py-2.5">
      <FileText size={18} className="shrink-0 text-violeta" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-[0.88rem] font-semibold text-tinta">{documento.titulo}</p>
        <p className="text-[0.74rem] text-tinta-suave">{documento.subtitulo || documento.fecha || ""}</p>
      </div>
      {estado === "generando" && (
        <span className="shrink-0 text-[0.78rem] text-tinta-suave">{t("angela.doc_generando")}</span>
      )}
      {estado === "listo" && (
        <button type="button" onClick={bajar}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-full bg-violeta px-3.5 py-1.5 text-[0.8rem] font-semibold text-crema">
          {t("angela.doc_descargar")}
        </button>
      )}
      {estado === "error" && (
        <span className="shrink-0 text-[0.78rem] font-semibold text-rojo">{t("angela.doc_error")}</span>
      )}
    </div>
  );
}

function PlanChecklist({ plan }) {
  const [visibles, setVisibles] = useState(0);
  const pasos = plan.pasos || [];
  useEffect(() => {
    let k = 0;
    const id = setInterval(() => {
      k += 1;
      setVisibles(k);
      if (k >= pasos.length) clearInterval(id);
    }, 550);
    return () => clearInterval(id);
  }, [pasos.length]);
  return (
    <div className="mt-2.5 space-y-1.5 border-t border-linea/70 pt-2.5">
      {pasos.slice(0, visibles).map((p, i) => (
        <div key={i} className="flex items-start gap-2 text-[0.88rem]">
          {p.ok ? (
            <Check size={15} className="mt-0.5 shrink-0 text-salvia" />
          ) : (
            <XCircle size={15} className="mt-0.5 shrink-0 text-rojo" />
          )}
          <span className={p.ok ? "text-tinta" : "text-rojo-hondo"}>
            {p.titulo}
            {p.detalle && <span className="text-tinta-suave"> — {p.detalle}</span>}
            {p.error && <span className="text-rojo-hondo"> — {p.error}</span>}
          </span>
        </div>
      ))}
      {visibles < pasos.length && (
        <p className="text-[0.78rem] font-semibold text-tinta-suave">
          {visibles}/{pasos.length}…
        </p>
      )}
    </div>
  );
}
