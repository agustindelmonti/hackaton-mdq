// ============================================================================
// EL BACKUP GRABADO DE LA DEMO.
// ----------------------------------------------------------------------------
// Si el sábado se cae el wifi, se cuelga el gateway o el proyector no toma la
// notebook, esto es lo que se muestra. No es un video de marketing: es la MISMA
// app corriendo contra el MISMO backend, manejada por un guion, para que lo que
// se ve grabado sea exactamente lo que pasa en vivo.
//
// Sale un .webm por tramo en docs/demo/. El guion son los cinco minutos:
//
//   1. El panorama del dueño            (qué está pasando hoy)
//   2. El mapa                          (dónde está cada kilo · los que faltan)
//   3. La conciliación                  (la hipótesis, con su evidencia)
//   4. Un movimiento por texto libre    (N01 · lenguaje → transacción)
//   5. La carpeta de exportación        (N03 · el freno del remito y el PDF)
//   6. El equipo                        (Ángela propone · se asigna a Néstor)
//   7. El celular de Néstor             (le llegó · la marca hecha)
//
// Uso:  node demo-grabada.mjs            (todo)
//       TRAMO=5 node demo-grabada.mjs    (sólo uno, para re-grabarlo)
// ============================================================================
import { chromium } from "playwright";
import fs from "fs";

const BASE = process.env.BASE || "http://localhost:5210";
const SALIDA = "../docs/demo";
const CRED = {
  ernesto: "brote-8039", cecilia: "camara-1440", ruben: "semilla-9654",
  marcos: "campania-9443", dalia: "spunta-9785", nestor: "spunta-5546",
};
const SOLO = process.env.TRAMO ? Number(process.env.TRAMO) : null;

fs.mkdirSync(SALIDA, { recursive: true });
const browser = await chromium.launch();

/** Un tramo = un contexto con su propio video. */
async function tramo(n, titulo, { mobile = false, usuario = "ernesto" } = {}, guion) {
  if (SOLO && SOLO !== n) return;
  const size = mobile ? { width: 390, height: 844 } : { width: 1440, height: 900 };
  const ctx = await browser.newContext({
    viewport: size,
    recordVideo: { dir: SALIDA, size },
    acceptDownloads: true,
    isMobile: mobile,
    hasTouch: mobile,
    deviceScaleFactor: 1,
  });
  const p = await ctx.newPage();
  await entrar(p, usuario);
  try {
    await guion(p);
  } catch (e) {
    console.log(`  ! tramo ${n} cortó:`, String(e).split("\n")[0].slice(0, 120));
  }
  await p.waitForTimeout(1400);
  const video = p.video();
  await ctx.close();
  const destino = `${SALIDA}/${String(n).padStart(2, "0")}-${titulo}.webm`;
  if (video) {
    await video.saveAs(destino);
    await video.delete().catch(() => {});
    console.log(`✓ ${destino}`);
  }
}

async function entrar(p, usuario) {
  await p.goto(BASE, { waitUntil: "domcontentloaded" });
  await p.waitForSelector("input", { timeout: 30000 }).catch(() => {});
  if (await p.locator("input").first().isVisible().catch(() => false)) {
    await p.locator("input").first().type(usuario, { delay: 55 });
    await p.locator('input[type="password"]').first().type(CRED[usuario], { delay: 35 });
    await p.waitForTimeout(400);
    await p.keyboard.press("Enter");
  }
  await p.waitForFunction(
    () => !/Leyendo tu negocio|Reading your/.test(document.body.innerText),
    null, { timeout: 60000 }).catch(() => {});
  await p.waitForTimeout(2200);
}

/** Ir a una sección por el nombre del ítem del menú. */
async function ir(p, nombre, espera = 3500) {
  await p.getByRole("button", { name: new RegExp(nombre, "i") }).first().click();
  await p.waitForTimeout(espera);
}

/** Lee: baja despacio para que se pueda seguir en el video. */
async function leer(p, px = 600, pasos = 4) {
  const [w, h] = [p.viewportSize().width, p.viewportSize().height];
  await p.mouse.move(Math.round(w / 2), Math.round(h / 2));
  for (let i = 0; i < pasos; i++) {
    await p.mouse.wheel(0, px / pasos);
    await p.waitForTimeout(700);
  }
}

// 1 · EL PANORAMA -----------------------------------------------------------
await tramo(1, "el-panorama-del-dueno", {}, async (p) => {
  await ir(p, "^Inicio$");
  await leer(p, 900, 5);
  await p.waitForTimeout(1200);
});

// 2 · EL MAPA ---------------------------------------------------------------
await tramo(2, "el-mapa-de-la-operacion", {}, async (p) => {
  await ir(p, "mapa de la operaci", 5000);
  await p.waitForSelector(".react-flow__node", { timeout: 20000 }).catch(() => {});
  await p.waitForTimeout(2500);
  // el hallazgo que ilumina el camino de los kilos que salieron y no llegaron
  await p.getByRole("button", { name: /MOV-2026-0912/i }).first().click().catch(() => {});
  await p.waitForTimeout(3200);
  await p.locator('[data-id="ubi_chapadmalal"]').first().click().catch(() => {});
  await p.waitForTimeout(3500);
});

// 3 · LA CONCILIACIÓN -------------------------------------------------------
await tramo(3, "la-hipotesis-con-su-evidencia", {}, async (p) => {
  await ir(p, "^Conciliaci", 4000);
  await leer(p, 700, 4);
  await p.waitForTimeout(1500);
});

// 4 · EL MOVIMIENTO POR TEXTO LIBRE -----------------------------------------
await tramo(4, "un-traslado-dicho-en-criollo", {}, async (p) => {
  await ir(p, "^Movimientos$", 4000);
  const caja = p.locator("textarea, input[type=text]").first();
  await caja.click().catch(() => {});
  await caja.type("pasé dieciocho bolsones de Spunta de Ruta 226 al galpón",
                  { delay: 42 }).catch(() => {});
  await p.waitForTimeout(900);
  await p.keyboard.press("Enter").catch(() => {});
  await p.waitForTimeout(4500);
  await leer(p, 500, 3);
});

// 5 · LA CARPETA DE EXPORTACIÓN ---------------------------------------------
await tramo(5, "la-carpeta-de-exportacion", { usuario: "cecilia" }, async (p) => {
  await ir(p, "^Exportaci", 4500);
  await p.waitForTimeout(1200);
  await p.locator("text=Factura proforma").first().click().catch(() => {});
  await p.waitForTimeout(3000);
  await leer(p, 800, 4);
  await p.locator("text=Certificado Fitosanitario").first().click().catch(() => {});
  await p.waitForTimeout(3000);
  await leer(p, 700, 4);
});

// 6 · EL EQUIPO: ÁNGELA PROPONE, EL DUEÑO ASIGNA ----------------------------
await tramo(6, "angela-propone-y-el-dueno-asigna", {}, async (p) => {
  await ir(p, "^Equipo$", 5000);
  await leer(p, 1100, 5);
  const btn = p.getByRole("button", { name: /Asignar a /i }).first();
  if (await btn.count()) {
    await btn.click();
    await p.waitForTimeout(3200);
  }
  await leer(p, 500, 3);
});

// 7 · EL CELULAR DE NÉSTOR --------------------------------------------------
await tramo(7, "le-llego-al-celular-de-nestor", { mobile: true, usuario: "nestor" },
  async (p) => {
    await p.waitForTimeout(1800);
    await leer(p, 900, 5);
    await p.waitForTimeout(2500);
  });

await browser.close();
console.log("\nlisto · los tramos quedaron en docs/demo/");
