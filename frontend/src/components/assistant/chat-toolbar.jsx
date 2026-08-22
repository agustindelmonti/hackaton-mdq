import { useMemo, useRef, useState } from "react";
import { useAui, useAuiState } from "@assistant-ui/react";
import { History, Maximize2, Minimize2, Plus, Search } from "lucide-react";
import AngelaMark from "../AngelaMark";
import { field, floating, ghostButton } from "./surfaces";
import { cn } from "../../lib/cn";
import { useT } from "../../lib/i18n";

function useVisibleThreads() {
  const threadItems = useAuiState((s) => s.threads.threadItems);
  return useMemo(
    () =>
      threadItems
        .filter((t) => Boolean(t.remoteId) && t.status === "regular")
        .map((t) => ({
          remoteId: t.remoteId,
          title: t.title?.trim() || "",
          lastMessageAt: t.lastMessageAt ?? new Date(),
        }))
        .sort((a, b) => b.lastMessageAt.getTime() - a.lastMessageAt.getTime()),
    [threadItems],
  );
}

function esMismoDia(a, b) {
  return a.toDateString() === b.toDateString();
}

function agruparPorDia(threads, t) {
  const hoy = new Date();
  const ayer = new Date(hoy);
  ayer.setDate(ayer.getDate() - 1);

  const grupos = [
    { etiqueta: t("angela.historial_hoy"), items: [] },
    { etiqueta: t("angela.historial_ayer"), items: [] },
    { etiqueta: t("angela.historial_anteriores"), items: [] },
  ];
  for (const item of threads) {
    if (esMismoDia(item.lastMessageAt, hoy)) grupos[0].items.push(item);
    else if (esMismoDia(item.lastMessageAt, ayer)) grupos[1].items.push(item);
    else grupos[2].items.push(item);
  }
  return grupos.filter((g) => g.items.length > 0);
}

export function useActiveThreadTitle(fallback) {
  const t = useT();
  const title = useAuiState((s) => s.threadListItem.title)?.trim();
  return title || fallback || t("angela.titulo");
}

export function NewChatButton({ className }) {
  const t = useT();
  const aui = useAui();
  return (
    <button
      type="button"
      onClick={() => aui.threads.switchToNewThread()}
      title={t("angela.nueva_consulta")}
      aria-label={t("angela.nueva_consulta")}
      className={cn(ghostButton, "h-9 w-9 shrink-0", className)}
    >
      <Plus size={18} />
    </button>
  );
}

export function HistoryDropdown({ className }) {
  const t = useT();
  const aui = useAui();
  const activeId = useAuiState((s) => s.threadListItem.remoteId);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef(null);
  const threads = useVisibleThreads();

  const filtrados = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return threads;
    return threads.filter((item) => item.title.toLowerCase().includes(q));
  }, [threads, query]);

  const grupos = useMemo(() => agruparPorDia(filtrados, t), [filtrados, t]);

  const abrir = () => {
    setOpen((v) => !v);
    queueMicrotask(() => inputRef.current?.focus());
  };

  return (
    <div className={cn("relative shrink-0", className)}>
      <button
        type="button"
        onClick={abrir}
        title={t("angela.historial")}
        aria-label={t("angela.historial")}
        className={cn(ghostButton, "h-9 w-9")}
      >
        <History size={18} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} aria-hidden="true" />
          <div className={cn(floating, "absolute right-0 top-10 z-50 w-[min(20rem,calc(100vw-2rem))] rounded-2xl p-2")}>
            <div className={cn(field, "mb-2 flex items-center gap-2 rounded-xl px-3 py-2")}>
              <Search size={14} className="shrink-0 text-tinta-suave" />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t("angela.buscar_consultas")}
                className="w-full bg-transparent text-[13px] text-tinta placeholder:text-tinta-suave focus:outline-none"
              />
            </div>
            <div className="max-h-80 overflow-y-auto">
              {grupos.length === 0 && (
                <p className="px-3 py-4 text-center text-[12.5px] text-tinta-suave">
                  {t("angela.sin_consultas")}
                </p>
              )}
              {grupos.map((g) => (
                <div key={g.etiqueta} className="mb-2 last:mb-0">
                  <div className="px-2 pb-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-tinta-suave/80">
                    {g.etiqueta}
                  </div>
                  <div className="flex flex-col gap-0.5">
                    {g.items.map((item) => (
                      <button
                        key={item.remoteId}
                        type="button"
                        onClick={() => {
                          setOpen(false);
                          aui.threads.switchToThread(item.remoteId);
                        }}
                        className={cn(
                          "w-full truncate rounded-xl px-3 py-2 text-left text-[13px] transition-colors",
                          item.remoteId === activeId
                            ? "bg-violeta-suave/50 font-semibold text-violeta"
                            : "text-tinta hover:bg-papel-hondo",
                        )}
                      >
                        {item.title || t("angela.sin_titulo")}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function FullscreenButton({ onClick, className }) {
  const t = useT();
  return (
    <button
      type="button"
      onClick={onClick}
      title={t("angela.pantalla_completa")}
      aria-label={t("angela.pantalla_completa")}
      className={cn(ghostButton, "h-9 w-9 shrink-0", className)}
    >
      <Maximize2 size={17} />
    </button>
  );
}

export function MinimizeButton({ onClick, className }) {
  const t = useT();
  return (
    <button
      type="button"
      onClick={onClick}
      title={t("angela.volver_panel")}
      aria-label={t("angela.volver_panel")}
      className={cn(ghostButton, "h-9 w-9 shrink-0", className)}
    >
      <Minimize2 size={17} />
    </button>
  );
}

/** Barra superior: título del hilo activo, nueva consulta (+) e historial. */
export function ChatToolbar({ className, compact = false, trailing = null }) {
  const t = useT();
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const title = useActiveThreadTitle();

  return (
    <header className={cn("flex items-center gap-1.5", compact ? "py-0" : "border-b border-linea px-1 py-2", className)}>
      <AngelaMark size={compact ? 24 : 28} estado={isRunning ? "pensando" : "idle"} />
      <p className={cn("min-w-0 flex-1 truncate font-semibold text-tinta", compact ? "text-[13px]" : "text-[14px]")}>
        {title}
      </p>
      <NewChatButton />
      <HistoryDropdown />
      {trailing}
    </header>
  );
}
