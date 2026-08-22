// ============================================================
// Papasud — prototipo de UI. Núcleo determinístico en JS plano;
// no hay LLM real acá (no hay backend) — el parser de dictado
// es un stand-in simple para la extracción por tool forzada que
// tendría la app real. Nada se inventa: campo ausente -> null +
// confianza 'dudosa'.
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

// ---------- Resolución determinística de identificadores (fuzzy) ----------
function scoreUbicacion(texto, ubic) {
  const t = normaliza(texto);
  const candidatos = [ubic.nombre, ubic.apodo, ubic.localidad].map(normaliza);
  let score = 0;
  candidatos.forEach(c => {
    if (!c) return;
    if (t.includes(c) || c.includes(t)) score = Math.max(score, c.length >= 4 ? 0.95 : 0.6);
    else {
      const tokens = c.split(' ');
      tokens.forEach(tok => { if (tok.length > 3 && t.includes(tok)) score = Math.max(score, 0.7); });
    }
  });
  return score;
}
function resolverUbicacion(texto) {
  const ranked = UBICACIONES.map(u => ({ ubic: u, score: scoreUbicacion(texto, u) }))
    .filter(r => r.score > 0)
    .sort((a, b) => b.score - a.score);
  if (ranked.length === 0) return { match: null, candidatos: [], confianza: 'dudosa' };
  if (ranked[0].score >= 0.9 && (ranked.length === 1 || ranked[0].score - ranked[1].score > 0.15)) {
    return { match: ranked[0].ubic, candidatos: ranked, confianza: 'alta' };
  }
  return { match: null, candidatos: ranked.slice(0, 3), confianza: 'dudosa' };
}
function resolverLote(numeroTexto) {
  const num = String(numeroTexto).trim();
  if (num === '42') { // alias narrativo de demo, ver data.js
    return { match: LOTE_BY_ID[LOTE_VOZ_DEMO_ID], candidatos: [], confianza: 'alta' };
  }
  if (LOTE_BY_ID[num]) return { match: LOTE_BY_ID[num], candidatos: [], confianza: 'alta' };
  // candidatos cercanos por número
  const cercanos = LOTES
    .map(l => ({ lote: l, score: 1 / (1 + Math.abs(parseInt(l.id) - parseInt(num || '0'))) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, 3);
  return { match: null, candidatos: cercanos, confianza: 'dudosa' };
}

// ---------- Parser de dictado (stand-in de la tool forzada) ----------
function parseDictado(textoOriginal) {
  let texto = ' ' + normaliza(textoOriginal) + ' ';
  const bolsonesMatch = texto.match(/(\d+)\s*bolson/);
  const loteMatch = texto.match(/lote\s*(\d+)/);
  texto = texto.replace(/lote\s*\d+/, ' '); // saca ruido antes de separar origen/destino

  const odMatch = texto.match(/(?:del|desde)\s+(.+?)\s+(?:al|hacia|a)\s+(.+?)(?:$|\.|,)/);

  const cantidadBolsones = bolsonesMatch ? parseInt(bolsonesMatch[1]) : null;
  const kg = cantidadBolsones ? cantidadBolsones * KG_POR_BOLSON : null;

  const loteInfo = loteMatch ? resolverLote(loteMatch[1]) : { match: null, candidatos: [], confianza: 'dudosa' };
  const origenInfo = odMatch ? resolverUbicacion(odMatch[1]) : { match: null, candidatos: [], confianza: 'dudosa' };
  const destinoInfo = odMatch ? resolverUbicacion(odMatch[2]) : { match: null, candidatos: [], confianza: 'dudosa' };

  return {
    transcripcion: textoOriginal,
    loteTextoOriginal: loteMatch ? loteMatch[1] : null,
    lote: loteInfo,
    kg,
    kgConfianza: kg ? 'alta' : 'dudosa',
    origen: origenInfo,
    destino: destinoInfo,
  };
}

// ============================================================
// ---------------------- NAVEGACIÓN --------------------------
// ============================================================
let viewStack = ['tablero'];
let ctx = {}; // parámetros de la vista actual (ubicacionId, loteId...)

const TITLES = {
  tablero: ['Tablero', '4 ubicaciones · en tiempo real'],
  ubicacion: null, // dinámico
  lote: null,
  voz: ['Captura por voz', 'Dictá un movimiento de stock'],
  conteo: ['Conteo físico', 'Discrepancia neta de merma'],
  lotes: ['Catálogo de lotes', 'Linaje y registro'],
  exportacion: ['Exportación', 'Documentación — cierre, DEMO sin valor legal'],
};

function navTo(view, params) {
  ctx = params || {};
  viewStack = [view];
  renderView(view);
}
function pushView(view, params) {
  ctx = params || {};
  viewStack.push(view);
  renderView(view);
}
function goBack() {
  if (viewStack.length > 1) viewStack.pop();
  renderView(viewStack[viewStack.length - 1]);
}

function renderView(view) {
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.dataset.view === view));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.toggle('active', b.dataset.nav === view));
  document.getElementById('backBtn').style.display = viewStack.length > 1 ? '' : 'none';

  if (view === 'tablero') { setTitle('Tablero', '4 ubicaciones · en tiempo real'); renderTablero(); }
  if (view === 'ubicacion') renderUbicacion(ctx.ubicacionId);
  if (view === 'lote') renderLoteDetalle(ctx.loteId);
  if (view === 'voz') { setTitle('Captura por voz', 'Dictá un movimiento de stock'); }
  if (view === 'conteo') { setTitle('Conteo físico', 'Discrepancia neta de merma'); initConteoView(); }
  if (view === 'lotes') { setTitle('Catálogo de lotes', 'Linaje y registro'); initLotesView(); }
  if (view === 'exportacion') { setTitle('Exportación', 'Documentación — cierre, DEMO sin valor legal'); initExportacionView(ctx.loteId); }
}
function setTitle(title, subtitle) {
  document.getElementById('topTitle').textContent = title;
  document.getElementById('topSubtitle').textContent = subtitle;
}

