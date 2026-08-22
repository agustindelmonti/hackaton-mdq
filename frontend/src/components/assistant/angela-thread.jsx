import { useEffect, useState } from "react";
import {
  AuiIf,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAui,
  useAuiState,
} from "@assistant-ui/react";
import { WebSpeechDictationAdapter } from "@assistant-ui/core";
import { ArrowUpIcon, Camera, SquareIcon } from "lucide-react";
import AngelaMark from "../AngelaMark";
import { ErrorState } from "./error-state";
import { ThinkingIndicator } from "./thinking-indicator";
import { AngelaToolCall } from "./angela-tool";
import { ComposerVoice, ComposerVoiceButton } from "./composer";
import { inkButton, ghostButton } from "./surfaces";
import { cn } from "../../lib/cn";
import { toolLabels } from "../../lib/assistant/tool-labels";

function AssistantText({ text }) {
  return (
    <p className="whitespace-pre-line text-[0.95rem] leading-snug text-tinta">{text}</p>
  );
}

function chatErrorFields(status) {
  if (status?.type !== "incomplete" || status.reason !== "error") {
    return { code: "", message: "" };
  }
  const err = status.error;
  const code =
    typeof err === "object" && err !== null && "code" in err
      ? String(err.code ?? "")
      : "";
  const message =
    typeof err === "string"
      ? err
      : typeof err === "object" && err !== null && "message" in err
        ? String(err.message ?? "")
        : "";
  return { code, message };
}

