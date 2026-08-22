import { createContext, useCallback, useContext, useMemo } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  useRemoteThreadListRuntime,
} from "@assistant-ui/react";
import { WebSpeechDictationAdapter } from "@assistant-ui/core";
import {
  createLocalStorageAdapter,
  createSimpleTitleAdapter,
} from "@assistant-ui/core/react";
import { angelaChatAdapter } from "./adapter";

const browserStorage = {
  async getItem(key) {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(key);
  },
  async setItem(key, value) {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(key, value);
  },
  async removeItem(key) {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(key);
  },
};

const threadListAdapter = createLocalStorageAdapter({
  storage: browserStorage,
  prefix: "polpilot.angela",
  titleGenerator: createSimpleTitleAdapter(),
});

const DockContext = createContext(null);

export function useAngelaDock() {
  const value = useContext(DockContext);
  if (!value) {
    return {
      open: false,
      setOpen: () => undefined,
      toggle: () => undefined,
    };
  }
  return value;
}

function useAngelaRuntime() {
  const dictation = useMemo(
    () =>
      new WebSpeechDictationAdapter({
        language: "es-AR",
        continuous: true,
        interimResults: true,
      }),
    [],
  );
  return useRemoteThreadListRuntime({
    runtimeHook: () =>
      useLocalRuntime(angelaChatAdapter, {
        maxSteps: 1,
        adapters: { dictation },
      }),
    adapter: threadListAdapter,
  });
}

export function AngelaRuntimeProvider({ children, dockOpen, setDockOpen }) {
  const runtime = useAngelaRuntime();
  const toggle = useCallback(() => setDockOpen?.((v) => !v), [setDockOpen]);
  const dock = useMemo(
    () => ({
      open: dockOpen ?? false,
      setOpen: setDockOpen ?? (() => undefined),
      toggle,
    }),
    [dockOpen, setDockOpen, toggle],
  );

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <DockContext.Provider value={dock}>{children}</DockContext.Provider>
    </AssistantRuntimeProvider>
  );
}