// ============================================================
// ---------------------- TABLERO ------------------------------
// ============================================================
function renderTablero() {
  const grid = document.getElementById('ubicGrid');
  grid.innerHTML = UBICACIONES.map(u => {
    const kg = stockTotalUbicacion(u.id);
    const nLotes = lotesConStockEn(u.id).length;
    const tipoLabel = u.tipo === 'frigorifico' ? 'Frigorífico' : 'Galpón';
    return `
      <div class="ubic-card" onclick="pushView('ubicacion', {ubicacionId:'${u.id}'})">
        <div>
          <div class="tipo-tag">${tipoLabel}</div>
          <div class="nombre">${u.nombre}</div>
        </div>
        <div>
          <div class="stat-big tabular">${fmtKg(kg)}</div>
          <div class="lote-count">${nLotes} lote${nLotes === 1 ? '' : 's'}</div>
        </div>
      </div>`;
  }).join('');

  // Feed de alertas: movimientos con confianza dudosa sin resolver
  const dudosos = MOVIMIENTOS.filter(m => m.confianza === 'dudoso' || m.confianza === 'dudosa');
  const feed = document.getElementById('alertsFeed');
  if (dudosos.length === 0) {
    feed.innerHTML = '<div class="empty-state">Sin alertas pendientes.</div>';
  } else {
    feed.innerHTML = dudosos.map(m => {
      const lote = LOTE_BY_ID[m.loteId];
      return `
        <div class="alert-box dudoso">
          <div class="alert-title">🟡 Movimiento dudoso — Lote ${lote ? lote.nroLote : m.loteId}</div>
          <div class="alert-body">"${escapeHtml(m.transcripcion || 'sin transcripción')}" — falta confirmar destino. Registrado ${fechaCorta(m.fecha)}.</div>
        </div>`;
    }).join('');
  }
}

// ============================================================
// ---------------------- UBICACIÓN ----------------------------
// ============================================================
function renderUbicacion(ubicacionId) {
  const u = UBICACIONES.find(x => x.id === ubicacionId);
  setTitle(u.nombre, `${u.localidad}, ${u.provincia}`);
  document.getElementById('ubicDetailHeader').innerHTML = `
    <div class="stat-big tabular">${fmtKg(stockTotalUbicacion(u.id))}</div>
    <div style="color:var(--color-text-dim); font-size:12.5px; margin-top:2px;">stock declarado total, ${lotesConStockEn(u.id).length} lotes activos</div>`;

  const list = document.getElementById('ubicLoteList');
  const loteIds = lotesConStockEn(u.id);
  if (loteIds.length === 0) {
    list.innerHTML = '<div class="empty-state">No hay lotes con stock acá.</div>';
    return;
  }
  list.innerHTML = loteIds.map(id => {
    const lote = LOTE_BY_ID[id];
    const sub = SUBCATEGORIAS.find(s => s.id === lote.subcategoria);
    const kg = stockPorLoteUbic(id, u.id);
    return `
      <div class="card tappable" onclick="pushView('lote', {loteId:'${id}'})">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:700; font-size:14.5px;">Lote ${lote.nroLote}</div>
            <div style="font-size:12px; color:var(--color-text-dim); margin-top:2px;">${VARIEDADES.find(v=>v.id===lote.variedadId).nombre} · ${sub.nombre}</div>
          </div>
          <div class="stat-big tabular" style="font-size:17px;">${fmtKg(kg)}</div>
        </div>
      </div>`;
  }).join('');
}

// ============================================================
// ---------------------- LOTE / REMITO -------------------------
// ============================================================
function renderLoteDetalle(loteId) {
  const lote = LOTE_BY_ID[loteId];
  const sub = SUBCATEGORIAS.find(s => s.id === lote.subcategoria);
  const variedad = VARIEDADES.find(v => v.id === lote.variedadId);
  const ubic = ubicacionActualDeLote(loteId);

  setTitle(`Lote ${lote.nroLote}`, sub.categoria);
  document.getElementById('loteId').textContent = `Lote ${lote.nroLote}`;
  document.getElementById('loteCat').textContent =
    (sub.id === 'registrada' ? 'Categoría: Certificada – Registrada · Generación: G3' : `${sub.categoria} – ${sub.nombre}`);
  document.getElementById('loteVariedad').textContent = variedad.nombre;
  document.getElementById('loteUbic').textContent = ubic ? ubic.nombre : '— sin stock activo —';
  document.getElementById('loteEstimadoTag').innerHTML = '';

  // merma neta esperada respecto a la ubicación actual
  let stockNeto = stockTotalLote(loteId);
  if (ubic) {
    const ingreso = ultimoIngresoA(loteId, ubic.id);
    if (ingreso) {
      const dias = diasDesde(ingreso.fecha);
      const pct = mermaEsperadaPct(dias);
      stockNeto = stockPorLoteUbic(loteId, ubic.id) * (1 - pct / 100);
    }
  }
  document.getElementById('loteStock').textContent = fmtKg(stockNeto);

  // Genealogía
  const chain = [];
  let cur = lote;
  while (cur) { chain.unshift(cur); cur = cur.lotePadreId ? LOTE_BY_ID[cur.lotePadreId] : null; }
  document.getElementById('loteLinaje').innerHTML = chain.map(l => {
    const s = SUBCATEGORIAS.find(x => x.id === l.subcategoria);
    const isSelf = l.id === lote.id;
    return `
      <div class="linaje-node ${isSelf ? 'self' : ''}">
        <div>
          <div class="ln-sub">${s.nombre} ${isSelf ? '(este lote)' : ''}</div>
          <div class="ln-meta">Lote ${l.nroLote} · ${l.zonaProduccion} · cosecha ${l.anioCosecha}</div>
        </div>
      </div>`;
  }).join('');

  // Movimientos
  const movs = movimientosDeLote(loteId);
  const movsHtml = movs.length === 0 ? '<div class="empty-state">Sin movimientos registrados.</div>' : movs.map(m => {
    const origen = m.origenId ? UBICACIONES.find(u => u.id === m.origenId).nombre : 'Ingreso / cosecha';
    const destino = m.destinoId ? UBICACIONES.find(u => u.id === m.destinoId).nombre : 'Egreso / despacho';
    const isOut = !!m.origenId && m.confirmadoPor;
    return `
      <div class="mov-item">
        <div>
          <div class="mov-main">${origen} → ${destino}</div>
          <div class="mov-sub">${fechaCorta(m.fecha)} · <span class="badge-src">${m.fuente}</span> · ${m.usuario}</div>
        </div>
        <div class="mov-kg ${m.origenId ? 'out' : 'in'} tabular">${m.origenId ? '−' : '+'}${fmtKg(m.kg)}</div>
      </div>`;
  }).join('');
  document.getElementById('loteMovs').innerHTML = movsHtml;

  document.getElementById('remitoResult').innerHTML = '';
  document.getElementById('remitoKg').dataset.loteId = loteId;
}

