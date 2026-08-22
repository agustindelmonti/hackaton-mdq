// ============================================================
// Papasud — prototipo desktop. Misma regla que el mobile: núcleo
// determinístico (acá + logic.js + data-desktop.js) y nada de LLM de
// verdad — el panel conversacional usa preguntas enlatadas resueltas
// por "tools" tipadas fijas (ver data-desktop.js), con el mismo
// patrón de cita de fuente que tendría con un modelo real detrás.
// ============================================================

const TITLES = {
  analitica: ['Analítica', 'Rendimiento, superficie y consulta con cita de fuente'],
  exportacion: ['Comercio exterior', 'Pipeline de documentación de exportación — DEMO, sin valor legal'],
  operaciones: ['Operaciones de stock', 'Vista única de las 4 ubicaciones, libro de movimientos y discrepancias'],
};

function navTo(view) {
  document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.dataset.view === view));
  document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.toggle('active', b.dataset.nav === view));
  document.getElementById('topTitle').textContent = TITLES[view][0];
  document.getElementById('topSubtitle').textContent = TITLES[view][1];
  if (view === 'analitica') initAnalitica();
  if (view === 'exportacion') initExportacion();
  if (view === 'operaciones') initOperaciones();
}

// ============================================================
// ---------------------- ANALÍTICA ------------------------------
// ============================================================
let chartsInit = false;

function initAnalitica() {
  renderKPIs();
  renderOutlierCard();
  if (!chartsInit) { renderCharts(); chartsInit = true; }
  if (!document.getElementById('querySuggestions').dataset.filled) {
    renderQuerySuggestions();
    document.getElementById('querySuggestions').dataset.filled = '1';
  }
}

function renderKPIs() {
  const sup = variacionAnual('superficieHa');
  const prod = variacionAnual('produccionT');
  const campanas2025 = CAMPANAS.filter(c => c.anio === 2025);
  const rendProm2025 = campanas2025.reduce((s, c) => s + c.rendimientoTHa, 0) / campanas2025.length;
  const campanas2024 = CAMPANAS.filter(c => c.anio === 2024);
  const rendProm2024 = campanas2024.reduce((s, c) => s + c.rendimientoTHa, 0) / campanas2024.length;
  const rendDelta = ((rendProm2025 - rendProm2024) / rendProm2024) * 100;

  const kpis = [
    { label: 'Superficie sembrada 2025', value: Math.round(sup.valUltimo).toLocaleString('es-AR') + ' ha', delta: sup.pct },
    { label: 'Producción 2025', value: Math.round(prod.valUltimo).toLocaleString('es-AR') + ' t', delta: prod.pct },
    { label: 'Rendimiento promedio 2025', value: (Math.round(rendProm2025 * 10) / 10) + ' t/ha', delta: Math.round(rendDelta * 10) / 10 },
    { label: 'Campaña en curso', value: '2025 · pérdidas', delta: null },
  ];
  document.getElementById('kpiGrid').innerHTML = kpis.map(k => `
    <div class="card kpi-card">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-value tabular">${k.value}</div>
      ${k.delta !== null ? `<div class="kpi-delta ${k.delta >= 0 ? 'up' : 'down'}">${k.delta >= 0 ? '▲' : '▼'} ${Math.abs(k.delta)}% vs. año anterior</div>` : `<div class="kpi-delta down">11 meses consecutivos de pérdidas, según Papasud</div>`}
    </div>`).join('');
}

// F1.9 — detección de outliers: para cada variedad, la campaña con
// mayor desvío negativo respecto a su propio promedio histórico.
function renderOutlierCard() {
  let peor = null;
  VARIEDADES.forEach(v => {
    const filas = CAMPANAS.filter(c => c.variedadId === v.id);
    if (!filas.length) return;
    const promedio = filas.reduce((s, f) => s + f.rendimientoTHa, 0) / filas.length;
    filas.forEach(f => {
      const desvio = f.rendimientoTHa - promedio;
      if (!peor || desvio < peor.desvio) peor = { ...f, promedio: Math.round(promedio * 10) / 10, desvio: Math.round(desvio * 10) / 10 };
    });
  });
  document.getElementById('outlierCard').innerHTML = `
    <h3>Outlier de campaña (F1.9)</h3>
    <div class="card-sub">Qué año se salió de la curva y por cuánto</div>
    <div class="alert-box dudoso">
      <div class="alert-title">🟡 ${nombreVariedad(peor.variedadId)} ${peor.anio}</div>
      <div class="alert-body">Rindió ${peor.rendimientoTHa} t/ha contra un promedio histórico propio de ${peor.promedio} t/ha (${peor.desvio} t/ha). Es la mayor caída puntual de la serie — candidato a revisar campaña, no necesariamente un error de carga.</div>
    </div>`;
}

