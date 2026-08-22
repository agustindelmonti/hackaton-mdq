// ============================================================================
// Service worker — para que la app ABRA sin señal.
// ----------------------------------------------------------------------------
// La cola offline no sirve de nada si la pantalla no carga. Adentro de una
// cámara frigorífica no hay red: si el operario abre la app y ve el dinosaurio
// del navegador, todo lo demás es teoría.
//
// DOS ESTRATEGIAS, CADA UNA DONDE CORRESPONDE:
//
//   · El SHELL (html, js, css, fuentes, logo) va cache-first. Son archivos con
//     hash en el nombre: si cambian, cambia la URL, así que servir del cache es
//     siempre correcto y es instantáneo.
//   · Los DATOS (/api/...) van network-first con fallback al cache. Con red,
//     siempre el dato fresco. Sin red, la última respuesta buena, marcada con
//     la cabecera `X-Desde-Cache` para que la UI pueda decir "esto es de hace
//     un rato" en vez de hacerlo pasar por actual.
//
// Lo que NO se cachea nunca: los POST. Un movimiento no se "responde de cache":
// se encola en IndexedDB y se manda cuando vuelve la señal (ver lib/offline.js).
// ============================================================================

const VERSION = "papasud-v1";
const SHELL = `${VERSION}-shell`;
const DATOS = `${VERSION}-datos`;

// Lo mínimo para que la app abra. El resto de los assets entra al cache solo,
// a medida que se usan.
const BASE = ["/", "/index.html", "/logos/papasud.svg"];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(SHELL)
      .then((c) => c.addAll(BASE).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((ks) => Promise.all(
        ks.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;               // los POST no se cachean jamás
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  // --- datos: red primero, cache como red de contención -------------------
  if (url.pathname.startsWith("/api/")) {
    e.respondWith(
      fetch(req)
        .then((r) => {
          if (r.ok) {
            const copia = r.clone();
            caches.open(DATOS).then((c) => c.put(req, copia));
          }
          return r;
        })
        .catch(async () => {
          const cacheada = await caches.match(req);
          if (!cacheada) throw new Error("sin red y sin cache");
          // Se marca la respuesta para que la pantalla pueda avisar que el dato
          // no es de ahora. Servir dato viejo como si fuera fresco sería peor
          // que no servir nada.
          const cuerpo = await cacheada.blob();
          const h = new Headers(cacheada.headers);
          h.set("X-Desde-Cache", "1");
          return new Response(cuerpo, { status: 200, headers: h });
        })
    );
    return;
  }

  // --- shell: cache primero -----------------------------------------------
  e.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((r) => {
        if (r.ok && (req.destination || url.pathname.startsWith("/assets/"))) {
          const copia = r.clone();
          caches.open(SHELL).then((c) => c.put(req, copia));
        }
        return r;
      }).catch(() => caches.match("/index.html"));
    })
  );
});