function intentarRemito() {
  const loteId = document.getElementById('remitoKg').dataset.loteId;
  const kgPedido = parseFloat(document.getElementById('remitoKg').value) || 0;
  const ubic = ubicacionActualDeLote(loteId);
  const resultEl = document.getElementById('remitoResult');

  if (!ubic) {
    resultEl.innerHTML = `<div class="alert-box error"><div class="alert-title">🔴 Sin stock</div><div class="alert-body">Este lote no tiene stock activo en ninguna ubicación.</div></div>`;
    return;
  }

  const declarado = stockPorLoteUbic(loteId, ubic.id);
  const ingreso = ultimoIngresoA(loteId, ubic.id);
  const dias = ingreso ? diasDesde(ingreso.fecha) : 0;
  const pct = mermaEsperadaPct(dias);
  const disponibleNeto = declarado * (1 - pct / 100);

  const movsComponentes = MOVIMIENTOS.filter(m => m.loteId === loteId && (m.origenId === ubic.id || m.destinoId === ubic.id));

  if (kgPedido > disponibleNeto) {
    resultEl.innerHTML = `
      <div class="alert-box error">
        <div class="alert-title">🔴 Bloqueado — stock insuficiente</div>
        <div class="alert-body">Se pidieron <strong class="tabular">${fmtKg(kgPedido)}</strong> pero el stock verificado (neto de merma esperada) en ${ubic.nombre} es de <strong class="tabular">${fmtKg(disponibleNeto)}</strong>.</div>
        <div class="section-label" style="margin:6px 0 2px;">Movimientos que componen el saldo</div>
        <div class="evidence-list">
          ${movsComponentes.map(m => `
            <div class="evidence-item">
              <span>${m.origenId === ubic.id ? 'Salida' : 'Entrada'} · ${fechaCorta(m.fecha)}</span>
              <span class="tabular mov-kg ${m.origenId === ubic.id ? 'out' : 'in'}">${m.origenId === ubic.id ? '−' : '+'}${fmtKg(m.kg)}</span>
            </div>`).join('')}
        </div>
      </div>`;
  } else {
    resultEl.innerHTML = `
      <div class="alert-box confirmado">
        <div class="alert-title">🟢 Remito habilitado</div>
        <div class="alert-body">Stock verificado suficiente. Documento de tránsito: <strong>DTV-e</strong>${kgPedido >= 4500 ? ' + <strong>COT de ARBA</strong> (supera 4.500 kg)' : ''}.</div>
      </div>`;
  }
}

// ============================================================
// ---------------------- VOZ -----------------------------------
// ============================================================
let recognizing = false;
let audioCtx, analyser, micStream, ampRAF;
let parsedActual = null;

function ensureAmpBars() {
  const wrap = document.getElementById('ampBars');
  if (wrap.children.length) return;
  for (let i = 0; i < 22; i++) {
    const bar = document.createElement('div');
    bar.className = 'bar';
    bar.style.height = '4px';
    wrap.appendChild(bar);
  }
}
ensureAmpBars();

function setAmpHeights(values) {
  const bars = document.querySelectorAll('#ampBars .bar');
  bars.forEach((b, i) => { b.style.height = Math.max(4, values[i % values.length]) + 'px'; });
}

function startFakeAmplitude() {
  stopAmplitude();
  ampRAF = setInterval(() => {
    const vals = Array.from({ length: 22 }, () => 4 + Math.random() * 30);
    setAmpHeights(vals);
  }, 90);
}
function stopAmplitude() {
  if (ampRAF) { clearInterval(ampRAF); ampRAF = null; }
  if (audioCtx) { try { audioCtx.close(); } catch (e) {} audioCtx = null; }
  if (micStream) { micStream.getTracks().forEach(t => t.stop()); micStream = null; }
  setAmpHeights(Array(22).fill(4));
}

async function startRealAmplitude() {
  try {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioCtx.createMediaStreamSource(micStream);
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 64;
    source.connect(analyser);
    const data = new Uint8Array(analyser.frequencyBinCount);
    function tick() {
      if (!recognizing) return;
      analyser.getByteFrequencyData(data);
      const vals = Array.from(data).slice(0, 22).map(v => 4 + (v / 255) * 34);
      setAmpHeights(vals);
      ampRAF = requestAnimationFrame(tick);
    }
    tick();
    return true;
  } catch (e) {
    return false;
  }
}

function toggleMic() {
  if (recognizing) { stopMic(); return; }
  startMic();
}

