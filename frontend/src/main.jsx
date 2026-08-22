import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

// --- MODO SIN CONEXIÓN ------------------------------------------------------
// El service worker hace que la app ABRA sin señal (adentro de una cámara
// frigorífica no hay red). La cola de movimientos vive en IndexedDB y se
// sincroniza sola cuando vuelve la conexión — ver lib/offline.js.
//
// SÓLO EN PRODUCCIÓN. En desarrollo los módulos llegan de /src sin hash en el
// nombre, así que el cache-first del shell los deja PEGADOS: se edita el
// código, se recarga, y sigue apareciendo la versión vieja. Costó descubrirlo
// una vez; que no vuelva a pasar el día de una demo.
if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js", { updateViaCache: "none" })
      .then((reg) => { reg.update().catch(() => {}); })
      .catch(() => {
        // Sin service worker la app sigue funcionando con red; sólo se pierde
        // el arranque offline. No es motivo para romper nada.
      });
  });
} else if ("serviceWorker" in navigator) {
  // Si quedó uno registrado de una corrida anterior, se va con sus caches.
  navigator.serviceWorker.getRegistrations()
    .then((rs) => rs.forEach((r) => r.unregister()))
    .catch(() => {});
  if (window.caches) {
    caches.keys().then((ks) => ks.forEach((k) => {
      if (k.startsWith("papasud-")) caches.delete(k);
    })).catch(() => {});
  }
}
