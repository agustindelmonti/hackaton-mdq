// ============================================================
// Papasud — núcleo determinístico compartido.
//
// Todo lo que hay acá es lógica pura sobre los datos de data.js: sin
// LLM, sin backend, sin DOM (salvo escapeHtml, que usa un <div>
// desechable sólo para escapar texto). Lo cargan tanto el prototipo
// mobile (prototype/app.js) como el desktop (desktop/app.js) — así
// "cuánto stock tiene el lote 17" o "esto excede la merma" se computa
// en un solo lugar y ambas pantallas nunca pueden mostrar números
// distintos para el mismo dato.
// ============================================================

// ---------- Utilidades ----------
function escapeHtml(s) {
  const div = document.createElement('div');
  div.textContent = s == null ? '' : String(s);
  return div.innerHTML;
}
function fmtKg(kg) {
  return Math.round(kg).toLocaleString('es-AR') + ' kg';
}
function normaliza(s) {
  return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim();
}
function fechaCorta(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit', year: '2-digit' });
}
function diasDesde(iso) {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86400000);
}

// ---------- Stock derivado del libro append-only ----------
function stockPorLoteUbic(loteId, ubicacionId) {
  let kg = 0;
  for (const m of MOVIMIENTOS) {
    if (m.loteId !== loteId) continue;
    if (m.destinoId === ubicacionId) kg += m.kg;
    if (m.origenId === ubicacionId) kg -= m.kg;
  }
  return kg;
}
function stockTotalUbicacion(ubicacionId) {
  let kg = 0;
  for (const m of MOVIMIENTOS) {
    if (m.destinoId === ubicacionId) kg += m.kg;
    if (m.origenId === ubicacionId) kg -= m.kg;
  }
  return kg;
}
function lotesConStockEn(ubicacionId) {
  const ids = new Set();
  MOVIMIENTOS.forEach(m => {
    if (m.destinoId === ubicacionId || m.origenId === ubicacionId) ids.add(m.loteId);
  });
  return [...ids].filter(id => stockPorLoteUbic(id, ubicacionId) > 0);
}
function ubicacionActualDeLote(loteId) {
  for (const u of UBICACIONES) {
    if (stockPorLoteUbic(loteId, u.id) > 0) return u;
  }
  return null;
}
function stockTotalLote(loteId) {
  return UBICACIONES.reduce((sum, u) => sum + Math.max(0, stockPorLoteUbic(loteId, u.id)), 0);
}
function movimientosDeLote(loteId) {
  return MOVIMIENTOS.filter(m => m.loteId === loteId).sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
}
function ultimoIngresoA(loteId, ubicacionId) {
  const movs = MOVIMIENTOS.filter(m => m.loteId === loteId && m.destinoId === ubicacionId)
    .sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
  return movs[0] || null;
}

// ---------- Discrepancia neta de merma (F3.9) ----------
// Cálculo compartido entre el render en vivo y el registro persistido
// (registrarConteo) — un solo lugar decide qué es "esperado" y qué
// "excede", para que la auditoría y la pantalla nunca puedan divergir.
function calcularDiscrepancia(loteId, kgContado) {
  const ubic = ubicacionActualDeLote(loteId);
  if (!ubic) return null;
  const declarado = stockPorLoteUbic(loteId, ubic.id);
  const ingreso = ultimoIngresoA(loteId, ubic.id);
  const dias = ingreso ? diasDesde(ingreso.fecha) : 0;
  const pct = mermaEsperadaPct(dias);
  const esperado = declarado * (1 - pct / 100);
  const tolerancia = declarado * 0.01;
  const result = { ubic, declarado, ingreso, dias, pct, esperado, tolerancia };
  if (!isNaN(kgContado)) {
    result.delta = kgContado - esperado;
    result.excede = Math.abs(result.delta) > tolerancia;
  }
  return result;
}

// ============================================================
// Redacción de la hipótesis de discrepancia (F3.10).
//
// CÓMO FUNCIONA ACÁ (prototipo, sin backend/LLM):
// Esta función es una plantilla determinística en JS que arma la
// frase interpolando los campos reales del candidato (fecha, kg,
// origen, transcripción) — no hay generación de lenguaje de verdad,
// sólo string templating sobre datos que ya calculó otra función.
//
// CÓMO DEBERÍA FUNCIONAR EN LA APP REAL (con LLM):
// El candidato/candidatos ya viene filtrado y rankeado por la capa
// determinística de arriba (quien llama a esta función: sólo
// movimientos con salida sin espejo en destino o `confianza:
// 'dudosa'`, nunca la tabla de movimientos entera). Esa lista acotada
// — ya formateada como strings (fechas, kg, ubicaciones) — es lo
// único que se le pasaría a un LLM, con una tool/prompt que le exige:
//   1. Narrar en castellano llano SÓLO sobre esos movimientos.
//   2. Copiar fecha/kg/ubicación verbatim — prohibido reformatear,
//      redondear, o inventar un movimiento que no esté en la lista.
//   3. Si no hay candidatos, decir explícitamente "no encontré una
//      causa probable" en vez de inventar una.
// El LLM nunca decide QUÉ es candidato (eso ya lo resolvió el filtro
// determinístico) ni recalcula ningún número — sólo redacta la frase
// a partir de los datos que ya le llegaron resueltos. Reemplazar esta
// función por una llamada real a un LLM no debería tocar nada de
// quien la llama: la interfaz (candidatos in, texto out) es la misma,
// sólo cambia quién arma la oración.
// ============================================================
function redactarHipotesisMerma(candidatos) {
  if (!candidatos.length) return null;

  // Rankeo simple: preferimos una salida sin espejo en destino (más
  // accionable) sobre un movimiento sólo marcado como dudoso; a
  // igualdad de tipo, el de mayor kg (mayor impacto en el saldo).
  const principal = [...candidatos].sort((a, b) => {
    const tipoA = a.origenId && !a.destinoId ? 1 : 0;
    const tipoB = b.origenId && !b.destinoId ? 1 : 0;
    return tipoB - tipoA || b.kg - a.kg;
  })[0];

  let frase;
  if (principal.origenId && !principal.destinoId) {
    const origenNombre = UBICACIONES.find(u => u.id === principal.origenId).nombre;
    frase = `Un movimiento del ${fechaCorta(principal.fecha)} posiblemente no se registró en destino — salieron ${fmtKg(principal.kg)} de ${origenNombre} y no hay ninguna entrada espejo para ese egreso en el libro.`;
  } else {
    frase = `El movimiento del ${fechaCorta(principal.fecha)} quedó cargado con confianza dudosa` +
      (principal.transcripcion ? ` — "${escapeHtml(principal.transcripcion)}"` : '') +
      ` — podría explicar la diferencia.`;
  }

  const resto = candidatos.length - 1;
  if (resto > 0) frase += ` Hay ${resto} movimiento${resto === 1 ? '' : 's'} más para revisar en la lista de abajo.`;
  return frase;
}

// Candidatos a discrepancia para un lote: movimientos con salida sin
// espejo en destino, o cargados con confianza dudosa. Extraído a una
// función porque tanto el prototipo mobile (Conteo) como el desktop
// (cola de discrepancias) necesitan el mismo filtro antes de narrar.
function candidatosDiscrepancia(loteId) {
  return MOVIMIENTOS.filter(m => m.loteId === loteId && ((m.origenId && !m.destinoId) || m.confianza === 'dudosa'));
}