let recognition = null;
async function startMic() {
  recognizing = true;
  document.getElementById('micBtn').classList.add('listening');
  document.getElementById('micHint').textContent = 'Escuchando… hablá con naturalidad';
  document.getElementById('transcriptBox').classList.remove('empty');
  document.getElementById('transcriptBox').textContent = '…';

  const gotMic = await startRealAmplitude();
  if (!gotMic) startFakeAmplitude();

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SR) {
    recognition = new SR();
    recognition.lang = 'es-AR';
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (ev) => {
      let text = '';
      for (let i = 0; i < ev.results.length; i++) text += ev.results[i][0].transcript;
      document.getElementById('transcriptBox').textContent = text;
      const last = ev.results[ev.results.length - 1];
      if (last.isFinal) handleTranscriptFinal(text);
    };
    recognition.onerror = () => { document.getElementById('micHint').textContent = 'No se pudo acceder al micrófono — probá el ejemplo de abajo.'; };
    recognition.onend = () => { if (recognizing) stopMic(); };
    try { recognition.start(); } catch (e) {}
  } else {
    document.getElementById('micHint').textContent = 'Este navegador no soporta Web Speech API — probá el ejemplo de abajo.';
  }
}
function stopMic() {
  recognizing = false;
  document.getElementById('micBtn').classList.remove('listening');
  document.getElementById('micHint').textContent = 'Mantené presionado o tocá para dictar en castellano';
  if (recognition) { try { recognition.stop(); } catch (e) {} recognition = null; }
  stopAmplitude();
}

function simulateDictation(text) {
  stopMic();
  const box = document.getElementById('transcriptBox');
  box.classList.remove('empty');
  box.textContent = '';
  startFakeAmplitude();
  let i = 0;
  const iv = setInterval(() => {
    box.textContent = text.slice(0, i);
    i += 3;
    if (i > text.length) {
      clearInterval(iv);
      stopAmplitude();
      box.textContent = text;
      handleTranscriptFinal(text);
    }
  }, 18);
}

function handleTranscriptFinal(text) {
  parsedActual = parseDictado(text);
  renderParsedCard();
}

function chipClass(conf) { return conf === 'alta' ? 'inferido' : 'dudoso'; }

function renderParsedCard() {
  const p = parsedActual;
  const wrap = document.getElementById('parsedCardWrap');
  if (!p) { wrap.innerHTML = ''; return; }

  const loteLabel = p.lote.match ? `Lote ${p.lote.match.nroLote}` : (p.loteTextoOriginal ? `"${escapeHtml(p.loteTextoOriginal)}" — sin resolver` : 'no dictado');
  const kgLabel = p.kg ? fmtKg(p.kg) : 'no dictado';
  const origenLabel = p.origen.match ? p.origen.match.nombre : 'sin resolver';
  const destinoLabel = p.destino.match ? p.destino.match.nombre : 'sin resolver';

  let candidatosHtml = '';
  const needsPicker = (!p.lote.match && p.lote.candidatos.length) ||
    (!p.origen.match && p.origen.candidatos.length) ||
    (!p.destino.match && p.destino.candidatos.length);

  if (!p.lote.match && p.lote.candidatos.length) {
    candidatosHtml += `<div class="section-label" style="margin-top:12px;">No reconozco ese lote — ¿cuál es?</div><div class="candidate-list">` +
      p.lote.candidatos.map(c => `<div class="candidate-item" onclick="pickLoteCandidato('${c.lote.id}')"><span>Lote ${c.lote.nroLote}</span><span class="score">${VARIEDADES.find(v=>v.id===c.lote.variedadId).nombre}</span></div>`).join('') + `</div>`;
  }
  if (!p.origen.match && p.origen.candidatos.length) {
    candidatosHtml += `<div class="section-label" style="margin-top:12px;">¿Cuál es el origen?</div><div class="candidate-list">` +
      p.origen.candidatos.map(c => `<div class="candidate-item" onclick="pickUbicCandidato('origen','${c.ubic.id}')"><span>${c.ubic.nombre}</span><span class="score">${Math.round(c.score*100)}%</span></div>`).join('') + `</div>`;
  }
  if (!p.destino.match && p.destino.candidatos.length) {
    candidatosHtml += `<div class="section-label" style="margin-top:12px;">¿Cuál es el destino?</div><div class="candidate-list">` +
      p.destino.candidatos.map(c => `<div class="candidate-item" onclick="pickUbicCandidato('destino','${c.ubic.id}')"><span>${c.ubic.nombre}</span><span class="score">${Math.round(c.score*100)}%</span></div>`).join('') + `</div>`;
  }

  // validación de disponibilidad si tenemos todo lo necesario
  let dispoHtml = '';
  let bloqueado = false;
  if (p.lote.match && p.origen.match && p.kg) {
    const declarado = stockPorLoteUbic(p.lote.match.id, p.origen.match.id);
    if (p.kg > declarado) {
      bloqueado = true;
      dispoHtml = `<div class="alert-box error"><div class="alert-title">🔴 Sin stock suficiente</div><div class="alert-body">Se dictaron <strong class="tabular">${fmtKg(p.kg)}</strong> pero el saldo en ${p.origen.match.nombre} es de <strong class="tabular">${fmtKg(declarado)}</strong>. No se puede confirmar.</div></div>`;
    }
  }

  const puedeConfirmar = p.lote.match && p.origen.match && p.destino.match && p.kg && !bloqueado;

  wrap.innerHTML = `
    <div class="section-label">Tarjeta de confirmación</div>
    <div class="card">
      <div class="field-row"><span class="field-label">Lote</span><span class="chip ${p.lote.match ? chipClass('alta') : 'dudoso'}">${loteLabel}</span></div>
      <div class="field-row"><span class="field-label">Cantidad</span><span class="chip ${chipClass(p.kgConfianza)}" onclick="editarCantidad()">${kgLabel} ${p.kg ? '<span class="edit-mark">✎</span>' : ''}</span></div>
      <div class="field-row"><span class="field-label">Origen</span><span class="chip ${p.origen.match ? chipClass('alta') : 'dudoso'}">${origenLabel}</span></div>
      <div class="field-row"><span class="field-label">Destino</span><span class="chip ${p.destino.match ? chipClass('alta') : 'dudoso'}">${destinoLabel}</span></div>
      ${candidatosHtml}
      ${dispoHtml}
      <div style="height:10px;"></div>
      <button class="btn btn-primary" ${puedeConfirmar ? '' : 'disabled'} onclick="confirmarMovimiento()">Confirmar</button>
    </div>`;
}

