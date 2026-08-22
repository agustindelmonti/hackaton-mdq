/** Context injected into every Ángela chat request (token, rol, vista). */

const STORAGE_KEY = "polpilot.angela.runContext";

const FALLBACK = {
  token: null,
  rol: null,
  nombre: null,
  vista: null,
};

let current = { ...FALLBACK };
let onDone = null;

function readStored() {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return { ...FALLBACK, ...JSON.parse(raw) };
  } catch {
    return null;
  }
}

export function setAngelaRunContext(ctx) {
  current = { ...FALLBACK, ...ctx };
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
}

export function getAngelaRunContext() {
  const stored = readStored();
  if (stored) current = stored;
  return current;
}

export function setAngelaOnDone(fn) {
  onDone = fn;
}

export function getAngelaOnDone() {
  return onDone;
}
