// LA VISTA-HERRAMIENTA DE CADA ROL.
//
// Cuando alguien de Papasud entra (o el dueño usa "Ver como"), aterriza en SU
// pantalla de trabajo, no en un tablero de monitoreo ni en un chat vacío. Un
// operario parado adentro de una cámara a 4 grados con el celular en la mano no
// necesita ver el valor inmovilizado de la empresa: necesita decir lo que acaba
// de mover y que el sistema le confirme que había stock.
//
// Cada rol declara cuatro cosas:
//   (a) tareas   — qué tiene que hacer hoy (se DERIVAN de datos reales, ver piso.js)
//   (b) acciones — los botones con los que hace su trabajo
//   (c) chips    — las preguntas típicas de su oficio, pre-cargadas para Ángela
//   (d) lo que reporta hacia arriba — cada acción de tipo "reporte" entra al
//       sistema atribuida a la persona y el dueño la ve en su panel
//
// COHERENCIA CON «QUIÉN VE QUÉ»: cada acción y cada chip declara los features
// que necesita. Si el rol no los tiene habilitados en la matriz, eso no se
// muestra — la vista nunca ofrece algo que la matriz no permite.
//
// El rol se lee del TEXTO del rol (el del seed), no de una lista de usernames:
// una persona nueva con el mismo rol hereda su vista sin tocar código.

// El orden importa: "Encargado de depósito" matchea antes que "depósito" solo.
const CATALOGO = [
  {
    id: "encargado",
    match: /encargado/i,
    voz: true,
    acciones: [
      // Lo primero del encargado no es mirar un número: es cerrar lo que quedó
      // abierto. Un traslado sin confirmar en destino son kilos que no están en
      // ningún lado, y es la causa raíz del problema que este sistema resuelve.
      { id: "confirmar_traslados", icon: "PackageCheck", need: ["movimientos"],
        kind: "navegar", a: "movimientos", destaca: true },
      { id: "ver_diferencias", icon: "Scale", need: ["conciliacion"],
        kind: "navegar", a: "conciliacion" },
      { id: "marcar_conteo", icon: "ListChecks", need: ["conciliacion"],
        kind: "reporte", tipo: "conteo" },
    ],
    chips: [
      { k: "rol.chip_cuanto_hay", need: ["deposito"] },
      { k: "rol.chip_sin_confirmar", need: ["movimientos"] },
      { k: "rol.chip_por_que_falta", need: ["conciliacion"] },
    ],
  },
  {
    // NÉSTOR ES OTRO ROL AUNQUE TENGA EL MISMO PUESTO.
    // Entró hace tres semanas. Su problema no es registrar rápido: es no saber
    // todavía dónde va cada cosa. Matchea ANTES que "operario" y su vista
    // arranca por lo que le toca hoy y por preguntas de aprendizaje — las que
    // hoy le hace a un compañero y le cortan el trabajo a los dos.
    id: "nuevo",
    match: /galp[oó]n/i,
    voz: true,
    nuevo: true,
    acciones: [
      { id: "que_me_toca", icon: "ListChecks", need: ["deposito"],
        kind: "angela", pregunta: "rol.chip_que_me_toca", destaca: true },
      { id: "registrar_movimiento", icon: "ArrowLeftRight", need: ["movimientos"],
        kind: "navegar", a: "movimientos" },
      { id: "donde_va", icon: "Snowflake", need: ["deposito"],
        kind: "angela", pregunta: "rol.chip_donde_va" },
      { id: "reportar_faltante", icon: "TriangleAlert", need: ["deposito"],
        kind: "reporte", tipo: "faltante" },
    ],
    chips: [
      { k: "rol.chip_que_me_toca", need: ["deposito"] },
      { k: "rol.chip_donde_va", need: ["deposito"] },
      { k: "rol.chip_como_se_anota", need: ["movimientos"] },
      { k: "rol.chip_que_es_categoria", need: ["deposito"] },
    ],
  },
  {
    id: "operario",
    match: /operario|frigor[ií]fico|galp[oó]n/i,
    voz: true,
    acciones: [
      // La acción estrella del operario: contar lo que movió. Es N01, y es lo
      // único que tiene que saber hacer para que todo el resto funcione.
      { id: "registrar_movimiento", icon: "ArrowLeftRight", need: ["movimientos"],
        kind: "navegar", a: "movimientos", destaca: true },
      { id: "cargar_remito", icon: "Camera", need: ["cargar"],
        kind: "navegar", a: "cargar" },
      { id: "reportar_faltante", icon: "TriangleAlert", need: ["deposito"],
        kind: "reporte", tipo: "faltante" },
    ],
    chips: [
      { k: "rol.chip_donde_esta", need: ["deposito"] },
      { k: "rol.chip_cuanto_queda", need: ["deposito"] },
      { k: "rol.chip_que_sale_hoy", need: ["movimientos"] },
    ],
  },
  {
    id: "agronoma",
    match: /agr[oó]nom/i,
    acciones: [
      // La agrónoma responde por la sanidad y la categoría de cada lote: su
      // pantalla arranca por lo que está por vencer, no por el stock.
      { id: "analisis_por_vencer", icon: "FlaskConical", need: ["trazabilidad"],
        kind: "angela", pregunta: "rol.chip_analisis_vencen", destaca: true },
      { id: "ver_brotacion", icon: "Sprout", need: ["deposito"],
        kind: "angela", pregunta: "rol.chip_brotan" },
      { id: "marcar_observado", icon: "TriangleAlert", need: ["conciliacion"],
        kind: "reporte", tipo: "faltante" },
    ],
    chips: [
      { k: "rol.chip_analisis_vencen", need: ["trazabilidad"] },
      { k: "rol.chip_brotan", need: ["deposito"] },
      { k: "rol.chip_calibre_mal", need: ["inventario"] },
    ],
  },
  {
    id: "comercio_exterior",
    match: /comercio exterior|administraci|export/i,
    acciones: [
      // Su trabajo es la carpeta de cada embarque: arranca por la que está
      // frenada, porque es la que tiene fecha de contenedor.
      { id: "ver_embarques", icon: "Ship", need: ["logistica"],
        kind: "navegar", a: "logistica", destaca: true },
      { id: "armar_documentos", icon: "FileText", need: ["exportacion"],
        kind: "navegar", a: "exportacion" },
      { id: "trazabilidad_lote", icon: "Route", need: ["trazabilidad"],
        kind: "angela", pregunta: "rol.chip_pedigri" },
    ],
    chips: [
      { k: "rol.chip_embarque_frenado", need: ["logistica"] },
      { k: "rol.chip_falta_papel", need: ["exportacion"] },
      { k: "rol.chip_pedigri", need: ["trazabilidad"] },
    ],
  },
];


