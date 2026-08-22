import { getAngelaRunContext, getAngelaOnDone } from "./run-context";

const RATE_LIMIT_DETAIL =
  "El modelo está limitado por ahora. Probá de nuevo en un momento.";
const GENERIC_DETAIL = "Se cortó la consulta. Probá de nuevo en un momento.";

function looksLikeRateLimit(blob) {
  return /\b429\b|rate_limit|RateLimitExceeded/i.test(blob);
}

function isToolDump(text) {
  return /<\/?function\b|<tool_call>|<\/tool_call>|<\|tool_call\|>/i.test(text || "");
}

function visibleAssistantText(text) {
  if (!isToolDump(text)) return text;
  const stripped = text
    .replace(/<function\b[\s\S]*?<\/function>/gi, "")
    .replace(/<tool_call>[\s\S]*?<\/tool_call>/gi, "")
    .replace(/<\/function>/gi, "")
    .trim();
  if (!stripped || /^[\d\s{}":,[\]]+$/.test(stripped)) return "";
  return stripped;
}

export function angelaChatFailure(input) {
  const blob = [input.errorCode, input.errorTecnico, input.body, input.status]
    .filter(Boolean)
    .join(" ");
  if (input.status === 429 || input.errorCode === "rate_limit" || looksLikeRateLimit(blob)) {
    return { code: "rate_limit", message: RATE_LIMIT_DETAIL };
  }
  return {
    code: input.errorCode || "provider",
    message: input.fallback?.trim() || GENERIC_DETAIL,
  };
}

function textOf(message) {
  return message.content
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n");
}

function metaFromDone(result) {
  const plan = (result.acciones || []).find((a) => a.type === "plan_progreso");
  const docAccion = (result.acciones || []).find((a) => a.type === "documento");
  return {
    modo: result.modo,
    acciones: result.acciones || [],
    opciones: result.opciones || [],
    plan: plan ? { pasos: plan.pasos, resumen: plan.resumen } : undefined,
    documento: docAccion?.documento,
    sinModelo: result.modo === "simulado",
    sugerencias: result.sugerencias || [],
  };
}

export const angelaChatAdapter = {
  async *run({ messages, abortSignal }) {
    const ctx = getAngelaRunContext();
    const lastUser = [...messages].reverse().find((m) => m.role === "user");
    const pregunta = lastUser ? textOf(lastUser) : "";
    const historial = messages
      .filter((m) => m !== lastUser && (m.role === "user" || m.role === "assistant"))
      .map((m) => ({ role: m.role, content: textOf(m) }))
      .filter((m) => m.content);

    const response = await fetch("/api/angela/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: abortSignal,
      body: JSON.stringify({
        mensaje: pregunta,
        historial,
        token: ctx.token,
      }),
    });

    if (!response.ok || !response.body) {
      const body = await response.text().catch(() => response.statusText);
      yield {
        content: [],
        status: {
          type: "incomplete",
          reason: "error",
          error: angelaChatFailure({ status: response.status, body }),
        },
      };
      return;
    }

    const tools = new Map();
    let text = "";
    let meta = {};

    const emit = () => ({
      content: [
        ...Array.from(tools.values()),
        ...(text ? [{ type: "text", text }] : []),
      ],
      metadata: { custom: meta },
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split("\n\n");
      buffer = chunks.pop() ?? "";
      for (const chunk of chunks) {
        const line = chunk.split("\n").find((l) => l.startsWith("data:"));
        if (!line) continue;
        let event;
        try {
          event = JSON.parse(line.slice(5).trim());
        } catch {
          continue;
        }
        if (event.type === "tool") {
          tools.set(event.id, {
            type: "tool-call",
            toolCallId: event.id,
            toolName: event.name,
            args: event.input ?? {},
            argsText: JSON.stringify(event.input ?? {}),
            result: event.result,
          });
          yield emit();
        } else if (event.type === "text") {
          text = visibleAssistantText(event.text);
          yield emit();
        } else if (event.type === "suggestions") {
          meta = { ...meta, sugerencias: event.suggestions || [] };
          yield emit();
        } else if (event.type === "done") {
          const result = event.result ?? {};
          const answer = result.respuesta ?? text;
          const visible = visibleAssistantText(answer);
          const dump = isToolDump(answer) && !visible;
          if (result.ok === false || dump) {
            yield {
              ...emit(),
              status: {
                type: "incomplete",
                reason: "error",
                error: angelaChatFailure({
                  errorCode: result.error_code,
                  errorTecnico: result.error_tecnico,
                  fallback: dump ? undefined : result.respuesta,
                }),
              },
            };
            return;
          }
          if (visible) text = visible;
          meta = metaFromDone(result);
          getAngelaOnDone()?.(result);
          yield emit();
        }
      }
    }
  },
};
