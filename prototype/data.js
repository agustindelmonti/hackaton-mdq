// ============================================================
// Datos de dominio — Papasud (mock, para el prototipo visual).
// Escalera de subcategorías y regla de linaje: ver
// docs/papa-semilla-modelo-de-datos.md. Números en disputa
// (norma exacta) deliberadamente NO se citan en la UI.
// ============================================================

const KG_POR_BOLSON = 700;

const SUBCATEGORIAS = [
  { id: 'preinicial_0', nombre: 'Preinicial 0', categoria: 'Básica' },
  { id: 'preinicial_I', nombre: 'Preinicial I', categoria: 'Básica' },
  { id: 'preinicial_II', nombre: 'Preinicial II', categoria: 'Básica' },
  { id: 'inicial_I', nombre: 'Inicial I', categoria: 'Básica' },
  { id: 'inicial_II', nombre: 'Inicial II', categoria: 'Básica' },
  { id: 'inicial_III', nombre: 'Inicial III', categoria: 'Básica' },
  { id: 'fundacion', nombre: 'Fundación', categoria: 'Básica' },
  { id: 'registrada', nombre: 'Registrada', categoria: 'Certificada' },
  { id: 'certificada_A', nombre: 'Certificada A', categoria: 'Certificada' },
  { id: 'certificada_B', nombre: 'Certificada B', categoria: 'Certificada' },
];
const SUB_INDEX = Object.fromEntries(SUBCATEGORIAS.map((s, i) => [s.id, i]));

function linajeValido(padreSub, hijoSub) {
  return SUB_INDEX[padreSub] <= SUB_INDEX[hijoSub];
}

const VARIEDADES = [
  { id: 'innovator', nombre: 'Innovator', obtentor: 'HZPC', uso: 'industria' },
  { id: 'spunta', nombre: 'Spunta', obtentor: 'INTA', uso: 'fresco' },
  { id: 'atlantic', nombre: 'Atlantic', obtentor: 'USDA / dominio público', uso: 'industria' },
  { id: 'daisy', nombre: 'Daisy', obtentor: 'HZPC', uso: 'industria' },
  { id: 'markies', nombre: 'Markies', obtentor: 'Meijer', uso: 'industria' },
];

const UBICACIONES = [
  { id: 'frig_ta', nombre: 'Frigorífico Tres Arroyos', tipo: 'frigorifico', localidad: 'Tres Arroyos', provincia: 'Buenos Aires', apodo: 'frigorífico 1' },
  { id: 'frig_gc', nombre: 'Frigorífico Gonzales Chaves', tipo: 'frigorifico', localidad: 'Gonzales Chaves', provincia: 'Buenos Aires', apodo: 'frigorífico 2' },
  { id: 'frig_sc', nombre: 'Frigorífico San Cayetano', tipo: 'frigorifico', localidad: 'San Cayetano', provincia: 'Buenos Aires', apodo: 'frigorífico 3' },
  { id: 'galpon_gp', nombre: 'Galpón General Pueyrredón', tipo: 'galpon', localidad: 'General Pueyrredón', provincia: 'Buenos Aires', apodo: 'galpón' },
];

// Curva de merma no lineal — placeholder a calibrar con datos reales.
// El punto (22, 4.5) reproduce el ejemplo de docs/papa-semilla-modelo-de-datos.md.
const MERMA_CURVA = [
  { dias: 0, pct: 0 },
  { dias: 10, pct: 2.0 },
  { dias: 22, pct: 4.5 },
  { dias: 30, pct: 5.0 },
  { dias: 60, pct: 5.8 },
  { dias: 90, pct: 6.6 },
  { dias: 120, pct: 7.1 },
  { dias: 180, pct: 7.4 },
];

function mermaEsperadaPct(dias) {
  if (dias <= 0) return 0;
  const curve = MERMA_CURVA;
  if (dias >= curve[curve.length - 1].dias) return curve[curve.length - 1].pct;
  for (let i = 0; i < curve.length - 1; i++) {
    const a = curve[i], b = curve[i + 1];
    if (dias >= a.dias && dias <= b.dias) {
      const frac = (dias - a.dias) / (b.dias - a.dias);
      return a.pct + frac * (b.pct - a.pct);
    }
  }
  return curve[curve.length - 1].pct;
}