// EL DUEÑO NO TIENE VISTA-HERRAMIENTA, PERO SÍ TIENE OFICIO.
// Ernesto no registra movimientos: mira si el negocio cierra. Sus preguntas van
// aparte del CATALOGO porque `rolDe` devuelve null para el admin (su pantalla
// es el panel completo, no una vista de trabajo).
const CHIPS_DUENO = [
  { k: "rol.chip_3t_semana" },
  { k: "rol.chip_cuanto_hay" },
];

/** El rol-herramienta de una persona (null = el dueño, que tiene su propio panel). */
export function rolDe(user) {
  if (!user || user.es_admin) return null;
  const texto = user.rol || "";
  return CATALOGO.find((r) => r.match.test(texto)) || null;
}

/** ¿Esta persona aterriza en su vista de trabajo? */
export function tieneVistaHerramienta(user) {
  return rolDe(user) != null;
}

const tieneFeats = (user, need) =>
  (need || []).every((f) => (user?.features || []).includes(f));

/** Las acciones que este rol puede USAR de verdad (según «Quién ve qué»). */
export function accionesDe(user) {
  const r = rolDe(user);
  if (!r) return [];
  return r.acciones.filter((a) => tieneFeats(user, a.need));
}

/** ¿Este rol REPORTA por voz desde el piso?
 *
 *  Hay dos usos distintos de la misma voz, y conviene no confundirlos:
 *
 *    · CONSULTAR — "¿cuántos bolsones quedan de ese lote?". Eso lo quiere
 *      cualquiera, y por eso el micrófono del chat de Ángela no tiene gate:
 *      está para todos, del dueño para abajo.
 *
 *    · REPORTAR — "pasé dieciocho bolsones al galpón". Eso es trabajo de piso:
 *      entra por `piso.reportar` o por el riel de movimientos y termina en una
 *      propuesta que alguien confirma. Sólo tiene sentido para quien está
 *      parado frente a los bolsones, y por eso el botón de voz de la vista de
 *      trabajo sí se pregunta por el rol.
 *
 *  Sale del rol y no de una feature porque no es un permiso: es una forma de
 *  trabajar. */