function editarCantidad() {
  const nuevo = prompt('Cantidad correcta en kg:', parsedActual.kg || '');
  if (nuevo === null) return;
  const val = parseFloat(nuevo);
  if (!isNaN(val) && val > 0) { parsedActual.kg = val; parsedActual.kgConfianza = 'alta'; renderParsedCard(); }
}
function pickLoteCandidato(loteId) {
  parsedActual.lote = { match: LOTE_BY_ID[loteId], candidatos: [], confianza: 'alta' };
  renderParsedCard();
}
function pickUbicCandidato(cual, ubicId) {
  const ubic = UBICACIONES.find(u => u.id === ubicId);
  if (cual === 'origen') parsedActual.origen = { match: ubic, candidatos: [], confianza: 'alta' };
  else parsedActual.destino = { match: ubic, candidatos: [], confianza: 'alta' };
  renderParsedCard();
}

function confirmarMovimiento() {
  const p = parsedActual;
  const mov = mkMov({
    loteId: p.lote.match.id, origenId: p.origen.match.id, destinoId: p.destino.match.id,
    kg: p.kg, fuente: 'voz', confianza: 'alta', confirmadoPor: 'Operario Depósito',
    transcripcion: p.transcripcion, diasAtras: 0,
  });
  if (offline) {
    syncQueue.push(mov.id);
  }
  MOVIMIENTOS.push(mov);

  const wrap = document.getElementById('parsedCardWrap');
  wrap.innerHTML = `<div class="alert-box confirmado"><div class="alert-title">🟢 Movimiento confirmado</div>
    <div class="alert-body">Lote ${p.lote.match.nroLote}: ${fmtKg(p.kg)} de ${p.origen.match.nombre} a ${p.destino.match.nombre}.${offline ? ' En cola de sincronización (sin señal).' : ''}</div></div>`;
  parsedActual = null;
  document.getElementById('transcriptBox').classList.add('empty');
  document.getElementById('transcriptBox').textContent = 'La transcripción va a aparecer acá, en azul, mientras escucha…';
  updateSyncPill();
}

// ============================================================
// ---------------------- CONTEO / MERMA -------------------------
// ============================================================
function initConteoView() {
  const sel = document.getElementById('conteoLoteSelect');
  if (!sel.dataset.filled) {
    const conStock = LOTES.filter(l => ubicacionActualDeLote(l.id));
    sel.innerHTML = conStock.map(l => `<option value="${l.id}" ${l.id === '17' ? 'selected' : ''}>Lote ${l.nroLote} — ${VARIEDADES.find(v=>v.id===l.variedadId).nombre}</option>`).join('');
    sel.dataset.filled = '1';
  }
  document.getElementById('conteoKgInput').value = document.getElementById('conteoKgInput').value || 13100;
  renderConteoForm();
}

