/** Spanish running/done labels per tool name (thinking row + tool disclosure). */

export const TOOL_LABELS = {
  resumen_negocio: { running: "Mirando el negocio…", done: "Miró el negocio" },
  plata_en: { running: "Calculando la plata…", done: "Calculó la plata" },
  buscar_productos: { running: "Buscando productos…", done: "Buscó productos" },
  top_inmovilizado: { running: "Ordenando inmovilizado…", done: "Ordenó inmovilizado" },
  listar_grupo: { running: "Listando el grupo…", done: "Listó el grupo" },
  navegar_a: { running: "Preparando navegación…", done: "Navegó" },
  stock_ubicaciones: { running: "Consultando ubicaciones…", done: "Consultó ubicaciones" },
  consultar_lote: { running: "Leyendo el lote…", done: "Leyó el lote" },
  verificar_disponibilidad: { running: "Verificando stock…", done: "Verificó stock" },
  registrar_movimiento: { running: "Registrando movimiento…", done: "Registró movimiento" },
  explicar_diferencia: { running: "Analizando discrepancia…", done: "Analizó discrepancia" },
  consultar_manual: { running: "Consultando el manual…", done: "Consultó el manual" },
  generar_documento: { running: "Generando documento…", done: "Generó documento" },
  proponer_plan: { running: "Armando el plan…", done: "Armó el plan" },
  ejecutar_plan: { running: "Ejecutando el plan…", done: "Ejecutó el plan" },
  capital_recuperable: { running: "Calculando recuperable…", done: "Calculó recuperable" },
  mostrarGrafico: { running: "Armando el gráfico…", done: "Armó el gráfico" },
  mostrarTabla: { running: "Armando la tabla…", done: "Armó la tabla" },
  recordar: { running: "Guardando en la memoria…", done: "Guardó en la memoria" },
  recordar_hecho: { running: "Guardando lo que dijiste…", done: "Guardó lo que dijiste" },
};

export function toolLabels(name) {
  return TOOL_LABELS[name] ?? { running: `Consultando ${name}…`, done: name };
}
