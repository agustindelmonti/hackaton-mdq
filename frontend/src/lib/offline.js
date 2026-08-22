// ============================================================================
// MODO SIN CONEXIÓN — porque adentro de un frigorífico no hay señal.
// ----------------------------------------------------------------------------
// El operario está parado en una cámara a 4 grados, con guantes, y acaba de
// mover dieciocho bolsones. No hay wifi y el celular no tiene datos: las
// paredes de una cámara frigorífica son una jaula de Faraday bastante decente.
//
// Si la app necesita conexión para registrar eso, no sirve en el mundo real. El
// operario va a anotarlo en un papel, y ese papel es exactamente la planilla
// que vinimos a matar.
//
// CÓMO FUNCIONA
//
//   · Un SNAPSHOT del stock y de los catálogos se guarda en IndexedDB cada vez
//     que hay conexión. Con eso, sin red se puede seguir consultando lotes y
//     VALIDANDO disponibilidad — con el último dato conocido, y diciéndolo.
//   · Lo que el operario registra sin red va a una COLA local, visible, con
//     estado "pendiente de sincronizar". No se pierde y no miente: nadie cree
//     que ya está en el sistema.
//   · Cuando vuelve la conexión, la cola se manda sola. Y acá está la parte que
//     importa: cada movimiento se RE-VALIDA contra el stock real del servidor.
//     El snapshot podía estar viejo; alguien pudo mover ese mismo lote mientras
//     no había señal. Lo que no pasa la re-validación no se descarta en
//     silencio: queda marcado como `conflicto` para que una persona decida.
//
// POR QUÉ INDEXEDDB Y NO localStorage: localStorage es síncrono (bloquea el
// hilo de la UI), tiene ~5 MB y guarda sólo strings. Acá hay que guardar el
// snapshot de 147 lotes y una cola que puede tener fotos adentro.
// ============================================================================

const DB_NOMBRE = "polpilot-papasud";
const DB_VERSION = 1;
const STORE_COLA = "cola";
const STORE_SNAPSHOT = "snapshot";

let _db = null;

function abrir() {
  if (_db) return Promise.resolve(_db);
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NOMBRE, DB_VERSION);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE_COLA)) {
        db.createObjectStore(STORE_COLA, { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains(STORE_SNAPSHOT)) {
        db.createObjectStore(STORE_SNAPSHOT, { keyPath: "clave" });
      }
    };
    req.onsuccess = () => { _db = req.result; resolve(_db); };
    req.onerror = () => reject(req.error);
  });
}

async function tx(store, modo, fn) {
  const db = await abrir();
  return new Promise((resolve, reject) => {
    const t = db.transaction(store, modo);
    const s = t.objectStore(store);
    const r = fn(s);
    t.oncomplete = () => resolve(r && r.result !== undefined ? r.result : r);
    t.onerror = () => reject(t.error);
  });
}

// --- el snapshot: la última foto conocida del stock -------------------------
export async function guardarSnapshot(clave, datos) {
  try {
    await tx(STORE_SNAPSHOT, "readwrite", (s) =>
      s.put({ clave, datos, guardado: new Date().toISOString() }));
  } catch { /* sin IndexedDB (modo privado viejo): el online sigue andando */ }
}

export async function leerSnapshot(clave) {
  try {
    const r = await tx(STORE_SNAPSHOT, "readonly", (s) => s.get(clave));
    return r || null;
  } catch {
    return null;
  }
}

