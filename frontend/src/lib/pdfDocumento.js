// ============================================================================
// EL PDF QUE EL DUEÑO MIRA Y DICE "ESTO LO MANDO MAÑANA".
// ----------------------------------------------------------------------------
// Antes esto era una pila de líneas de texto: `linea("Razón social: PAPASUD")`,
// una debajo de la otra, sin una sola regla ni una tabla. Servía para probar
// que los datos estaban; no servía para mandarlo a un despachante.
//
// Un documento de exportación tiene una forma esperada y quien lo recibe la
// reconoce antes de leerlo:
//
//   · MEMBRETE con el logo y los datos fiscales del exportador
//   · NÚMERO CORRELATIVO y fecha, arriba a la derecha, donde se buscan
//   · SECCIONES rotuladas, con etiqueta y valor alineados en dos columnas
//   · TABLA de mercadería con encabezado, filas cebradas y números a la derecha
//   · TOTALES en su recuadro
//   · FIRMA Y SELLO — un papel sin lugar para firmar no es un papel
//   · PIE con la nota legal, la paginación y de dónde salió
//
// Los CAMPOS QUE FALTAN se imprimen como una línea de puntos para completar a
// mano, no como un hueco: así el documento sirve igual y se ve qué falta.
//
// El logo se rasteriza del SVG en un canvas — jsPDF no dibuja SVG. Si el
// navegador no puede (CSP, SVG roto), cae a la marca tipográfica y el PDF sale
// igual: nunca se rompe la descarga por el logo.
// ============================================================================

const A4 = { w: 210, h: 297 };
const M = 16;                              // margen
const ANCHO = A4.w - M * 2;
const MARINO = [30, 47, 111];
const TINTA = [33, 32, 29];
const SUAVE = [110, 106, 99];
const LINEA = [214, 210, 202];
const CEBRA = [246, 244, 240];

/** El logo del cliente, rasterizado. Devuelve {dataUrl, w, h} en mm, o null. */
async function rasterizarLogo(src, altoMm = 12) {
  try {
    const img = new Image();
    img.crossOrigin = "anonymous";
    await new Promise((ok, fail) => {
      img.onload = ok;
      img.onerror = fail;
      img.src = src;
    });
    const escala = 6;                       // px por mm: nítido al imprimir
    const ratio = (img.naturalWidth || 1) / (img.naturalHeight || 1);
    const anchoMm = altoMm * ratio;
    const c = document.createElement("canvas");
    c.width = Math.round(anchoMm * escala);
    c.height = Math.round(altoMm * escala);
    const ctx = c.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.drawImage(img, 0, 0, c.width, c.height);
    return { dataUrl: c.toDataURL("image/png"), w: anchoMm, h: altoMm };
  } catch {
    return null;                            // sin logo, marca de texto
  }
}

