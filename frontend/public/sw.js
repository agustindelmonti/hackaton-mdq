// ============================================================================
// Service worker — para que la app ABRA sin señal.
// ----------------------------------------------------------------------------
// La cola offline no sirve de nada si la pantalla no carga. Adentro de una
// cámara frigorífica no hay red: si el operario abre la app y ve el dinosaurio
// del navegador, todo lo demás es teoría.
//
// DOS ESTRATEGIAS, CADA UNA DONDE CORRESPONDE:
//
//   · El HTML y sw.js van network-first. El index apunta a /assets/index-HASH.js:
//     si se sirve un index viejo de cache, el HASH ya no está en el server y
//     FastAPI (antes) devolvía index.html con MIME text/html → pantalla blanca.
//   · Los ASSETS con hash (/assets/...) van cache-first. La URL es inmutable:
//     si cambian, cambia el nombre. Nunca se cachea una respuesta text/html
//     bajo una URL .js/.css (eso envenenaba el cache en deploys seguidos).
//   · Los DATOS (/api/...) van network-first con fallback al cache.
//
// Lo que NO se cachea nunca: los POST. Un movimiento no se "responde de cache":
// se encola en IndexedDB y se manda cuando vuelve la señal (ver lib/offline.js).
//
// __BUILD_ID__ lo pisa Vite en cada `npm run build` para que activate tire
// los caches viejos. No editar a mano.
// ============================================================================

const VERSION = "papasud-v2-__BUILD_ID__";
const SHELL = `${VERSION}-shell`;
const DATOS = `${VERSION}-datos`;

const BASE = ["/index.html", "/logos/papasud.svg"];

function esHtml(r) {
  const ct = (r && r.headers && r.headers.get("content-type")) || "";
  return ct.includes("text/html");
}

function esAsset(url) {
  return url.pathname.startsWith("/assets/") ||
    /\.(?:js|mjs|css|wasm|map|woff2?)$/.test(url.pathname);
}

function esNavegacion(req, url) {
  return req.mode === "navigate" || req.destination === "document" ||
    url.pathname === "/" || url.pathname === "/index.html";
}

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(SHELL)
      .then((c) => c.addAll(BASE).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil((async () => {
    const ks = await caches.keys();
    await Promise.all(
      ks.filter((k) => k !== SHELL && k !== DATOS).map((k) => caches.delete(k)));
    await self.clients.claim();
    // Las pestañas que quedaron en blanco (JS con MIME html) nunca corren el
    // bundle nuevo: hay que navegarlas desde acá, no esperar un listener en
    // main.jsx que no llegó a cargarse.
    const ventanas = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    await Promise.all(ventanas.map((c) => (c.navigate ? c.navigate(c.url) : Promise.resolve())));
  })());
});

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
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
          const cuerpo = await cacheada.blob();
          const h = new Headers(cacheada.headers);
          h.set("X-Desde-Cache", "1");
          return new Response(cuerpo, { status: 200, headers: h });
        })
    );
    return;
  }

  // --- HTML / SW: red primero, cache sólo si no hay señal -----------------
  if (esNavegacion(req, url) || url.pathname === "/sw.js") {
    e.respondWith(
      fetch(req)
        .then((r) => {
          if (r.ok && (url.pathname === "/sw.js" || esHtml(r))) {
            const paraReq = r.clone();
            const paraIndex = esHtml(r) ? r.clone() : null;
            caches.open(SHELL).then((c) => {
              c.put(req, paraReq);
              if (paraIndex) c.put("/index.html", paraIndex);
            });
          }
          return r;
        })
        .catch(() => {
          if (url.pathname === "/sw.js") return Promise.reject(new Error("sin sw"));
          return caches.match("/index.html");
        })
    );
    return;
  }

  // --- assets con hash: cache-first, jamás HTML disfrazado de JS ----------
  if (esAsset(url)) {
    e.respondWith(
      caches.match(req).then((hit) => {
        if (hit && !esHtml(hit)) return hit;
        return fetch(req).then((r) => {
          if (r.ok && !esHtml(r)) {
            const copia = r.clone();
            caches.open(SHELL).then((c) => c.put(req, copia));
          }
          return r;
        });
      })
    );
    return;
  }

  // --- resto del shell (logo, fuentes, favicon) ---------------------------
  e.respondWith(
    caches.match(req).then((hit) => {
      if (hit && !esHtml(hit)) return hit;
      return fetch(req).then((r) => {
        if (r.ok && !esHtml(r)) {
          const copia = r.clone();
          caches.open(SHELL).then((c) => c.put(req, copia));
        }
        return r;
      });
    })
  );
});
