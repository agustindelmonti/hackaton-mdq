// ============================================================
// Datos mock específicos del prototipo desktop. Carga después de
// ../prototype/data.js y ../prototype/logic.js — reusa LOTES,
// UBICACIONES, VARIEDADES, SUBCATEGORIAS, MOVIMIENTOS, CONTEOS,
// PAISES_DESTINO, NCM_SEMILLA, certificadoInaseInfo, etc. de ahí.
// Todo lo de acá es específico de los roles de escritorio: series
// históricas de campañas (Vertical 01) y el pipeline de exportación
// a escala (vs. el detalle de un solo lote que ya cubre el mobile).
// ============================================================

// ---------- Campañas históricas (F1.6-F1.9, Flow H) ----------
// Rendimiento en t/ha, superficie en ha, por variedad y campaña.
// Números ilustrativos — no son datos reales de Papasud. La caída de
// superficie en 2025/26 y el año de pérdidas están tomados como
// hechos narrativos de docs/papasud-company-research.md, no como
// series verificadas.
const CAMPANAS = (function build() {
  const anios = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025];
  const base = { innovator: 34, spunta: 29, atlantic: 31 };
  const rows = [];
  anios.forEach((anio, i) => {
    Object.keys(base).forEach(variedadId => {
      // Leve tendencia + una campaña de "precios bajos" marcada (2020, 2023)
      // + un outlier real: 2022 se sale de la curva para innovator.
      let rendimiento = base[variedadId] + i * 0.4 + (Math.sin(i * 1.3 + base[variedadId]) * 1.2);
      if (variedadId === 'innovator' && anio === 2022) rendimiento -= 7.5; // outlier (F1.9)
      const precioBajo = anio === 2020 || anio === 2023;
      const superficieBase = { innovator: 62, spunta: 48, atlantic: 41 }[variedadId];
      let superficie = superficieBase + i * 1.1;
      if (anio === 2025) superficie *= 0.88; // -12% superficie sembrada 2025/26
      rows.push({
        anio, variedadId,
        rendimientoTHa: Math.round(rendimiento * 10) / 10,
        superficieHa: Math.round(superficie),
        produccionT: Math.round(rendimiento * superficie),
        precioBajo,
        perdida: anio === 2025,
      });
    });
  });
  return rows;
})();

// ---------- Benchmark de zona (F1.8) — MAGyP, ILUSTRATIVO ----------
// Las Estimaciones Agrícolas de MAGyP son un dato público real, pero
// estos valores puntuales NO se verificaron contra la fuente — se
// muestran marcados como tal en la UI, nunca con tono de autoridad.
const BENCHMARK_ZONA = {
  2023: { promedioPartidoTHa: 27.8 },
  2024: { promedioPartidoTHa: 28.4 },
  2025: { promedioPartidoTHa: 28.1 },
};

// ---------- Pipeline de exportación a escala (F3.12-F3.15) ----------
// Cada entrada trae los mismos campos que la pantalla mobile de
// Exportación pide por dictado/carga rápida — acá vienen pre-cargados
// para simular un lote de trabajo ya en curso del administrativo.
// El estado (listo / con inconsistencias) se DERIVA de estos campos
// con la misma lógica de checks que el mobile, nunca se guarda como
// dato aparte — ver evaluarExportacion() en desktop/app.js.
const EXPORT_PIPELINE = [
  { loteId: '6', paisId: 'brasil', responsable: 'M. Ibáñez', actualizado: diasAtras(1), ncmDeclarado: '0701.10.00', fechaCertOrigen: diasAtras(20), pesoPackingList: 20000, envaseKg: 45, plagaAdjunta: true },
  { loteId: '7', paisId: 'brasil', responsable: 'M. Ibáñez', actualizado: diasAtras(2), ncmDeclarado: '0701.90.00', fechaCertOrigen: diasAtras(75), pesoPackingList: 19200, envaseKg: 55, plagaAdjunta: false },
  { loteId: '13', paisId: 'uruguay', responsable: 'M. Ibáñez', actualizado: diasAtras(3), ncmDeclarado: '0701.10.00', fechaCertOrigen: diasAtras(15), pesoPackingList: 32200, envaseKg: 48, plagaAdjunta: true },
  { loteId: '17', paisId: 'vietnam', responsable: 'R. Sosa', actualizado: diasAtras(1), ncmDeclarado: '0701.10.00', fechaCertOrigen: diasAtras(10), pesoPackingList: 14000, envaseKg: 40, plagaAdjunta: true },
  { loteId: '20', paisId: 'brasil', responsable: 'R. Sosa', actualizado: diasAtras(5), ncmDeclarado: '0701.10.00', fechaCertOrigen: diasAtras(40), pesoPackingList: 17600, envaseKg: 50, plagaAdjunta: true },
  { loteId: '24', paisId: 'egipto', responsable: 'M. Ibáñez', actualizado: diasAtras(8), ncmDeclarado: '0701.10.00', fechaCertOrigen: diasAtras(30), pesoPackingList: 27300, envaseKg: 50, plagaAdjunta: false },
];
function diasAtras(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}