function renderConteoForm() {
  renderDiscrepancia();
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
// determinística de arriba (ver `renderDiscrepancia`: sólo movimientos
// con salida sin espejo en destino o `confianza: 'dudosa', nunca la
// tabla de movimientos entera). Esa lista acotada — ya formateada como
// strings (fechas, kg, ubicaciones) — es lo único que se le pasaría a
// un LLM, con una tool/prompt que le exige:
//   1. Narrar en castellano llano SÓLO sobre esos movimientos.
//   2. Copiar fecha/kg/ubicación verbatim — prohibido reformatear,
//      redondear, o inventar un movimiento que no esté en la lista.
//   3. Si no hay candidatos, decir explícitamente "no encontré una
//      causa probable" en vez de inventar una.
// El LLM nunca decide QUÉ es candidato (eso ya lo resolvió el filtro
// determinístico) ni recalcula ningún número — sólo redacta la frase
// a partir de los datos que ya le llegaron resueltos. Reemplazar esta
// función por una llamada real a un LLM no debería tocar nada de
// `renderDiscrepancia`: la interfaz (candidatos in, texto out) es la
// misma, sólo cambia quién arma la oración.
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

function renderDiscrepancia() {
  const loteId = document.getElementById('conteoLoteSelect').value;
  const kgContado = parseFloat(document.getElementById('conteoKgInput').value);
  const lote = LOTE_BY_ID[loteId];
  const ubic = ubicacionActualDeLote(loteId);
  const resultEl = document.getElementById('discrepanciaResult');

  if (!ubic) { resultEl.innerHTML = '<div class="empty-state">Este lote no tiene stock activo.</div>'; return; }

  const declarado = stockPorLoteUbic(loteId, ubic.id);
  const ingreso = ultimoIngresoA(loteId, ubic.id);
  const dias = ingreso ? diasDesde(ingreso.fecha) : 0;
  const pct = mermaEsperadaPct(dias);
  const esperado = declarado * (1 - pct / 100);

  let bodyExtra = '';
  let box = '';
  if (isNaN(kgContado)) {
    box = `<div class="alert-box dudoso"><div class="alert-title">🟡 Ingresá el conteo</div><div class="alert-body">Escribí los kg contados físicamente para comparar contra lo esperado.</div></div>`;
  } else {
    const delta = kgContado - esperado;
    const tolerancia = declarado * 0.01;
    const excede = Math.abs(delta) > tolerancia;

    if (!excede) {
      box = `
        <div class="alert-box confirmado">
          <div class="alert-title">🟢 Dentro de la merma esperada</div>
          <div class="alert-body">Declarado ${fmtKg(declarado)} hace ${dias} días → merma esperada ${pct.toFixed(1)}% → esperado ${fmtKg(esperado)}. Contado ${fmtKg(kgContado)} (Δ ${delta >= 0 ? '+' : ''}${Math.round(delta)} kg). El sistema no genera alerta.</div>
        </div>`;
    } else {
      // Capa determinística: filtra candidatos ANTES de narrar. La
      // hipótesis (redactarHipotesisMerma, más abajo) sólo puede hablar
      // sobre lo que está en esta lista acotada — nunca sobre toda la
      // tabla de movimientos. Ver el comentario largo sobre
      // redactarHipotesisMerma para cómo esto se conecta con un LLM real.
      const candidatos = MOVIMIENTOS.filter(m => m.loteId === loteId && ((m.origenId && !m.destinoId) || m.confianza === 'dudosa'));
      const hipotesis = redactarHipotesisMerma(candidatos);
      box = `
        <div class="alert-box error">
          <div class="alert-title">🔴 Excede la merma esperada</div>
          <div class="alert-body">Declarado ${fmtKg(declarado)} hace ${dias} días → merma esperada ${pct.toFixed(1)}% → esperado ≈ ${fmtKg(esperado)}. Contado ${fmtKg(kgContado)} → Δ ${Math.round(delta)} kg, por encima de la tolerancia (${Math.round(tolerancia)} kg).</div>
          <div class="section-label" style="margin:6px 0 2px;">Hipótesis (redactada sólo sobre estos candidatos)</div>
          ${candidatos.length ? `
            <div class="evidence-list">
              ${candidatos.map(m => `<div class="evidence-item"><span>${escapeHtml(m.transcripcion ? m.transcripcion : (m.origenId ? 'Salida sin espejo en destino' : 'Movimiento de confianza dudosa'))} · ${fechaCorta(m.fecha)}</span><span class="tabular">${fmtKg(m.kg)}</span></div>`).join('')}
            </div>
            <div class="alert-body" style="margin-top:4px;">${hipotesis}</div>` :
            `<div class="alert-body">No hay movimientos candidatos con salida sin espejo o confianza dudosa. Escalar a supervisor para reconteo.</div>`}
        </div>`;
    }
  }

  resultEl.innerHTML = `
    <div class="section-label">Comparación</div>
    <div class="card">
      <div class="field-row"><span class="field-label">Declarado (libro)</span><span class="field-value tabular">${fmtKg(declarado)}</span></div>
      <div class="field-row"><span class="field-label">Días en ${ubic.nombre}</span><span class="field-value tabular">${dias}</span></div>
      <div class="field-row"><span class="field-label">Merma esperada</span><span class="field-value tabular">${pct.toFixed(1)}%</span></div>
      <div class="field-row"><span class="field-label">Kg esperado</span><span class="field-value tabular">${fmtKg(esperado)}</span></div>
    </div>
    ${box}`;
}

// ============================================================
// ---------------------- LOTES / LINAJE --------------------------
// ============================================================
function initLotesView() {
  const subSel = document.getElementById('nuevoLoteSub');
  if (!subSel.dataset.filled) {
    subSel.innerHTML = SUBCATEGORIAS.map(s => `<option value="${s.id}" ${s.id === 'inicial_I' ? 'selected' : ''}>${s.nombre} (${s.categoria})</option>`).join('');
    const padreSel = document.getElementById('nuevoLotePadre');
    padreSel.innerHTML = LOTES.map(l => {
      const s = SUBCATEGORIAS.find(x => x.id === l.subcategoria);
      return `<option value="${l.id}" ${l.id === '6' ? 'selected' : ''}>Lote ${l.nroLote} — ${s.nombre}</option>`;
    }).join('');
    subSel.dataset.filled = '1';
  }
  renderLotesList();
}

function renderLotesList() {
  const q = normaliza(document.getElementById('loteSearch').value);
  const wrap = document.getElementById('lotesListWrap');
  const filtered = LOTES.filter(l => {
    if (!q) return true;
    const s = SUBCATEGORIAS.find(x => x.id === l.subcategoria);
    const v = VARIEDADES.find(x => x.id === l.variedadId);
    return normaliza(`${l.nroLote} ${v.nombre} ${s.nombre} ${l.zonaProduccion}`).includes(q);
  });
  wrap.innerHTML = filtered.map(l => {
    const s = SUBCATEGORIAS.find(x => x.id === l.subcategoria);
    const v = VARIEDADES.find(x => x.id === l.variedadId);
    const stock = stockTotalLote(l.id);
    return `
      <div class="card tappable" onclick="pushView('lote', {loteId:'${l.id}'})">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:700; font-size:14px;">Lote ${l.nroLote}</div>
            <div style="font-size:11.5px; color:var(--color-text-dim); margin-top:2px;">${v.nombre} · ${s.nombre} · ${l.zonaProduccion}</div>
          </div>
          <div class="stat-big tabular" style="font-size:15px;">${fmtKg(stock)}</div>
        </div>
      </div>`;
  }).join('') || '<div class="empty-state">Sin resultados.</div>';
}

function intentarNuevoLote() {
  const subId = document.getElementById('nuevoLoteSub').value;
  const padreId = document.getElementById('nuevoLotePadre').value;
  const padre = LOTE_BY_ID[padreId];
  const padreSub = SUBCATEGORIAS.find(s => s.id === padre.subcategoria);
  const hijoSub = SUBCATEGORIAS.find(s => s.id === subId);
  const resultEl = document.getElementById('linajeResult');

  if (!linajeValido(padre.subcategoria, subId)) {
    const validas = SUBCATEGORIAS.slice(SUB_INDEX[padre.subcategoria]);
    resultEl.innerHTML = `
      <div class="alert-box error">
        <div class="alert-title">🔴 Rechazado — regla de linaje</div>
        <div class="alert-body">Un lote sólo puede provenir de una subcategoría igual o superior a la de su padre. El lote ${padre.nroLote} es <strong>${padreSub.nombre}</strong>; no puede originar un lote <strong>${hijoSub.nombre}</strong>.</div>
        <div class="section-label" style="margin:6px 0 2px;">Subcategorías válidas para este padre</div>
        <div class="evidence-list">${validas.map(s => `<div class="evidence-item"><span>${s.nombre}</span><span>${s.categoria}</span></div>`).join('')}</div>
      </div>`;
  } else {
    resultEl.innerHTML = `
      <div class="alert-box confirmado">
        <div class="alert-title">🟢 Linaje válido</div>
        <div class="alert-body">Lote nuevo <strong>${hijoSub.nombre}</strong> a partir del lote ${padre.nroLote} (<strong>${padreSub.nombre}</strong>). Listo para registrar.</div>
      </div>`;
  }
}

// ============================================================
// ---------------------- SYNC / OFFLINE ---------------------------
// ============================================================
let offline = false;
let syncQueue = [];

function toggleOffline() {
  offline = !offline;
  if (!offline && syncQueue.length) {
    // cascada a verde al reconectar
    const pending = [...syncQueue];
    syncQueue = [];
    updateSyncPill();
    pending.forEach((id, i) => {
      setTimeout(() => {
        syncQueue = syncQueue.filter(x => x !== id);
        updateSyncPill();
      }, 260 * (i + 1));
    });
  }
  updateSyncPill();
}
function updateSyncPill() {
  const pill = document.getElementById('syncPill');
  const label = document.getElementById('syncLabel');
  const badge = document.getElementById('syncBadge');
  pill.classList.toggle('offline', offline);
  label.textContent = offline ? 'Sin señal' : 'Conectado';
  if (syncQueue.length > 0) {
    badge.style.display = '';
    badge.textContent = syncQueue.length;
  } else {
    badge.style.display = 'none';
  }
}

// ============================================================
// ------------- EXPORTACIÓN (pantalla de cierre, N03) -----------
// ============================================================
// El sistema lee los requisitos documentales por destino y los cruza
// con la trazabilidad del lote para pre-completar lo que ya sabe.
// Igual que el resto de la app: el chequeo es determinístico. En la
// versión real, acá es donde el LLM redactaría una nota narrando
// SOLO los resultados de estos checks — nunca decidiendo el checkeo.
let currentExportLoteId = null;

function initExportacionView(loteId) {
  currentExportLoteId = loteId;
  const sel = document.getElementById('expPaisSelect');
  if (!sel.dataset.filled) {
    sel.innerHTML = PAISES_DESTINO.map(p => `<option value="${p.id}">${p.nombre}</option>`).join('');
    sel.dataset.filled = '1';
  }
  renderExportacion();
}

function renderExportacion() {
  const loteId = currentExportLoteId;
  const lote = LOTE_BY_ID[loteId];
  const sub = SUBCATEGORIAS.find(s => s.id === lote.subcategoria);
  const variedad = VARIEDADES.find(v => v.id === lote.variedadId);
  const ubic = ubicacionActualDeLote(loteId);
  const stockDeclarado = ubic ? stockPorLoteUbic(loteId, ubic.id) : stockTotalLote(loteId);
  const pais = PAISES_DESTINO.find(p => p.id === document.getElementById('expPaisSelect').value) || PAISES_DESTINO[0];
  const inase = certificadoInaseInfo(loteId);

  // ---- Pre-completado desde trazabilidad (nunca editable acá) ----
  document.getElementById('expPrecompletado').innerHTML = `
    <div class="field-row"><span class="field-label">Variedad</span><span class="chip confirmado">${variedad.nombre} (${variedad.obtentor})</span></div>
    <div class="field-row"><span class="field-label">Categoría</span><span class="chip confirmado">${sub.categoria} – ${sub.nombre}</span></div>
    <div class="field-row"><span class="field-label">Zona de producción</span><span class="chip confirmado">${lote.zonaProduccion}</span></div>
    <div class="field-row"><span class="field-label">Año de cosecha</span><span class="chip confirmado">${lote.anioCosecha}</span></div>
    <div class="field-row"><span class="field-label">Semillero / N° inscripción</span><span class="chip confirmado">${lote.semillero} · ${lote.nroInscripcion}</span></div>
    <div class="field-row"><span class="field-label">Peso declarado (trazabilidad)</span><span class="chip confirmado tabular">${fmtKg(stockDeclarado)}</span></div>
    <div class="field-row"><span class="field-label">Certificado INASE</span><span class="chip ${inase.vencido ? 'error' : 'confirmado'}">${inase.vencido ? 'vencido' : 'vigente'} · ${fechaCorta(inase.fecha.toISOString())}</span></div>
  `;

  let checksBannerHtml = '';
  if (pais.id === 'egipto') {
    checksBannerHtml = `<div class="alert-box dudoso"><div class="alert-title">🟡 Destino no habilitado</div><div class="alert-body">${escapeHtml(pais.plagaAdicional)}. Se muestra igual, a título ilustrativo — DEMO.</div></div>`;
  }

  const ncm = document.getElementById('expNcm').value.trim();
  const factura = document.getElementById('expFactura').value.trim();
  const fechaCertStr = document.getElementById('expFechaCert').value;
  const pesoPacking = parseFloat(document.getElementById('expPesoPacking').value);
  const envaseKg = parseFloat(document.getElementById('expEnvaseKg').value);
  const plagaOk = document.getElementById('expPlagaCheckbox') ? document.getElementById('expPlagaCheckbox').checked : false;

  const tope = sub.id.startsWith('preinicial') ? 20 : 50;

  const checks = [];

  checks.push(ncm === NCM_SEMILLA
    ? { status: 'ok', label: 'NCM', detail: `${NCM_SEMILLA} — semilla, correcto.` }
    : { status: 'fail', label: 'NCM', detail: `Declarado ${escapeHtml(ncm || '(vacío)')} — corresponde a semilla, no a consumo. Debe ser ${NCM_SEMILLA}. Es el error más caro y más fácil de cometer.` });

  if (!fechaCertStr) {
    checks.push({ status: 'pending', label: 'Certificado de origen', detail: 'Falta la fecha de emisión — dictá o cargá el dato.' });
  } else {
    const dias = diasDesde(new Date(fechaCertStr).toISOString());
    checks.push(dias <= 60
      ? { status: 'ok', label: 'Certificado de origen', detail: `Emitido hace ${dias} días — dentro de los 60 días.` }
      : { status: 'fail', label: 'Certificado de origen', detail: `Emitido hace ${dias} días — supera el margen de 60 días.` });
  }

  if (isNaN(pesoPacking)) {
    checks.push({ status: 'pending', label: 'Peso Factura E vs. packing list', detail: 'Falta el peso del packing list — dictá o cargá el dato.' });
  } else {
    const delta = Math.abs(pesoPacking - stockDeclarado);
    const tolerancia = stockDeclarado * 0.01;
    checks.push(delta <= tolerancia
      ? { status: 'ok', label: 'Peso Factura E vs. packing list', detail: `${fmtKg(pesoPacking)} — coincide con la trazabilidad (${fmtKg(stockDeclarado)}).` }
      : { status: 'fail', label: 'Peso Factura E vs. packing list', detail: `${fmtKg(pesoPacking)} declarado vs. ${fmtKg(stockDeclarado)} en trazabilidad — no cuadra.` });
  }

  if (pais.id !== 'egipto') {
    checks.push(plagaOk
      ? { status: 'ok', label: 'Declaración adicional de plaga', detail: `${escapeHtml(pais.plagaAdicional)} — adjunta.` }
      : { status: 'fail', label: 'Declaración adicional de plaga', detail: `Falta para ${pais.nombre}: ${escapeHtml(pais.plagaAdicional)}.` });
  }

  checks.push(isNaN(envaseKg)
    ? { status: 'pending', label: 'Rótulo — tope de kg por envase', detail: 'Cargá el peso del envase rotulado.' }
    : envaseKg <= tope
      ? { status: 'ok', label: 'Rótulo — tope de kg por envase', detail: `${envaseKg} kg — dentro del tope (${tope} kg, ${sub.categoria}).` }
      : { status: 'fail', label: 'Rótulo — tope de kg por envase', detail: `${envaseKg} kg excede el tope de ${tope} kg para ${sub.nombre}.` });

  checks.push(inase.vencido
    ? { status: 'fail', label: 'Certificado INASE', detail: `Vencido el ${fechaCorta(inase.fecha.toISOString())}.` }
    : { status: 'ok', label: 'Certificado INASE', detail: `Vigente hasta el ${fechaCorta(inase.fecha.toISOString())}.` });

  const icon = { ok: '🟢', fail: '🔴', pending: '🟡' };
  document.getElementById('expChecks').innerHTML = checksBannerHtml + checks.map(c => `
    <div class="check-item ${c.status}">
      <div class="check-icon">${icon[c.status]}</div>
      <div class="check-body">
        <div class="check-label">${c.label}</div>
        <div class="check-detail">${c.detail}</div>
      </div>
    </div>`).join('');

  document.getElementById('expDocResult').innerHTML = '';
}

function dictarCamposExportacion() {
  const btn = document.getElementById('expMicBtn');
  btn.classList.add('listening');
  setTimeout(() => {
    btn.classList.remove('listening');
    document.getElementById('expFactura').value = 'A-0001-00003842';
    const fecha = new Date();
    fecha.setDate(fecha.getDate() - 45);
    document.getElementById('expFechaCert').value = fecha.toISOString().slice(0, 10);
    const lote = LOTE_BY_ID[currentExportLoteId];
    const ubic = ubicacionActualDeLote(currentExportLoteId);
    const stockDeclarado = ubic ? stockPorLoteUbic(currentExportLoteId, ubic.id) : stockTotalLote(currentExportLoteId);
    document.getElementById('expPesoPacking').value = Math.round(stockDeclarado);
    renderExportacion();
    // la declaración de plaga y NCM/envase quedan para revisión manual —
    // el dictado no inventa un check que el operario no confirmó.
  }, 650);
}

function generarDocumentoExportacion() {
  const loteId = currentExportLoteId;
  const lote = LOTE_BY_ID[loteId];
  const checksEls = document.querySelectorAll('#expChecks .check-item');
  const fails = document.querySelectorAll('#expChecks .check-item.fail').length;
  const pending = document.querySelectorAll('#expChecks .check-item.pending').length;
  const resultEl = document.getElementById('expDocResult');

  if (fails > 0 || pending > 0) {
    resultEl.innerHTML = `
      <div class="alert-box error">
        <div class="alert-title">🔴 No se puede generar — hay ${fails} inconsistencia${fails === 1 ? '' : 's'}${pending ? ` y ${pending} dato${pending === 1 ? '' : 's'} sin completar` : ''}</div>
        <div class="alert-body">Resolvé lo marcado en rojo/amarillo arriba antes de generar el documento. Es más barato encontrarlo acá que en la aduana.</div>
      </div>`;
    return;
  }

  resultEl.innerHTML = `
    <div class="alert-box confirmado">
      <div class="alert-title">🟢 Documento generado — DEMO, SIN VALOR LEGAL / NO OFICIAL</div>
      <div class="alert-body">
        Factura proforma — Lote ${lote.nroLote}<br/>
        NCM ${escapeHtml(document.getElementById('expNcm').value)} · Factura ${escapeHtml(document.getElementById('expFactura').value)}<br/>
        Certificado de origen: ${document.getElementById('expFechaCert').value}<br/>
        Peso: ${document.getElementById('expPesoPacking').value} kg
      </div>
    </div>`;
}

// ============================================================
// ---------------------- INIT ---------------------------------
// ============================================================
renderView('tablero');
updateSyncPill();