export function reportaPorVoz(user) {
  return !!rolDe(user)?.voz;
}

/** Las preguntas pre-cargadas de su oficio (sólo las que su rol puede responder). */
export function chipsDe(user) {
  const r = rolDe(user);
  if (!r) return [];
  return r.chips.filter((c) => tieneFeats(user, c.need));
}

/** Los campos de cada formulario de reporte: qué le pedimos al que está parado
 *  adentro de la cámara. Corto — se completa con una mano y con guantes. */
export const CAMPOS_REPORTE = {
  faltante: [
    { id: "producto", lk: "rol.f_lote", tipo: "texto", requerido: true },
    { id: "cantidad", lk: "rol.f_bolsones", tipo: "numero", requerido: true },
    { id: "motivo", lk: "rol.f_motivo", tipo: "opciones",
      opciones: [
        { v: "roto", lk: "rol.motivo_roto" },
        { v: "faltante", lk: "rol.motivo_faltante" },
        { v: "vencido", lk: "rol.motivo_brotado" },
        { v: "no_pedido", lk: "rol.motivo_no_pedido" },
      ] },
    { id: "nota", lk: "rol.f_nota", tipo: "texto" },
  ],
  conteo: [
    { id: "producto", lk: "rol.f_lote", tipo: "texto", requerido: true },
    { id: "contado", lk: "rol.f_contado", tipo: "numero", requerido: true },
    { id: "nota", lk: "rol.f_nota", tipo: "texto" },
  ],
  entrega: [
    { id: "cliente", lk: "rol.f_cliente", tipo: "texto", requerido: true },
    // La PRUEBA: foto del remito firmado. Es el respaldo de quien cargó si
    // después el cliente dice que no recibió. Opcional: sin foto igual se
    // confirma — pedirla como obligatoria haría que nadie confirme nada.
    { id: "prueba", lk: "rol.f_prueba", tipo: "foto" },
    { id: "nota", lk: "rol.f_nota_entrega", tipo: "texto" },
  ],
  reposicion: [
    { id: "producto", lk: "rol.f_lote", tipo: "texto", requerido: true },
    { id: "cantidad", lk: "rol.f_bolsones", tipo: "numero" },
    { id: "nota", lk: "rol.f_nota", tipo: "texto" },
  ],
  pedido: [
    { id: "cliente", lk: "rol.f_cliente", tipo: "texto", requerido: true },
    { id: "nota", lk: "rol.f_nota_pedido", tipo: "texto" },
  ],
};


/** Las preguntas que Ángela ofrece a ESTA persona, en su oficio.
 *
 *  Una sola fuente para el chat de desktop, el de mobile y la vista de trabajo.
 *  Antes cada pantalla traía su propia lista hardcodeada y por eso el dueño de
 *  una semillera se encontraba con "¿cuánta plata tengo en manteca?".
 *
 *  Devuelve {lk, enviar}: `lk` es lo que se MUESTRA y `enviar` es el payload —
 *  acá son la misma frase, porque el producto es en castellano. */
export function chipsAngelaDe(user) {
  const r = rolDe(user);
  const base = r ? r.chips.filter((c) => tieneFeats(user, c.need)) : CHIPS_DUENO;
  return base.map((c) => ({ lk: c.k, enviarLk: c.k }));
}

/** El saludo con el que Ángela abre para esta persona. */
export function saludoKeyDe(user) {
  const r = rolDe(user);
  if (!r) return "angela.saludo_dueno";
  return `angela.saludo_${r.id}`;
}