// ============================================================
// "Tools" tipadas fijas para la consulta conversacional (Flow H).
//
// Igual que en logic.js: esto es JS plano, no un LLM. Cada función de
// acá es una de las "tools tipadas fijas — no SQL libre" que describe
// CLAUDE.md: recibe argumentos concretos, devuelve datos YA
// formateados. En la app real, el LLM elegiría cuál tool llamar (a
// partir de la pregunta en lenguaje natural) y después SÓLO copiaría
// el string `respuesta` verbatim — nunca recalcula el número, nunca
// redondea distinto. Acá el "cuál tool" lo decide directamente cada
// pregunta enlatada (ver QUERIES más abajo), porque no hay LLM que
// haga ese paso — pero la forma de la respuesta (texto ya armado +
// las filas que lo sustentan, para la cita de fuente) es la misma que
// tendría con un modelo real detrás.
// ============================================================
function nombreVariedad(id) { return VARIEDADES.find(v => v.id === id).nombre; }

function rendimientoPor(variedadId, filtroPrecioBajo) {
  const filas = CAMPANAS.filter(c => c.variedadId === variedadId && (!filtroPrecioBajo || c.precioBajo));
  if (!filas.length) return null;
  const promedio = filas.reduce((s, f) => s + f.rendimientoTHa, 0) / filas.length;
  return { filas, promedio: Math.round(promedio * 10) / 10 };
}

function compararVariedades(aId, bId, anio) {
  const a = CAMPANAS.find(c => c.variedadId === aId && c.anio === anio);
  const b = CAMPANAS.find(c => c.variedadId === bId && c.anio === anio);
  if (!a || !b) return null;
  return { a, b };
}

function benchmarkZona(anio) {
  const propio = CAMPANAS.filter(c => c.anio === anio);
  const zona = BENCHMARK_ZONA[anio];
  if (!propio.length || !zona) return null;
  const promedioPropio = propio.reduce((s, f) => s + f.rendimientoTHa, 0) / propio.length;
  return { promedioPropio: Math.round(promedioPropio * 10) / 10, promedioZona: zona.promedioPartidoTHa, anio };
}

function variacionAnual(indicador) {
  const anios = [...new Set(CAMPANAS.map(c => c.anio))].sort();
  const ultimo = anios[anios.length - 1], previo = anios[anios.length - 2];
  const sum = (anio) => CAMPANAS.filter(c => c.anio === anio).reduce((s, f) => s + f[indicador], 0);
  const valUltimo = sum(ultimo), valPrevio = sum(previo);
  const pct = ((valUltimo - valPrevio) / valPrevio) * 100;
  return { ultimo, previo, valUltimo, valPrevio, pct: Math.round(pct * 10) / 10 };
}

