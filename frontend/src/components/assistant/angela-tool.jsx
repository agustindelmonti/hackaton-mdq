import { useState } from "react";
import { ToolCall } from "./tool-call";
import { toolLabels } from "../../lib/assistant/tool-labels";

function summarizeArgs(args) {
  if (!args || typeof args !== "object") return "";
  const values = Object.values(args)
    .filter((v) => v != null && v !== "")
    .map((v) => String(v));
  return values[0] ?? "";
}

export function AngelaToolCall(props) {
  const [open, setOpen] = useState(false);
  const labels = toolLabels(props.toolName);
  const running = props.result === undefined;
  const query = summarizeArgs(props.args);
  const request = props.argsText || JSON.stringify(props.args ?? {}, null, 2);
  const result =
    props.result === undefined
      ? "…"
      : typeof props.result === "string"
        ? props.result
        : JSON.stringify(props.result, null, 2);

  return (
    <ToolCall
      className="max-w-none"
      label={labels.done}
      activeLabel={labels.running}
      query={query}
      request={request}
      result={result}
      running={running}
      open={open}
      onOpenChange={setOpen}
    />
  );
}