function renderCharts() {
  const anios = [...new Set(CAMPANAS.map(c => c.anio))].sort();
  const colores = { innovator: '#4d8fd6', spunta: '#5cb85c', atlantic: '#d69a2d' };
  const gridColor = 'rgba(255,255,255,0.06)';
  const textColor = '#9aa7b0';
  Chart.defaults.color = textColor;
  Chart.defaults.font.size = 11;

  // Rendimiento por variedad y campaña
  new Chart(document.getElementById('chartRendimiento'), {
    type: 'line',
    data: {
      labels: anios,
      datasets: Object.keys(colores).map(vid => ({
        label: nombreVariedad(vid),
        data: anios.map(a => (CAMPANAS.find(c => c.anio === a && c.variedadId === vid) || {}).rendimientoTHa),
        borderColor: colores[vid], backgroundColor: colores[vid], tension: 0.25, pointRadius: 3,
      })),
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { x: { grid: { color: gridColor } }, y: { grid: { color: gridColor }, title: { display: true, text: 't/ha' } } },
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 10 } } },
    },
  });

  // Superficie sembrada por año, 2025 destacada
  new Chart(document.getElementById('chartSuperficie'), {
    type: 'bar',
    data: {
      labels: anios,
      datasets: [{
        label: 'Superficie total (ha)',
        data: anios.map(a => CAMPANAS.filter(c => c.anio === a).reduce((s, c) => s + c.superficieHa, 0)),
        backgroundColor: anios.map(a => a === 2025 ? '#c1502e' : '#4d8fd6'),
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { x: { grid: { display: false } }, y: { grid: { color: gridColor }, title: { display: true, text: 'ha' } } },
      plugins: { legend: { display: false } },
    },
  });

  // Benchmark de zona
  const aniosBench = Object.keys(BENCHMARK_ZONA).map(Number).sort();
  new Chart(document.getElementById('chartBenchmark'), {
    type: 'bar',
    data: {
      labels: aniosBench,
      datasets: [
        { label: 'Papasud', backgroundColor: '#5cb85c', data: aniosBench.map(a => { const f = CAMPANAS.filter(c => c.anio === a); return Math.round((f.reduce((s, c) => s + c.rendimientoTHa, 0) / f.length) * 10) / 10; }) },
        { label: 'Promedio partido (MAGyP, DEMO)', backgroundColor: '#6b7680', data: aniosBench.map(a => BENCHMARK_ZONA[a].promedioPartidoTHa) },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      scales: { x: { grid: { display: false } }, y: { grid: { color: gridColor }, title: { display: true, text: 't/ha' } } },
      plugins: { legend: { position: 'bottom', labels: { boxWidth: 10 } } },
    },
  });
}

// ---------- Panel conversacional (Flow H) ----------
function renderQuerySuggestions() {
  document.getElementById('querySuggestions').innerHTML = QUERIES.map(q =>
    `<span class="suggestion-chip" onclick="ejecutarPregunta('${q.id}')">${escapeHtml(q.pregunta)}</span>`).join('');
}

function enviarPregunta() {
  const input = document.getElementById('chatInput');
  const texto = input.value.trim();
  if (!texto) return;
  const match = QUERIES.find(q => normaliza(q.pregunta) === normaliza(texto)) ||
    QUERIES.find(q => normaliza(texto).includes(normaliza(q.pregunta).slice(0, 12)));
  input.value = '';
  if (match) { pushChatUser(match.pregunta); resolverPregunta(match); }
  else {
    pushChatUser(texto);
    pushChatAssistant('No tengo una tool cargada para esa pregunta todavía — elegí una de las sugeridas arriba, o probá reformularla parecido a una de ellas.', 'dudoso');
  }
}
function ejecutarPregunta(id) {
  const q = QUERIES.find(x => x.id === id);
  pushChatUser(q.pregunta);
  resolverPregunta(q);
}
function resolverPregunta(q) {
  const r = q.run();
  if (r.ambiguo) {
    pushChatAssistant(r.pregunta_aclaratoria, 'dudoso', null,
      r.opciones.map(op => `<span class="suggestion-chip" onclick="responderConVariedad('${VARIEDADES.find(v => v.nombre === op).id}')">${escapeHtml(op)}</span>`).join(''));
  } else if (r.noRespondible) {
    pushChatAssistant(r.motivo, 'dudoso');
  } else {
    pushChatAssistant(r.respuesta, 'confirmado', { toolName: r.toolName, filas: r.filas });
  }
}
function responderConVariedad(variedadId) {
  const { filas, promedio } = rendimientoPor(variedadId, false);
  pushChatAssistant(
    `${nombreVariedad(variedadId)} rindió en promedio ${promedio} t/ha en toda la serie histórica (2018-2025).`,
    'confirmado',
    { toolName: `rendimiento_por(variedad="${variedadId}")`, filas: filas.map(f => `${f.anio} · ${f.rendimientoTHa} t/ha`) });
}

function pushChatUser(texto) {
  const log = document.getElementById('chatLog');
  log.innerHTML += `<div class="chat-msg user">${escapeHtml(texto)}</div>`;
  log.scrollTop = log.scrollHeight;
}
function pushChatAssistant(texto, estado, tool, extraChipsHtml) {
  const log = document.getElementById('chatLog');
  const toolHtml = tool ? `
    <details class="tool-call">
      <summary>Ver fuente / tool call</summary>
      <div class="tool-body">
        <div class="tool-name">${escapeHtml(tool.toolName)}</div>
        <div class="evidence-list">${tool.filas.map(f => `<div class="evidence-item"><span>${escapeHtml(f)}</span></div>`).join('')}</div>
      </div>
    </details>` : '';
  log.innerHTML += `<div class="chat-msg assistant ${estado}">${escapeHtml(texto)}${toolHtml}${extraChipsHtml ? `<div class="suggestion-row" style="margin-top:8px; margin-bottom:0;">${extraChipsHtml}</div>` : ''}</div>`;
  log.scrollTop = log.scrollHeight;
}

// ============================================================
// ---------------------- COMERCIO EXTERIOR -----------------------
// ============================================================
function initExportacion() {
  const selPais = document.getElementById('expFiltroPais');
  if (!selPais.dataset.filled) {
    selPais.innerHTML += PAISES_DESTINO.map(p => `<option value="${p.id}">${p.nombre}</option>`).join('');
    selPais.dataset.filled = '1';
  }
  renderPipeline();
}

// Mismos chequeos F3.13 que el mobile (ver prototype/app.js
// generarDocumentoExportacion), acá agregados a escala de tabla en vez
// de un formulario por lote. Reusa NCM_SEMILLA, PAISES_DESTINO,
// certificadoInaseInfo y SUBCATEGORIAS de prototype/data.js, y
// stockPorLoteUbic/ubicacionActualDeLote de logic.js — el estado
// nunca se guarda aparte, siempre se deriva de estos campos.
function evaluarExportacion(entry) {
  const lote = LOTE_BY_ID[entry.loteId];
  const sub = SUBCATEGORIAS.find(s => s.id === lote.subcategoria);
  const pais = PAISES_DESTINO.find(p => p.id === entry.paisId);
  const ubic = ubicacionActualDeLote(entry.loteId);
  const declarado = ubic ? stockPorLoteUbic(entry.loteId, ubic.id) : 0;
  const inase = certificadoInaseInfo(entry.loteId);
  const tope = sub.id.startsWith('preinicial') ? 20 : 50;
  const diasCert = diasDesde(entry.fechaCertOrigen);

  const checks = [
    { label: 'NCM', ok: entry.ncmDeclarado === NCM_SEMILLA, detalle: entry.ncmDeclarado === NCM_SEMILLA ? `${NCM_SEMILLA}, correcto` : `Declarado ${entry.ncmDeclarado} — debe ser ${NCM_SEMILLA}` },
    { label: 'Certificado de origen', ok: diasCert <= 60, detalle: `Emitido hace ${diasCert} días` },
    { label: 'Peso Factura E vs. packing list', ok: Math.abs(entry.pesoPackingList - declarado) <= declarado * 0.01, detalle: `${fmtKg(entry.pesoPackingList)} declarado vs. ${fmtKg(declarado)} en trazabilidad` },
    { label: 'Declaración de plaga', ok: pais.id === 'egipto' || entry.plagaAdjunta, detalle: pais.id === 'egipto' ? 'Mercado no habilitado — no aplica' : (entry.plagaAdjunta ? pais.plagaAdicional + ' — adjunta' : `Falta: ${pais.plagaAdicional}`) },
    { label: 'Rótulo — tope de kg', ok: entry.envaseKg <= tope, detalle: `${entry.envaseKg} kg (tope ${tope} kg, ${sub.categoria})` },
    { label: 'Certificado INASE', ok: !inase.vencido, detalle: inase.vencido ? `Vencido el ${fechaCorta(inase.fecha.toISOString())}` : `Vigente hasta el ${fechaCorta(inase.fecha.toISOString())}` },
  ];
  const estado = checks.every(c => c.ok) ? 'listo' : 'con_inconsistencias';
  return { lote, sub, pais, checks, estado, motivos: checks.filter(c => !c.ok).map(c => c.label) };
}

function renderPipeline() {
  const filtroEstado = document.getElementById('expFiltroEstado').value;
  const filtroPais = document.getElementById('expFiltroPais').value;
  const evaluados = EXPORT_PIPELINE.map(e => ({ entry: e, ev: evaluarExportacion(e) }))
    .filter(({ ev }) => filtroEstado === 'todos' || ev.estado === filtroEstado)
    .filter(({ entry }) => filtroPais === 'todos' || entry.paisId === filtroPais);

  document.getElementById('expCount').textContent = `${evaluados.length} de ${EXPORT_PIPELINE.length} lotes`;
  document.getElementById('expTableBody').innerHTML = evaluados.map(({ entry, ev }) => `
    <tr class="clickable" onclick="abrirDrawerExportacion(${EXPORT_PIPELINE.indexOf(entry)})">
      <td>Lote ${ev.lote.nroLote}</td>
      <td>${VARIEDADES.find(v => v.id === ev.lote.variedadId).nombre}</td>
      <td>${ev.pais.nombre}</td>
      <td>${escapeHtml(entry.responsable)}</td>
      <td class="tabular">${fechaCorta(entry.actualizado)}</td>
      <td><span class="chip ${ev.estado === 'listo' ? 'confirmado' : 'error'}">${ev.estado === 'listo' ? 'listo' : `${ev.motivos.length} inconsistencia${ev.motivos.length === 1 ? '' : 's'}`}</span></td>
      <td><button class="btn-ghost">Ver detalle →</button></td>
    </tr>`).join('') || `<tr><td colspan="7"><div class="empty-state">Sin lotes para este filtro.</div></td></tr>`;
}

function abrirDrawerExportacion(index) {
  const entry = EXPORT_PIPELINE[index];
  const ev = evaluarExportacion(entry);
  document.getElementById('drawerContent').innerHTML = `
    <h2>Lote ${ev.lote.nroLote} → ${ev.pais.nombre}</h2>
    <div class="drawer-sub">Responsable ${escapeHtml(entry.responsable)} · actualizado ${fechaCorta(entry.actualizado)}</div>
    <div class="alert-box ${ev.estado === 'listo' ? 'confirmado' : 'error'}" style="margin-bottom:16px;">
      <div class="alert-title">${ev.estado === 'listo' ? '🟢 Listo para generar' : `🔴 ${ev.motivos.length} inconsistencia${ev.motivos.length === 1 ? '' : 's'} detectada${ev.motivos.length === 1 ? '' : 's'}`}</div>
      <div class="alert-body">${ev.estado === 'listo' ? 'Los 6 chequeos F3.13 pasaron.' : 'Marcado DEMO — SIN VALOR LEGAL / NO OFICIAL hasta resolverlas.'}</div>
    </div>
    <div class="evidence-list">
      ${ev.checks.map(c => `
        <div class="evidence-item" style="align-items:flex-start;">
          <span>${c.ok ? '🟢' : '🔴'} <strong>${c.label}</strong><br/><span style="color:var(--color-text-faint); font-size:11px;">${escapeHtml(c.detalle)}</span></span>
        </div>`).join('')}
    </div>`;
  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawerBackdrop').classList.add('open');
}
function cerrarDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawerBackdrop').classList.remove('open');
}

// ============================================================
// -------------------- OPERACIONES DE STOCK -----------------------
// ============================================================
function initOperaciones() {
  UBICACIONES.forEach((u, i) => { document.getElementById('colUbic' + i).textContent = u.nombre; });
  renderStockTable();
  renderDiscrepanciaQueue();
  renderMovimientosTable();
}

function renderStockTable() {
  document.getElementById('stockTableBody').innerHTML = LOTES.map(l => {
    const sub = SUBCATEGORIAS.find(s => s.id === l.subcategoria);
    const porUbic = UBICACIONES.map(u => stockPorLoteUbic(l.id, u.id));
    const total = porUbic.reduce((s, kg) => s + Math.max(0, kg), 0);
    if (total === 0) return '';
    return `<tr>
      <td>Lote ${l.nroLote}</td>
      <td>${VARIEDADES.find(v => v.id === l.variedadId).nombre}</td>
      <td>${sub.nombre}</td>
      ${porUbic.map(kg => `<td class="tabular">${kg > 0 ? fmtKg(kg) : '—'}</td>`).join('')}
      <td class="tabular"><strong>${fmtKg(total)}</strong></td>
    </tr>`;
  }).join('');
}

function renderDiscrepanciaQueue() {
  const wrap = document.getElementById('discrepanciaQueue');
  if (!CONTEOS.length) { wrap.innerHTML = '<div class="empty-state">Sin conteos registrados. Se cargan desde el prototipo mobile (pestaña Conteo).</div>'; return; }
  const ordenados = [...CONTEOS].sort((a, b) => new Date(b.fecha) - new Date(a.fecha));
  wrap.innerHTML = ordenados.map(c => {
    const lote = LOTE_BY_ID[c.loteId];
    const ubic = UBICACIONES.find(u => u.id === c.ubicacionId);
    const excede = c.clasificacion === 'excede_merma';
    let hipotesisHtml = '';
    if (excede) {
      const candidatos = candidatosDiscrepancia(c.loteId);
      const hipotesis = redactarHipotesisMerma(candidatos);
      hipotesisHtml = `<div class="alert-body" style="margin-top:6px;">${hipotesis || 'No hay movimientos candidatos — escalar a supervisor para reconteo.'}</div>`;
    }
    return `
      <div class="alert-box ${excede ? 'error' : 'confirmado'}" style="margin-bottom:10px;">
        <div class="alert-title">${excede ? '🔴' : '🟢'} Lote ${lote.nroLote} · ${ubic.nombre} — ${excede ? 'excede la merma esperada' : 'dentro de la merma esperada'}</div>
        <div class="alert-body">Contado ${fmtKg(c.kgContado)} vs. esperado ${fmtKg(c.kgEsperado)} (Δ ${Math.round(c.delta)} kg) · ${fechaCorta(c.fecha)} · ${escapeHtml(c.usuario)} · ${c.confianza === 'alta' ? 'pesaje confirmado' : 'estimado, pendiente de pesaje'}</div>
        ${hipotesisHtml}
      </div>`;
  }).join('');
}

function renderMovimientosTable() {
  const fuente = document.getElementById('movFiltroFuente').value;
  const confianza = document.getElementById('movFiltroConfianza').value;
  const filtrados = MOVIMIENTOS
    .filter(m => fuente === 'todos' || m.fuente === fuente)
    .filter(m => confianza === 'todos' || m.confianza === confianza)
    .sort((a, b) => new Date(b.fecha) - new Date(a.fecha))
    .slice(0, 150);

  document.getElementById('movCount').textContent = `${filtrados.length} movimientos (últimos 150)`;
  document.getElementById('movTableBody').innerHTML = filtrados.map(m => {
    const lote = LOTE_BY_ID[m.loteId];
    const origen = m.origenId ? UBICACIONES.find(u => u.id === m.origenId).nombre : 'Ingreso/cosecha';
    const destino = m.destinoId ? UBICACIONES.find(u => u.id === m.destinoId).nombre : 'Egreso/despacho';
    return `<tr>
      <td class="tabular">${fechaCorta(m.fecha)}</td>
      <td>Lote ${lote.nroLote}</td>
      <td>${origen}</td>
      <td>${destino}</td>
      <td class="tabular">${fmtKg(m.kg)}</td>
      <td><span class="badge-src">${m.fuente}</span></td>
      <td><span class="chip ${m.confianza === 'alta' ? 'confirmado' : 'dudoso'}">${m.confianza}</span></td>
      <td>${escapeHtml(m.usuario)}</td>
    </tr>`;
  }).join('') || `<tr><td colspan="8"><div class="empty-state">Sin movimientos para este filtro.</div></td></tr>`;
}

// ============================================================
// ---------------------- INIT ---------------------------------
// ============================================================
navTo('analitica');
