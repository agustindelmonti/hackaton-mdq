// ============================================================================
// EL INTÉRPRETE QUE CORRE EN EL CELULAR — sin red, sin modelo, sin servidor.
// ----------------------------------------------------------------------------
// Es el gemelo en el cliente de `core/movimientos_nl.py`: el MISMO algoritmo
// determinista (número + unidad + lote o variedad + origen + destino), pero
// corriendo contra el snapshot local del stock.
//
// Existe por una sola razón: adentro de la cámara no hay señal, y el operario
// igual tiene que poder decir lo que movió. Con conexión, el backend interpreta
// con el modelo y entiende cualquier frase; sin conexión, esto entiende la
// frase típica del piso — que es la que se dice el 95% de las veces.
//
// LO QUE NO CAMBIA SIN CONEXIÓN: que el sistema no elija el lote por su cuenta.
// Si hay varios candidatos, los muestra y decide la persona. Y la disponibilidad
// se valida igual, con el último stock conocido, DICIENDO que es el último
// conocido. Al sincronizar se re-valida contra el real.
// ============================================================================

const KG_POR_BOLSON = 1000;

const UNIDADES = {
  bolson: KG_POR_BOLSON, bolsones: KG_POR_BOLSON, "bolsón": KG_POR_BOLSON,
  "big bag": KG_POR_BOLSON, bigbag: KG_POR_BOLSON, maxisaco: KG_POR_BOLSON,
  kilo: 1, kilos: 1, kg: 1, kgs: 1,
  tonelada: 1000, toneladas: 1000, t: 1000, tn: 1000,
  bolsa: 50, bolsas: 50,
};

const NUMEROS = {
  un: 1, una: 1, uno: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6,
  siete: 7, ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, trece: 13,
  catorce: 14, quince: 15, dieciseis: 16, diecisiete: 17, dieciocho: 18,
  diecinueve: 19, veinte: 20, veintiuno: 21, veintidos: 22, veintitres: 23,
  veinticuatro: 24, veinticinco: 25, veintiseis: 26, veintisiete: 27,
  veintiocho: 28, veintinueve: 29, treinta: 30, cuarenta: 40, cincuenta: 50,
  sesenta: 60, setenta: 70, ochenta: 80, noventa: 90, cien: 100,
};

const VERBOS = {
  traslado: ["pase", "pasamos", "movi", "movimos", "mande", "mandamos", "lleve",
             "llevamos", "traslade", "trasladamos", "bajamos", "subimos"],
  egreso: ["despache", "despachamos", "cargue", "cargamos", "salio", "salieron",
           "entregue", "entregamos"],
  ingreso: ["entro", "entraron", "ingrese", "ingresamos", "recibi", "recibimos",
            "llego", "llegaron"],
  descarte: ["descarte", "descartamos", "tire", "tiramos", "di de baja",
             "dimos de baja", "perdimos"],
};

const norm = (s) =>
  (s || "").toString().normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();

const escapar = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

function parsearCantidad(t) {
  const uds = Object.keys(UNIDADES).sort((a, b) => b.length - a.length).map(escapar).join("|");
  let m = t.match(new RegExp(`(\\d+(?:[.,]\\d+)?)\\s*(${uds})\\b`));
  if (m) return [parseFloat(m[1].replace(/\./g, "").replace(",", ".")), m[2]];
  const nums = Object.keys(NUMEROS).sort((a, b) => b.length - a.length).map(escapar).join("|");
  m = t.match(new RegExp(`\\b(${nums})\\s+(${uds})\\b`));
  if (m) return [NUMEROS[m[1]], m[2]];
  m = t.match(/\b(\d+(?:[.,]\d+)?)\b/);
  if (m) return [parseFloat(m[1].replace(/\./g, "").replace(",", ".")), null];
  return [null, null];
}

function detectarTipo(t) {
  for (const [tipo, verbos] of Object.entries(VERBOS)) {
    if (verbos.some((v) => t.includes(v))) return tipo;
  }
  return "traslado";
}

function ubicacionesMencionadas(t, ubicaciones) {
  // En castellano el orden es casi siempre origen → destino («de X al Y»), así
  // que la posición en la frase alcanza para ordenarlas.
  const hits = [];
  for (const u of ubicaciones) {
    const claves = [norm(u.id)];
    for (const w of norm(u.nombre).split(/\s+/)) {
      if (w.length > 3 && !["frigorifico", "galpon", "padres", "los", "del"].includes(w)) {
        claves.push(w);
      }
    }
    if (u.tipo === "galpon") claves.push("galpon");
    const pos = claves.map((k) => t.indexOf(k)).filter((i) => i >= 0);
    if (pos.length) hits.push([Math.min(...pos), u]);
  }
  hits.sort((a, b) => a[0] - b[0]);
  return hits.map(([, u]) => u);
}

/**
 * Interpreta una frase con el snapshot local. Devuelve EXACTAMENTE la misma
 * forma que `/api/movimientos/interpretar`, para que la pantalla no tenga que
 * saber si hubo red o no.
 */