// ---------- Generación de ~24 lotes con linaje ----------
function buildLotes() {
  const lotes = [];
  let n = 1;
  function addLote(subId, variedadId, padreId, zona) {
    const id = String(n++);
    lotes.push({
      id,
      nroLote: id,
      variedadId,
      subcategoria: subId,
      zonaProduccion: zona,
      anioCosecha: 2024 + (n % 2),
      lotePadreId: padreId,
      semillero: 'Papasud',
      nroInscripcion: `RNC-${1000 + n}`,
    });
    return id;
  }

  // Cadenas de linaje: preinicial -> ... -> registrada (G3 comercial)
  const chains = [
    ['innovator', 'Santa Cruz'],
    ['spunta', 'Buenos Aires'],
    ['atlantic', 'Santa Cruz'],
  ];
  chains.forEach(([variedadId, zona]) => {
    const p0 = addLote('preinicial_0', variedadId, null, zona);
    const p1 = addLote('preinicial_I', variedadId, p0, zona);
    const iniI = addLote('inicial_I', variedadId, p1, zona);
    const iniII = addLote('inicial_II', variedadId, iniI, zona);
    const fund = addLote('fundacion', variedadId, iniII, zona);
    const reg = addLote('registrada', variedadId, fund, zona); // G3 comercial
    addLote('certificada_A', variedadId, reg, zona);
  });

  // Lotes sueltos adicionales para poblar el catálogo
  const extra = [
    ['daisy', 'inicial_III', 'Buenos Aires'],
    ['markies', 'fundacion', 'Buenos Aires'],
    ['spunta', 'registrada', 'Santa Cruz'],
  ];
  extra.forEach(([v, s, z]) => addLote(s, v, null, z));

  return lotes;
}

const LOTES = buildLotes();
const LOTE_BY_ID = Object.fromEntries(LOTES.map(l => [l.id, l]));

// ---------- Libro append-only de movimientos ----------
// origenId=null => ingreso/cosecha. destinoId=null => egreso/despacho.
let movSeq = 1;
function mkMov({ loteId, origenId, destinoId, kg, fuente, confianza, confirmadoPor, transcripcion, diasAtras }) {
  const fecha = new Date();
  fecha.setDate(fecha.getDate() - (diasAtras || 0));
  return {
    id: movSeq++,
    loteId, origenId, destinoId, kg,
    fecha: fecha.toISOString(),
    usuario: confirmadoPor ? 'Operario Depósito' : 'Sistema (seed)',
    fuente: fuente || 'importacion',
    transcripcion: transcripcion || null,
    confianza: confianza || 'alta',
    confirmadoPor: confirmadoPor || 'seed',
  };
}

const MOVIMIENTOS = [];

// Baseline: cada lote ingresa a una ubicación con stock razonable.
LOTES.forEach((lote, idx) => {
  const ubic = UBICACIONES[idx % UBICACIONES.length];
  const bolsones = 10 + (idx * 3) % 40;
  MOVIMIENTOS.push(mkMov({
    loteId: lote.id, origenId: null, destinoId: ubic.id,
    kg: bolsones * KG_POR_BOLSON, diasAtras: 45 + idx * 3,
  }));
});

// Escenario Flow C (bloqueo de remito): lote 8 con stock muy justo en Tres Arroyos.
// Sobreescribe: dejamos sólo 480kg netos ahí.
(function seedLote8() {
  const loteId = '8';
  // limpiar movimiento baseline de ese lote si cae en frig_ta, forzar 480kg netos
  const idx = MOVIMIENTOS.findIndex(m => m.loteId === loteId);
  if (idx >= 0) MOVIMIENTOS.splice(idx, 1);
  MOVIMIENTOS.push(mkMov({ loteId, origenId: null, destinoId: 'frig_ta', kg: 1200, diasAtras: 40 }));
  MOVIMIENTOS.push(mkMov({ loteId, origenId: 'frig_ta', destinoId: 'galpon_gp', kg: 720, diasAtras: 5, fuente: 'voz', confianza: 'alta', confirmadoPor: 'Operario Depósito' }));
  // saldo neto en frig_ta: 1200 - 720 = 480kg
})();

// Escenario Flow B (discrepancia de merma): lote 17 con 20 bolsones (14.000kg)
// declarados en Gonzales Chaves hace 22 días. Coincide con el ejemplo de los docs.
(function seedLote17() {
  const loteId = '17';
  const idx = MOVIMIENTOS.findIndex(m => m.loteId === loteId);
  if (idx >= 0) MOVIMIENTOS.splice(idx, 1);
  MOVIMIENTOS.push(mkMov({ loteId, origenId: null, destinoId: 'frig_gc', kg: 20 * KG_POR_BOLSON, diasAtras: 22 }));
})();