// --- la cola: lo que se registró sin señal ----------------------------------
export async function encolar(item) {
  const registro = {
    id: `local-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    creado: new Date().toISOString(),
    estado: "pendiente",
    intentos: 0,
    ...item,
  };
  await tx(STORE_COLA, "readwrite", (s) => s.put(registro));
  emitir();
  return registro;
}

export async function pendientes() {
  try {
    const db = await abrir();
    return new Promise((resolve) => {
      const t = db.transaction(STORE_COLA, "readonly");
      const req = t.objectStore(STORE_COLA).getAll();
      req.onsuccess = () => resolve(req.result || []);
      req.onerror = () => resolve([]);
    });
  } catch {
    return [];
  }
}

export async function borrarDeLaCola(id) {
  await tx(STORE_COLA, "readwrite", (s) => s.delete(id));
  emitir();
}

async function actualizar(item) {
  await tx(STORE_COLA, "readwrite", (s) => s.put(item));
  emitir();
}

// --- estado de conexión -----------------------------------------------------
// `navigator.onLine` miente seguido: dice true cuando hay wifi sin salida (el
// caso clásico del portal cautivo, y también el del frigorífico con un repetidor
// que llega pero no rutea). Por eso el estado real se confirma con un ping
// barato al backend, no sólo con lo que dice el navegador.
let _online = typeof navigator === "undefined" ? true : navigator.onLine;
let _sincronizando = false;
let _ultimoChequeo = 0;

const oyentes = new Set();
let cache = { online: _online, pendientes: 0, sincronizando: false, conflictos: 0 };

function emitir() {
  pendientes().then((ps) => {
    cache = {
      online: _online,
      sincronizando: _sincronizando,
      pendientes: ps.filter((p) => p.estado === "pendiente").length,
      conflictos: ps.filter((p) => p.estado === "conflicto").length,
    };
    oyentes.forEach((fn) => fn());
  });
}

export const estadoConexion = {
  subscribe(fn) {
    oyentes.add(fn);
    return () => oyentes.delete(fn);
  },
  getSnapshot() {
    return cache;
  },
};

export function estaOnline() {
  return _online;
}

async function ping() {
  // No pisamos el estado más de una vez cada 5 s: esto corre en el celular de
  // alguien que está trabajando, no en una máquina de test.
  if (Date.now() - _ultimoChequeo < 5000) return _online;
  _ultimoChequeo = Date.now();
  try {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 3000);
    const r = await fetch("/api/health", { signal: ctrl.signal, cache: "no-store" });
    clearTimeout(t);
    _online = r.ok;
  } catch {
    _online = false;
  }
  return _online;
}

// --- la sincronización ------------------------------------------------------
export async function sincronizar(enviar) {
  // `enviar` es la función que sabe hablar con la API (se le pasa desde afuera
  // para no acoplar este módulo al cliente HTTP ni a los endpoints).
  if (_sincronizando) return { ya: true };
  const ps = (await pendientes()).filter((p) => p.estado === "pendiente");
  if (!ps.length) return { enviados: 0, conflictos: 0 };
  if (!(await ping())) return { sin_conexion: true };

  _sincronizando = true;
  emitir();
  let enviados = 0, conflictos = 0;
  for (const item of ps) {
    try {
      // El servidor vuelve a validar disponibilidad con el stock REAL. El
      // snapshot con el que se validó offline podía estar viejo.
      const r = await enviar(item);
      await borrarDeLaCola(item.id);
      enviados += 1;
      item.resultado = r;
    } catch (e) {
      const esConflicto = e && (e.status === 409 || e.conflicto);
      await actualizar({
        ...item,
        estado: esConflicto ? "conflicto" : "pendiente",
        intentos: (item.intentos || 0) + 1,
        error: (e && (e.detalle || e.message)) || "error",
      });
      if (esConflicto) conflictos += 1;
    }
  }
  _sincronizando = false;
  emitir();
  return { enviados, conflictos };
}

// --- arranque ---------------------------------------------------------------
export function iniciarOffline(enviar) {
  if (typeof window === "undefined") return;
  const alVolver = async () => {
    _online = true;
    _ultimoChequeo = 0;
    emitir();
    await sincronizar(enviar);
  };
  const alCaer = () => { _online = false; _ultimoChequeo = Date.now(); emitir(); };

  window.addEventListener("online", alVolver);
  window.addEventListener("offline", alCaer);

  // Un ping AL ARRANQUE, no sólo cada 20 s. Sin esto, el estado inicial sale de
  // `navigator.onLine` (que miente) o queda pegado en el último valor: la app
  // decía "sin señal" con la señal andando, que es peor que no decir nada.
  ping().then((ok) => { emitir(); if (ok) sincronizar(enviar); });
  // El ping periódico existe por el portal cautivo: `navigator.onLine` puede
  // decir que hay red y no haber salida. Cada 20 s es suficiente y no gasta.
  setInterval(async () => {
    const antes = _online;
    const ahora = await ping();
    if (ahora !== antes) {
      emitir();
      if (ahora) await sincronizar(enviar);
    }
  }, 20000);
  emitir();
}
