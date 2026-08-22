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
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {
      // Sin service worker la app sigue funcionando con red; sólo se pierde el
      // arranque offline. No es motivo para romper nada.
    });
  });
}