export function AngelaThread({
  placeholder,
  suggestions = [],
  emptyTitle,
  emptyDetail,
  variant = "compact",
  className,
  onOpcion,
  renderExtras,
  extraComposer,
}) {
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const fullscreen = variant === "fullscreen";

  return (
    <ThreadPrimitive.Root
      className={cn("flex h-full min-h-0 flex-col", className)}
      style={{ "--thread-max-width": "42rem" }}
    >
      <ThreadPrimitive.Viewport className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
        <AuiIf condition={(s) => s.thread.isEmpty}>
          {fullscreen ? (
            <div className="flex flex-1 flex-col items-center justify-center px-4 py-6 text-center">
              <AngelaMark size={52} />
              {emptyTitle && (
                <h2 className="mt-4 font-display text-[1.15rem] font-bold leading-snug text-tinta">
                  {emptyTitle}
                </h2>
              )}
              {emptyDetail && (
                <p className="mt-2 max-w-[320px] text-[0.86rem] leading-relaxed text-tinta-suave">
                  {emptyDetail}
                </p>
              )}
              {suggestions.length > 0 && (
                <div className="mt-6 flex w-full max-w-md flex-col gap-2">
                  {suggestions.map((chip) => {
                    const prompt = typeof chip === "string" ? chip : chip.enviar;
                    const label = typeof chip === "string" ? chip : chip.label ?? chip.enviar;
                    return (
                      <ThreadPrimitive.Suggestion
                        key={typeof chip === "string" ? chip : chip.lk ?? chip.enviar}
                        prompt={prompt}
                        send
                        className="rounded-2xl border border-linea bg-crema px-4 py-3 text-left text-[0.88rem] leading-snug text-tinta transition-colors hover:border-violeta/40 hover:bg-violeta-suave/40"
                      >
                        {label}
                      </ThreadPrimitive.Suggestion>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-1 flex-col justify-end px-1 pb-2">
              {suggestions.length > 0 && (
                <div className="flex w-full flex-col gap-2">
                  {suggestions.map((chip) => {
                    const prompt = typeof chip === "string" ? chip : chip.enviar;
                    const label = typeof chip === "string" ? chip : chip.label ?? chip.enviar;
                    return (
                      <ThreadPrimitive.Suggestion
                        key={typeof chip === "string" ? chip : chip.lk ?? chip.enviar}
                        prompt={prompt}
                        send
                        className="rounded-2xl border border-linea bg-crema px-3.5 py-3 text-left text-[0.88rem] leading-snug text-tinta transition-colors hover:border-violeta/40 hover:bg-violeta-suave/40"
                      >
                        {label}
                      </ThreadPrimitive.Suggestion>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </AuiIf>

        <ThreadPrimitive.Messages>
          {({ message }) =>
            message.role === "user" ? <UserMessage /> : (
              <AssistantMessage onOpcion={onOpcion} renderExtras={renderExtras} />
            )
          }
        </ThreadPrimitive.Messages>

        {isRunning && <ThinkingRow />}

        <ThreadPrimitive.ViewportFooter className="sticky bottom-0 mt-auto bg-gradient-to-t from-papel via-papel to-transparent pt-2">
          <AngelaComposer placeholder={placeholder} extraComposer={extraComposer} />
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className="flex justify-end">
      <div className="max-w-[85%] whitespace-pre-line rounded-2xl rounded-tr-md bg-tinta px-3.5 py-2.5 text-[0.95rem] leading-snug text-crema">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
}

function AssistantMessage({ onOpcion, renderExtras }) {
  const meta = useAuiState((s) => s.message.metadata?.custom);
  const aui = useAui();
  const hasParts = useAuiState((s) => (s.message.content?.length ?? 0) > 0);

  return (
    <MessagePrimitive.Root className="flex gap-2.5">
      <AngelaMark size={28} />
      <div className="min-w-0 max-w-[88%]">
        {hasParts && (
          <div className="rounded-2xl rounded-tl-md border border-linea bg-crema px-3.5 py-2.5 sombra-papel">
            <MessagePrimitive.Parts
              components={{
                Text: ({ text }) => <AssistantText text={text} />,
                tools: {
                  Fallback: AngelaToolCall,
                },
              }}
            />
            {renderExtras?.(meta)}
            {meta?.sinModelo && (
              <p className="mt-2 border-t border-linea pt-1.5 text-[11px] leading-snug text-tinta-suave">
                Lo saqué de los datos: ahora mismo no tengo el modelo conectado.
              </p>
            )}
          </div>
        )}
        {meta?.opciones?.length > 0 && (
          <div className="mt-2 flex flex-col gap-1.5">
            {meta.opciones.map((op, k) => (
              <button
                key={k}
                type="button"
                onClick={() => onOpcion?.(op.enviar ?? op.label)}
                className="rounded-xl border border-violeta/30 bg-crema px-3 py-2 text-left text-[0.86rem] font-semibold text-violeta transition-colors hover:bg-violeta hover:text-crema"
              >
                {op.label}
              </button>
            ))}
          </div>
        )}
        <MessagePrimitive.Error>
          <RetryError
            className={hasParts ? "mt-2" : undefined}
            onRetry={() => aui.message.reload()}
          />
        </MessagePrimitive.Error>
      </div>
    </MessagePrimitive.Root>
  );
}

function RetryError({ onRetry, className }) {
  const retrying = useAuiState((s) => s.message.status?.type === "running");
  const errorCode = useAuiState((s) => chatErrorFields(s.message.status).code);
  const errorMessage = useAuiState((s) => chatErrorFields(s.message.status).message);
  const rateLimited = errorCode === "rate_limit" || /429|rate.?limit/i.test(errorMessage);
  return (
    <ErrorState
      className={className}
      title={rateLimited ? "Demasiadas consultas" : "No pude responder"}
      detail={
        rateLimited
          ? "El modelo está limitado por ahora. Probá de nuevo en un momento."
          : (errorMessage || "Se cortó la consulta. Probá de nuevo en un momento.")
      }
      retrying={retrying}
      onRetry={onRetry}
    />
  );
}

function ThinkingRow() {
  const last = useAuiState((s) => s.thread.messages.at(-1));
  const runningTool = last?.content.find(
    (part) => part.type === "tool-call" && part.result === undefined,
  );
  const label = runningTool && runningTool.type === "tool-call"
    ? toolLabels(runningTool.toolName).running
    : "Consultando tus datos…";

  return (
    <AuiIf condition={(s) => {
      const msg = s.thread.messages.at(-1);
      if (!msg || msg.role !== "assistant") return true;
      return !msg.content.some((p) => p.type === "text" && p.text);
    }}>
      <div className="flex gap-2.5">
        <AngelaMark size={28} />
        <ThinkingIndicator label={label} />
      </div>
    </AuiIf>
  );
}

function AngelaComposer({ placeholder, extraComposer }) {
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const canSend = useAuiState((s) => s.composer.canSend);
  const dictation = useAuiState((s) => s.composer.dictation);
  const recording =
    dictation?.status.type === "starting" || dictation?.status.type === "running";
  const [voiceOk, setVoiceOk] = useState(false);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    setVoiceOk(WebSpeechDictationAdapter.isSupported());
  }, []);

  useEffect(() => {
    if (!recording) {
      setSeconds(0);
      return;
    }
    const started = Date.now();
    const tick = window.setInterval(() => {
      setSeconds(Math.floor((Date.now() - started) / 1000));
    }, 250);
    return () => window.clearInterval(tick);
  }, [recording]);

  return (
    <ComposerPrimitive.Root className="rounded-full border border-linea bg-crema p-1.5 pl-2 sombra-papel">
      <div className="flex items-end gap-1">
        {extraComposer}
        {recording ? (
          <div className="min-w-0 flex-1">
            <ComposerVoice recording={dictation?.status.type === "running"} seconds={seconds} />
            <ComposerPrimitive.DictationTranscript className="block truncate px-3 pb-1 text-[12px] leading-snug text-tinta-suave" />
          </div>
        ) : (
          <ComposerPrimitive.Input
            placeholder={placeholder}
            rows={1}
            className="min-h-11 max-h-32 w-full min-w-0 flex-1 resize-none bg-transparent px-2 text-[0.95rem] text-tinta caret-violeta placeholder:text-tinta-suave/70 focus:outline-none"
          />
        )}
        {voiceOk && (
          recording ? (
            <ComposerPrimitive.StopDictation asChild>
              <ComposerVoiceButton active />
            </ComposerPrimitive.StopDictation>
          ) : (
            <ComposerPrimitive.Dictate asChild>
              <ComposerVoiceButton active={false} />
            </ComposerPrimitive.Dictate>
          )
        )}
        {isRunning ? (
          <ComposerPrimitive.Cancel
            className={cn(inkButton, "grid h-11 w-11 shrink-0 place-items-center rounded-full")}
            aria-label="Detener"
          >
            <SquareIcon className="size-3 fill-current" />
          </ComposerPrimitive.Cancel>
        ) : (
          <ComposerPrimitive.Send
            className={cn(
              "grid h-11 w-11 shrink-0 place-items-center rounded-full bg-violeta text-crema transition-transform active:scale-90 disabled:opacity-40",
              !canSend && "opacity-40",
            )}
            aria-label="Enviar"
          >
            <ArrowUpIcon className="size-[18px]" />
          </ComposerPrimitive.Send>
        )}
      </div>
    </ComposerPrimitive.Root>
  );
}

export function CameraComposerButton({ onClick, title }) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={cn(ghostButton, "grid h-11 w-11 shrink-0 place-items-center rounded-full")}
    >
      <Camera size={20} />
    </button>
  );
}