export function interpretarLocal(texto, snapshot) {
  const t = norm(texto);
  const lotes = (snapshot && snapshot.lotes) || [];
  const ubicaciones = (snapshot && snapshot.ubicaciones) || [];
  const variedades = (snapshot && snapshot.variedades) || [];
  const clientes = (snapshot && snapshot.clientes) || [];

  const [cantidad, unidad] = parsearCantidad(t);
  let tipo = detectarTipo(t);
  const ubis = ubicacionesMencionadas(t, ubicaciones);

  let origen = null, destino = null;
  if (ubis.length >= 2) { origen = ubis[0]; destino = ubis[1]; }
  else if (ubis.length === 1) {
    const u = ubis[0];
    const clave = norm(u.nombre).split(/\s+/).pop();
    const antes = t.slice(0, Math.max(0, t.indexOf(clave)));
    if (/\b(al|a la|a|hacia|para)\s*$/.test(antes.trim().slice(-12))) destino = u;
    else origen = u;
  }

  // el lote: primero un rótulo explícito, después la variedad
  let loteTexto = null;
  const rot = t.match(/\b(ps-?\d{4,6}-?[a-z]{3}-?\d{2,3})\b/);
  if (rot) loteTexto = rot[1].toUpperCase();
  else {
    const v = variedades.find((x) => t.includes(norm(x.nombre)));
    if (v) loteTexto = v.nombre;
  }

  if (!destino) {
    const cli = clientes.find((c) =>
      norm(c.nombre).split(/\s+/).filter((w) => w.length > 4).some((w) => t.includes(w)));
    if (cli) { destino = { nombre: cli.nombre, cliente: true }; tipo = "egreso"; }
  }

  // --- candidatos: el sistema NO desempata solo -----------------------------
  const q = norm(loteTexto);
  let candidatos = [];
  if (q) {
    const exactos = lotes.filter((l) => norm(l.lote) === q || String(l.codigo) === q);
    candidatos = exactos.length
      ? exactos
      : lotes.filter((l) =>
          norm(l.lote).includes(q) || norm(l.variedad).includes(q) ||
          norm(l.descripcion).includes(q));
    // si dijo de dónde lo sacó, eso acota
    if (origen && candidatos.length > 1) {
      const acotados = candidatos.filter((l) => l.ubicacion_id === origen.id);
      if (acotados.length) candidatos = acotados;
    }
    candidatos = [...candidatos].sort((a, b) => Math.abs(b.stock) - Math.abs(a.stock)).slice(0, 8);
  }
  const lote = candidatos.length === 1 ? candidatos[0] : null;
  if (!origen && lote) {
    origen = ubicaciones.find((u) => u.id === lote.ubicacion_id) || null;
  }

  const kg = cantidad == null ? null
    : cantidad * (unidad ? (UNIDADES[unidad] || 1) : KG_POR_BOLSON);

  // --- la validación, con el ÚLTIMO STOCK CONOCIDO --------------------------
  let validacion = null;
  if (lote && kg) {
    const disp = Number(lote.disponible_kg ?? lote.stock ?? 0);
    validacion = kg > disp
      ? { ok: false, motivo: "sin_stock_suficiente", pedido_kg: kg,
          disponible_kg: disp, faltante_kg: Math.round((kg - disp) * 10) / 10,
          // Se marca como offline para que la pantalla lo diga: este número
          // puede estar viejo, y al sincronizar se vuelve a validar.
          offline: true }
      : { ok: true, offline: true };
  }

  const faltantes = [];
  if (!candidatos.length) faltantes.push("lote");
  else if (candidatos.length > 1) faltantes.push("cual_lote");
  if (kg == null) faltantes.push("cantidad");
  if (tipo !== "descarte" && !destino) faltantes.push("destino");

  return {
    texto,
    motor: "local",
    interpretacion: { tipo, lote_texto: loteTexto, cantidad, unidad,
                      origen_texto: origen?.nombre || null,
                      destino_texto: destino?.nombre || null,
                      confianza: faltantes.length ? "dudosa" : "clara",
                      kg_calculado: kg },
    propuesta: {
      tipo,
      codigo: lote?.codigo ?? null,
      lote: lote?.lote ?? null,
      descripcion: lote?.descripcion ?? null,
      kg: kg == null ? null : Math.round(kg * 10) / 10,
      bolsones: kg == null ? null : Math.round((kg / KG_POR_BOLSON) * 100) / 100,
      origen: origen?.nombre || null,
      origen_id: origen?.id || null,
      destino: destino?.nombre || null,
      nota: null,
    },
    candidatos: candidatos.map((c) => ({
      codigo: c.codigo, lote: c.lote, descripcion: c.descripcion,
      ubicacion: c.ubicacion, camara: c.camara, stock: c.stock,
    })),
    validacion,
    faltantes,
    listo: !faltantes.length && !!validacion?.ok,
  };
}
