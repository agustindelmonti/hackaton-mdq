import { useCallback, useEffect, useRef, useState } from "react";
import { FileText, Check, XCircle } from "lucide-react";
import { useAui, useAuiState } from "@assistant-ui/react";
import AngelaMark from "../components/AngelaMark";
import FacturaFlow from "../components/FacturaFlow";
import { AngelaThread, CameraComposerButton } from "../components/assistant/angela-thread";
import { ChatToolbar } from "../components/assistant/chat-toolbar";
import { api } from "../lib/api";
import { angelaBus } from "../lib/angelaBus";
import { authStore } from "../lib/auth";
import { equipoStore } from "../lib/equipoStore";
import { vistaStore } from "../lib/vistaStore";
import { setAngelaOnDone, setAngelaRunContext } from "../lib/assistant/run-context";
import { useT } from "../lib/i18n";

// Chips default: chipsAngelaDe(user) desde desktop/mobile.
export default function AngelaView({
  saludoInicial,
  onNavigate,
  placeholderChips,
  inputInicial,
  user,
  onDatosCambiaron,
  variant = "compact",
  toolbarTrailing = null,
}) {
  const t = useT();
  const aui = useAui();
  const threadEmpty = useAuiState((s) => s.thread.isEmpty);
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const fullscreen = variant === "fullscreen";
  const [modo, setModo] = useState(null);
  const [fotoAbierta, setFotoAbierta] = useState(false);
  const ultimaConsulta = useRef(null);

  useEffect(() => {
    setAngelaRunContext({
      token: authStore.getSnapshot()?.token ?? null,
      rol: user?.rol,
      nombre: user?.username,
    });
  }, [user]);

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

  const chips = (placeholderChips || []).map((c) =>
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
    <div className="flex h-full min-h-0 flex-col">
      <ChatToolbar
        compact={!fullscreen}
        className={fullscreen ? "shrink-0 border-b border-linea px-3 py-2.5" : "shrink-0 pb-2"}
        trailing={toolbarTrailing}
      />

      {!threadEmpty && !fullscreen && (
        <header className="flex items-center gap-3 pb-2 pt-0.5">
          <AngelaMark size={36} estado={isRunning ? "pensando" : "idle"} />
          <p className="flex items-center gap-1.5 text-[0.76rem] text-tinta-suave">
            <span className="inline-block h-1.5 w-1.5 rounded-full bg-salvia" />
            {modo === "simulado" ? t("angela.modo_datos") : t("angela.socia")}
          </p>
        </header>
      )}

      <div className="min-h-0 flex-1 overflow-hidden">
        <AngelaThread
          variant={variant}
          placeholder={t("angela.ph_input")}
          emptyTitle={fullscreen ? t("angela.titulo") : undefined}
          emptyDetail={saludoInicial}
          suggestions={chips}
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