export async function generarPdfDocumento({ doc, carpeta, empresa, logo, t }) {
  const { jsPDF } = await import("jspdf");
  const pdf = new jsPDF({ unit: "mm", format: "a4" });
  const marca = await rasterizarLogo(logo || "/logos/papasud.svg", 13);

  let y = 0;
  const paginas = [];

  const font = (bold = false, size = 9, color = TINTA) => {
    pdf.setFont("helvetica", bold ? "bold" : "normal");
    pdf.setFontSize(size);
    pdf.setTextColor(...color);
  };

  const nuevaPagina = () => {
    pdf.addPage();
    paginas.push(pdf.getNumberOfPages());
    y = M;
    banda();
  };

  /** Deja lugar para `alto` mm; si no entra, pasa de página. */
  const espacio = (alto) => {
    // A4.h - 20 = arriba del pie de página, no del borde del papel.
    if (y + alto > A4.h - 20) nuevaPagina();
  };

  const banda = () => {
    pdf.setFillColor(...MARINO);
    pdf.rect(0, 0, A4.w, 2.6, "F");
  };

  const parrafo = (txt, { size = 8.6, bold = false, color = TINTA, gap = 4.2, x = M, ancho = ANCHO } = {}) => {
    font(bold, size, color);
    for (const l of pdf.splitTextToSize(String(txt ?? ""), ancho)) {
      espacio(gap);
      pdf.text(l, x, y);
      y += gap;
    }
  };

  // ---------------------------------------------------------------- MEMBRETE
  banda();
  y = M;
  const yMembrete = y;
  if (marca) {
    pdf.addImage(marca.dataUrl, "PNG", M, y - 1, marca.w, marca.h);
  } else {
    font(true, 15, MARINO);
    pdf.text(String(empresa || "PAPASUD S.A.").toUpperCase(), M, y + 6);
  }

  // los datos fiscales, a la derecha: es donde los busca un despachante
  const datos = [
    "CUIT 30-54187629-3",
    "RNCyFS N° 14.328 · Punto de venta exportación 0004",
    "Ruta 226 km 14,5 — Sierra de los Padres",
    "B7600 Mar del Plata, Buenos Aires, Argentina",
    "comercioexterior@papasud.com.ar · +54 223 400-0000",
  ];
  font(false, 7.2, SUAVE);
  let yd = yMembrete + 1;
  for (const l of datos) {
    pdf.text(l, A4.w - M, yd, { align: "right" });
    yd += 3.1;
  }
  y = Math.max(yMembrete + (marca ? marca.h : 9), yd) + 3;

  pdf.setDrawColor(...MARINO);
  pdf.setLineWidth(0.5);
  pdf.line(M, y, A4.w - M, y);
  y += 6.5;

  // ------------------------------------------------------------ TÍTULO + N°
  font(true, 13, MARINO);
  pdf.text(String(doc.titulo || "").toUpperCase(), M, y);
  if (doc.numero) {
    font(true, 9.5, TINTA);
    pdf.text(`N° ${doc.numero}`, A4.w - M, y, { align: "right" });
  }
  y += 4.6;
  font(false, 8, SUAVE);
  if (doc.subtitulo) pdf.text(doc.subtitulo, M, y);
  if (doc.emitido) {
    pdf.text(`${t("pdf.emitido")}: ${fechaLarga(doc.emitido)}`, A4.w - M, y, { align: "right" });
  }
  y += 4.2;
  font(false, 8, SUAVE);
  pdf.text(
    [carpeta.orden, carpeta.cliente, carpeta.pais].filter(Boolean).join("  ·  "),
    M, y);
  if (doc.organismo) pdf.text(doc.organismo, A4.w - M, y, { align: "right" });
  y += 7;

  // ------------------------------------------------------------- SECCIONES
  const filaCampo = (etiqueta, valor, falta) => {
    // La etiqueta TAMBIÉN se parte en líneas. Antes se imprimía de un tirón y
    // "Nombre y dirección declarada del consignatario" se metía por encima del
    // valor: dos textos superpuestos en un certificado del SENASA.
    const anchoEtq = 56;
    const xv = M + anchoEtq;
    const anchoVal = ANCHO - anchoEtq - 4;
    font(false, 7.6, SUAVE);
    const lEtq = pdf.splitTextToSize(String(etiqueta || ""), anchoEtq - 5);
    font(true, 8.4, TINTA);
    const lVal = falta ? ["."] : pdf.splitTextToSize(String(valor), anchoVal);
    const alto = Math.max(5.4, Math.max(lEtq.length, lVal.length) * 4.1 + 1.3);
    espacio(alto);
    font(false, 7.6, SUAVE);
    pdf.text(lEtq, M + 2, y);
    if (falta) {
      font(false, 8, SUAVE);
      pdf.text(".".repeat(70), xv, y, { maxWidth: anchoVal });
    } else {
      font(true, 8.4, TINTA);
      pdf.text(lVal, xv, y);
    }
    y += alto;
  };

  for (const s of doc.secciones || []) {
    espacio(14);
    pdf.setFillColor(...MARINO);
    pdf.rect(M, y - 3.4, ANCHO, 5.4, "F");
    font(true, 7.6, [255, 255, 255]);
    pdf.text(String(s.titulo || "").toUpperCase(), M + 2, y);
    y += 6.4;
    for (const c of s.campos || []) {
      const v = Array.isArray(c.valor) ? c.valor.join(" · ") : c.valor;
      filaCampo(c.etiqueta, v, v == null || v === "");
    }
    y += 2.4;
  }

  // ---------------------------------------------------------------- ITEMS
  // La tabla de mercadería es lo que mira primero el que recibe el papel. Tres
  // cosas la hacen legible y las tres faltaban: encabezados en castellano con
  // sus tildes, números con separador de miles y a la derecha, y anchos por
  // COLUMNA (el lote no puede comerse el espacio del importe).
  if (doc.items?.length) {
    const cols = Object.keys(doc.items[0]).filter((k) => k !== "fuente");
    const fijo = {
      codigo: 30, lote: 30, ncm: 20, cantidad: 20, unidad: 10, kg: 22,
      bultos: 18, bolsones: 20, precio_unitario: 24, importe: 26,
      peso_neto: 22, peso_bruto: 22, calibre: 20, grado: 16, categoria: 26,
    };
    const usado = cols.reduce((n, k) => n + (fijo[k] || 0), 0);
    const flex = cols.filter((k) => !fijo[k]);
    const anchoFlex = flex.length ? (ANCHO - usado) / flex.length : 0;
    const w = (k) => fijo[k] || anchoFlex;
    const x0 = [];
    let acc = M;
    for (const k of cols) { x0.push(acc); acc += w(k); }

    espacio(18);
    font(true, 8.6, MARINO);
    pdf.text(t("pdf.detalle").toUpperCase(), M, y);
    y += 4.4;

    pdf.setFillColor(...MARINO);
    pdf.rect(M, y - 3.4, ANCHO, 5.2, "F");
    font(true, 7, [255, 255, 255]);
    cols.forEach((k, i) => {
      const etq = etiquetaCol(k);
      if (esNumerica(doc.items, k)) pdf.text(etq, x0[i] + w(k) - 2, y, { align: "right" });
      else pdf.text(etq, x0[i] + 2, y);
    });
    y += 5.4;

    doc.items.forEach((it, fila) => {
      // cada fila se mide antes de dibujarse: una descripción larga ocupa dos
      // renglones y el cebrado tiene que cubrir los dos
      const celdas = cols.map((k, i) => {
        const num = esNumerica(doc.items, k);
        const txt = it[k] == null ? "—" : num ? formatoNum(it[k]) : String(it[k]);
        return { k, i, num, lineas: num ? [txt] : pdf.splitTextToSize(txt, w(k) - 4).slice(0, 2) };
      });
      const alto = Math.max(...celdas.map((c) => c.lineas.length)) * 3.9 + 1.6;
      espacio(alto + 2);
      if (fila % 2 === 1) {
        pdf.setFillColor(...CEBRA);
        pdf.rect(M, y - 3.4, ANCHO, alto, "F");
      }
      font(false, 7.4, TINTA);
      for (const c of celdas) {
        if (c.num) pdf.text(c.lineas[0], x0[c.i] + w(c.k) - 2, y, { align: "right" });
        else pdf.text(c.lineas, x0[c.i] + 2, y);
      }
      y += alto;
    });
    pdf.setDrawColor(...LINEA);
    pdf.setLineWidth(0.25);
    pdf.line(M, y - 3.2, A4.w - M, y - 3.2);
    y += 3;
  }

  // -------------------------------------------------------------- TOTALES
  if (doc.totales?.length) {
    const alto = doc.totales.length * 5 + 5;
    espacio(alto + 3);
    const ancho = 84;
    const x = A4.w - M - ancho;
    pdf.setDrawColor(...MARINO);
    pdf.setLineWidth(0.4);
    pdf.rect(x, y - 3.6, ancho, alto);
    let yt = y;
    for (const c of doc.totales) {
      font(false, 8, SUAVE);
      pdf.text(String(c.etiqueta), x + 3, yt);
      font(true, 9, TINTA);
      pdf.text(String(c.valor ?? "—"), x + ancho - 3, yt, { align: "right" });
      yt += 5;
    }
    y = yt + 4;
  }

  // ------------------------------------------------------------- PIE DE DOC
  for (const c of doc.pie || []) {
    filaCampo(c.etiqueta, c.valor, c.valor == null || c.valor === "");
  }

  // ------------------------------------------------------- FIRMA Y SELLO
  // Un papel de exportación sin lugar para firmar y sellar no lo toma nadie.
  y += 5;
  espacio(26);
  const anchoF = (ANCHO - 8) / 2;
  const firmas = [
    { rotulo: t("pdf.firma_exportador"), aclaracion: String(empresa || "Papasud S.A.") },
    { rotulo: t("pdf.firma_dt"), aclaracion: t("pdf.firma_dt_aclara") },
  ];
  firmas.forEach((f, i) => {
    const x = M + i * (anchoF + 8);
    pdf.setDrawColor(...LINEA);
    pdf.setLineWidth(0.3);
    pdf.rect(x, y, anchoF, 22);
    font(false, 6.8, SUAVE);
    pdf.text(f.rotulo.toUpperCase(), x + 2.5, y + 4);
    pdf.setDrawColor(...SUAVE);
    pdf.line(x + 4, y + 15, x + anchoF - 4, y + 15);
    font(false, 6.8, SUAVE);
    pdf.text(f.aclaracion, x + 4, y + 18.5);
  });
  y += 27;

  // -------------------------------------------------------------- NOTA LEGAL
  if (doc.nota_legal) {
    espacio(10);
    pdf.setDrawColor(...LINEA);
    pdf.setLineWidth(0.25);
    pdf.line(M, y - 2, A4.w - M, y - 2);
    y += 2;
    parrafo(doc.nota_legal, { size: 6.8, color: SUAVE, gap: 3.1 });
  }

  // -------------------------------------------------------------- PIE (todas)
  const total = pdf.getNumberOfPages();
  for (let p = 1; p <= total; p++) {
    pdf.setPage(p);
    pdf.setDrawColor(...LINEA);
    pdf.setLineWidth(0.25);
    pdf.line(M, A4.h - 14, A4.w - M, A4.h - 14);
    font(false, 6.6, SUAVE);
    pdf.text(
      [doc.numero, carpeta.orden, String(empresa || "Papasud S.A.")].filter(Boolean).join("  ·  "),
      M, A4.h - 10);
    pdf.text(t("pdf.pagina", { n: p, total }), A4.w - M, A4.h - 10, { align: "right" });
    pdf.text(t("pdf.generado"), A4.w / 2, A4.h - 6.5, { align: "center" });
  }

  pdf.save(`${doc.numero || carpeta.orden + "-" + doc.id}.pdf`);
}

