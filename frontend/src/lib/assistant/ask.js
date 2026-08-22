import { useCallback } from "react";
import { useAui } from "@assistant-ui/react";
import { useAngelaDock } from "./runtime-provider";

/** Send a prompt into the shared Ángela thread and open the dock. */
export function useAskAngela() {
  const aui = useAui();
  const dock = useAngelaDock();

  return useCallback(
    (text) => {
      const q = text.trim();
      if (!q) return;
      dock.setOpen(true);
      aui.thread.append(q);
    },
    [aui, dock],
  );
}
