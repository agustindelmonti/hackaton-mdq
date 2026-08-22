import { useEffect } from "react";
import { X } from "lucide-react";
import AngelaView from "../../views/AngelaView";
import { AngelaDock } from "./angela-dock";
import { FullscreenButton, MinimizeButton } from "./chat-toolbar";
import { useT } from "../../lib/i18n";

export default function AngelaPanel({
  fullscreen,
  onFullscreen,
  onMinimize,
  onClose,
  user,
  onNavigate,
  onDatosCambiaron,
  inputInicial,
  placeholderChips,
  saludoInicial,
}) {
  const t = useT();

  useEffect(() => {
    if (!fullscreen) return undefined;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (e) => {
      if (e.key === "Escape") onMinimize?.();
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = prev;
      window.removeEventListener("keydown", onKey);
    };
  }, [fullscreen, onMinimize]);

  const toolbarTrailing = fullscreen ? (
    <MinimizeButton onClick={onMinimize} />
  ) : (
    <>
      <FullscreenButton onClick={onFullscreen} />
      <button
        type="button"
        onClick={onClose}
        className="grid h-9 w-9 shrink-0 place-items-center rounded-full text-tinta-suave hover:bg-papel-hondo hover:text-tinta"
        aria-label={t("angela.cerrar_panel")}
      >
        <X size={18} />
      </button>
    </>
  );

  const view = (
    <AngelaView
      variant={fullscreen ? "fullscreen" : "compact"}
      user={user}
      onNavigate={onNavigate}
      onDatosCambiaron={onDatosCambiaron}
      inputInicial={inputInicial}
      placeholderChips={placeholderChips}
      saludoInicial={saludoInicial}
      toolbarTrailing={toolbarTrailing}
    />
  );

  if (fullscreen) {
    return (
      <div className="fixed inset-0 z-[120] flex flex-col bg-papel">
        <div className="mx-auto flex h-full w-full max-w-3xl flex-col px-4 pb-4 pt-3">
          {view}
        </div>
      </div>
    );
  }

  return (
    <AngelaDock>
      <div className="flex min-h-0 flex-1 flex-col overflow-hidden px-3 py-2">
        {view}
      </div>
    </AngelaDock>
  );
}