// Los rótulos de columna en castellano. Sin esto el encabezado del papel dice
// "codigo descripcion ncm" — se lee como un volcado de base de datos.
const ETIQUETA_COL = {
  codigo: "Lote", lote: "Lote", descripcion: "Descripción", ncm: "NCM",
  cantidad: "Cantidad", unidad: "Un.", precio_unitario: "Precio unit.",
  importe: "Importe", kg: "Kilos", bultos: "Bultos", bolsones: "Bolsones",
  peso_neto: "Peso neto", peso_bruto: "Peso bruto", calibre: "Calibre",
  grado: "Grado", categoria: "Categoría", variedad: "Variedad",
  campania: "Campaña", ubicacion: "Ubicación", camara: "Cámara",
};

function etiquetaCol(k) {
  if (ETIQUETA_COL[k]) return ETIQUETA_COL[k];
  const s = k.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/** ¿La columna es numérica? Se decide por los DATOS, no por el nombre. */
function esNumerica(items, k) {
  return items.some((it) => typeof it[k] === "number");
}

const NUM_AR = new Intl.NumberFormat("es-AR", { maximumFractionDigits: 2 });
function formatoNum(v) {
  return typeof v === "number" ? NUM_AR.format(v) : String(v);
}

function fechaLarga(iso) {
  try {
    const d = new Date(iso + "T00:00:00");
    return d.toLocaleDateString("es-AR", { day: "2-digit", month: "long", year: "numeric" });
  } catch {
    return iso;
  }
}