// Escenario Flow A (voz): aseguramos que el lote 42... no existe en el catálogo (~21 lotes),
// así que lo usamos como alias narrativo del lote 6 (registrada, con stock cómodo en Gonzales Chaves).
const LOTE_VOZ_DEMO_ID = '6';
(function seedLoteVozDemo() {
  const idx = MOVIMIENTOS.findIndex(m => m.loteId === LOTE_VOZ_DEMO_ID);
  if (idx >= 0) MOVIMIENTOS.splice(idx, 1);
  MOVIMIENTOS.push(mkMov({ loteId: LOTE_VOZ_DEMO_ID, origenId: null, destinoId: 'frig_gc', kg: 20000, diasAtras: 50 }));
})();

// Discrepancia sin resolver ya cargada (para el feed de alertas del tablero):
// movimiento de salida sin espejo en destino -> candidato a "excede_merma" / posible omisión.
(function seedAlertaPendiente() {
  MOVIMIENTOS.push(mkMov({
    loteId: '10', origenId: 'frig_sc', destinoId: null, kg: 400, diasAtras: 10,
    fuente: 'voz', confianza: 'dudosa', confirmadoPor: 'Operario Depósito',
    transcripcion: 'salieron cuatrocientos kilos del lote diez, no me acuerdo bien el destino',
  }));
})();

const CONTEOS = [];

// Un par de conteos históricos ya cargados para el lote 17, así el
// Historial y el gráfico de evolución no arrancan vacíos en la demo.
// Mismos números que el ejemplo de discrepancia (13.100kg a los 22
// días) para que ambas pantallas cuenten la misma historia.
(function seedConteosDemo() {
  const ingresoLote17 = new Date();
  ingresoLote17.setDate(ingresoLote17.getDate() - 22);
  const fechaA = new Date(ingresoLote17); fechaA.setDate(fechaA.getDate() + 10);
  const fechaB = new Date(ingresoLote17); fechaB.setDate(fechaB.getDate() + 22);
  CONTEOS.push(
    { id: 1, loteId: '17', ubicacionId: 'frig_gc', kgContado: 13700, kgEsperado: 13720, tolerancia: 140, delta: -20, clasificacion: 'dentro_de_merma', confianza: 'alta', fecha: fechaA.toISOString(), usuario: 'Operario Depósito' },
    { id: 2, loteId: '17', ubicacionId: 'frig_gc', kgContado: 13100, kgEsperado: 13370, tolerancia: 140, delta: -270, clasificacion: 'excede_merma', confianza: 'alta', fecha: fechaB.toISOString(), usuario: 'Operario Depósito' }
  );
})();

// ============================================================
// Documentación de exportación — pantalla de cierre (N03).
// Requisitos por país: mock a partir de docs/papasud-features-y-flows.md
// (secc. "El set documental de exportación" y "Fricciones de mercado").
// Los % de tolerancia sanitaria y anexos NO están publicados online:
// marcados DEMO, nunca presentados con tono de autoridad.
// ============================================================
const NCM_SEMILLA = '0701.10.00';
const NCM_CONSUMO = '0701.90.00';

const PAISES_DESTINO = [
  { id: 'brasil', nombre: 'Brasil', canal: 'ePhyto', requiereLavado: true, plagaAdicional: 'Nematodos (declaración adicional MERCOSUR/GMC Res. 29/22)' },
  { id: 'uruguay', nombre: 'Uruguay', canal: 'CERT-POV', requiereLavado: true, plagaAdicional: 'Nematodos' },
  { id: 'vietnam', nombre: 'Vietnam', canal: 'CERT-POV', requiereLavado: false, plagaAdicional: 'Roya (Phytophthora) — requisito propio de la ONPF de destino' },
  { id: 'egipto', nombre: 'Egipto', canal: 'CERT-POV', requiereLavado: false, plagaAdicional: 'Mercado aún no abierto por SENASA — DEMO, no operar sobre este destino' },
];

// Vencimiento del certificado INASE: mock determinístico por lote
// (no hay dato real de postcontrol en el prototipo).
function certificadoInaseInfo(loteId) {
  const vencido = parseInt(loteId) % 3 === 0;
  const dias = vencido ? -14 : 320;
  const fecha = new Date();
  fecha.setDate(fecha.getDate() + dias);
  return { vencido, fecha };
}