// Preguntas enlatadas para el panel conversacional. Cada `run()`
// devuelve una de tres formas:
//   { respuesta, toolName, args, filas } — resuelta con cita de fuente
//   { ambiguo: true, pregunta_aclaratoria, opciones } — F1.4, repregunta
//   { noRespondible: true, motivo } — UC1.7, declara el límite en vez de aproximar
const QUERIES = [
  {
    id: 'spunta-precios-bajos',
    pregunta: '¿Cómo rindió la Spunta en las campañas de precios bajos?',
    run() {
      const { filas, promedio } = rendimientoPor('spunta', true);
      return {
        toolName: 'rendimiento_por(variedad="spunta", filtro="precios_bajos")',
        args: { variedad: 'Spunta', filtro: 'precios_bajos' },
        filas: filas.map(f => `${f.anio} · ${f.rendimientoTHa} t/ha`),
        respuesta: `En las campañas de precios bajos (${filas.map(f => f.anio).join(' y ')}), la Spunta rindió en promedio ${promedio} t/ha.`,
      };
    },
  },
  {
    id: 'comparar-innovator-atlantic',
    pregunta: 'Compará el rendimiento de Innovator vs. Atlantic en 2025',
    run() {
      const { a, b } = compararVariedades('innovator', 'atlantic', 2025);
      const mejor = a.rendimientoTHa >= b.rendimientoTHa ? a : b;
      const peor = mejor === a ? b : a;
      return {
        toolName: 'comparar(a="innovator", b="atlantic", campaña=2025)',
        args: { a: 'Innovator', b: 'Atlantic', campaña: 2025 },
        filas: [`Innovator 2025 · ${a.rendimientoTHa} t/ha`, `Atlantic 2025 · ${b.rendimientoTHa} t/ha`],
        respuesta: `En 2025, ${nombreVariedad(mejor.variedadId)} rindió ${mejor.rendimientoTHa} t/ha contra ${peor.rendimientoTHa} t/ha de ${nombreVariedad(peor.variedadId)} — una diferencia de ${Math.round((mejor.rendimientoTHa - peor.rendimientoTHa) * 10) / 10} t/ha.`,
      };
    },
  },
  {
    id: 'benchmark-zona',
    pregunta: '¿Cómo venimos respecto al promedio de la zona?',
    run() {
      const b = benchmarkZona(2025);
      const diff = Math.round((b.promedioPropio - b.promedioZona) * 10) / 10;
      return {
        toolName: 'benchmark_zona(campaña=2025)',
        args: { campaña: 2025, fuente: 'MAGyP Estimaciones Agrícolas (DEMO, no verificado)' },
        filas: [`Papasud 2025 · ${b.promedioPropio} t/ha`, `Promedio partido 2025 · ${b.promedioZona} t/ha (MAGyP, ilustrativo)`],
        respuesta: `Papasud rindió ${b.promedioPropio} t/ha en 2025, ${diff >= 0 ? Math.abs(diff) + ' t/ha por encima' : Math.abs(diff) + ' t/ha por debajo'} del promedio estimado del partido (${b.promedioZona} t/ha). Dato de zona ilustrativo — MAGyP no fue verificado contra la fuente.`,
      };
    },
  },
  {
    id: 'superficie-2025',
    pregunta: '¿Qué pasó con la superficie sembrada este año?',
    run() {
      const v = variacionAnual('superficieHa');
      return {
        toolName: 'variacion_anual(indicador="superficieHa")',
        args: { indicador: 'superficie sembrada' },
        filas: [`${v.previo} · ${Math.round(v.valPrevio)} ha`, `${v.ultimo} · ${Math.round(v.valUltimo)} ha`],
        respuesta: `La superficie sembrada cayó ${Math.abs(v.pct)}% entre ${v.previo} y ${v.ultimo} (de ${Math.round(v.valPrevio).toLocaleString('es-AR')} ha a ${Math.round(v.valUltimo).toLocaleString('es-AR')} ha).`,
      };
    },
  },
  {
    id: 'ambigua-rendimiento',
    pregunta: '¿Cómo rindió la papa este año?',
    run() {
      return {
        ambiguo: true,
        pregunta_aclaratoria: '¿Qué variedad? Tenemos campañas registradas de Innovator, Spunta, Atlantic, Daisy y Markies.',
        opciones: VARIEDADES.map(v => v.nombre),
      };
    },
  },
  {
    id: 'no-respondible-precio-futuro',
    pregunta: '¿Cuál va a ser el precio de exportación el año que viene?',
    run() {
      return {
        noRespondible: true,
        motivo: 'No tengo datos de precios ni proyecciones cargados — sólo rendimiento, superficie y producción por campaña. No puedo responder esto con los datos disponibles.',
      };
    },
  },
];
