
**Contexto:** Papasud (empresa familiar de 140 años, semilla de papa, ~200 ha, 7.500 ton/ciclo, 25-30% exportación) propone 3 verticales de problemas reales de su operación diaria para que los equipos construyan prototipos en un día, usando IA.

**Las 3 verticales**, cada una con 3 niveles (Inicial → Intermedio → Avanzado):

1. **El cerebro de Papasud** (datos): 20+ años de historia viven en un Excel inmanejable.

- N01: copiloto conversacional sobre datos históricos
- N02: panel de indicadores con resúmenes automáticos
- N03: modelo predictivo de aptitud de semilla según clima/ubicación

2. **Campo inteligente** (operación en terreno): órdenes de trabajo se arman manualmente después de la jornada.

- N01: generar órdenes de trabajo por voz/texto libre
- N02: vincular fotos del lote automáticamente con reconocimiento de estado del cultivo
- N03: detección de anomalías cruzando imágenes satelitales con órdenes activas

3. **Stock, trazabilidad y compliance**: stock repartido en 4 ubicaciones, planilla compartida propensa a errores.

- N01: registrar movimientos de stock por voz/texto
- N02: vista única de stock en tiempo real con hipótesis de discrepancias
- N03: copiloto para documentación de exportación (facturas proforma, trazabilidad)

**Sobre tu pregunta:** el documento no lo dice explícitamente ("solo se podrá competir en estas verticales"), pero por cómo está estructurado — título "verticales & niveles", la sección de niveles explicando que cada equipo elige un nivel de dificultad, y que estos son los desafíos "para sponsoreo y jurado" — todo indica que sí, estas 3 verticales (con sus 9 sub-desafíos) son el temario oficial de la competencia, no ejemplos ilustrativos. También aclara que falta definir una etapa aparte: qué assets (datos, fotos, accesos) va a proveer Papasud el día del evento.

## Actores del sistema

- **Operario de campo** — ingeniero agrónomo que reporta actividad desde el lote
- **Operario de depósito** — mueve stock entre las 4 ubicaciones
- **Analista/gerencia** — consulta históricos, indicadores, toma decisiones
- **Administrativo de exportación** — genera documentación para clientes/organismos
- **Sistema/Agente IA** — interpreta lenguaje, detecta anomalías, genera explicaciones

---

## Vertical 01 — El cerebro de Papasud

**Features refinadas:**

- F1.1 — Chat de consulta en lenguaje natural (texto y voz) sobre el histórico
- F1.2 — Motor de traducción pregunta→consulta (text-to-SQL o RAG sobre datos estructurados)
- F1.3 — Respuesta con cita de fuente (qué campaña/registro sustenta el número)
- F1.4 — Dashboard de indicadores (rendimiento, superficie, producción) por año/variedad
- F1.5 — Generación automática de resumen narrativo de variaciones año a año
- F1.6 — (N03) Modelo predictivo de aptitud de semilla por lote/clima
- F1.7 — (N03) Explicación en lenguaje natural de la predicción para un agrónomo

**Casos de uso:**

- UC1.1 — Consultar rendimiento histórico de una variedad en una campaña específica
- UC1.2 — Comparar rendimiento entre dos campañas o variedades
- UC1.3 — Ver evolución de un indicador en el dashboard y leer el resumen automático
- UC1.4 — Pedir una proyección de aptitud de una variedad para un lote nuevo

---

## Vertical 02 — Campo inteligente

**Features refinadas:**

- F2.1 — Captura de orden de trabajo por voz/texto libre
- F2.2 — Extracción de entidades (lote, tarea, insumo, dosis, fecha) con validación contra diccionario
- F2.3 — Confirmación/corrección asistida cuando hay ambigüedad
- F2.4 — Captura de foto vinculada automáticamente a la orden de trabajo activa
- F2.5 — Reconocimiento de imagen (detección de estrés/plaga) → nota de texto vinculada
- F2.6 — Modo offline con sincronización diferida
- F2.7 — (N03) Cruce de imágenes satelitales vs. órdenes activas
- F2.8 — (N03) Alertas de zonas sin cobertura con hipótesis de causa

**Casos de uso:**

- UC2.1 — Registrar una tarea de campo dictando en lenguaje natural
- UC2.2 — Corregir un campo mal interpretado por el sistema
- UC2.3 — Sacar una foto del lote y que quede asociada a la orden del día
- UC2.4 — Recibir una alerta de posible estrés hídrico detectado por satélite sin orden asociada

---

## Vertical 03 — Stock, trazabilidad y compliance

**Features refinadas:**

- F3.1 — Registro de movimiento de stock por voz/texto (lote, cantidad, origen, destino)
- F3.2 — Validación automática de disponibilidad antes de confirmar el movimiento
- F3.3 — Vista consolidada de stock en tiempo real de las 4 ubicaciones
- F3.4 — Bloqueo de emisión de remito/orden de carga si no hay stock verificado
- F3.5 — Detección de discrepancia declarado vs. contado, con hipótesis de causa
- F3.6 — (N03) Generación asistida de factura proforma y documentación de exportación
- F3.7 — (N03) Pre-completado de formularios cruzando trazabilidad del lote con requisitos normativos

**Casos de uso:**

- UC3.1 — Registrar traslado de stock entre dos ubicaciones por voz
- UC3.2 — Consultar stock actual de un lote específico en las 4 ubicaciones
- UC3.3 — Intentar emitir un remito sin stock suficiente y recibir el bloqueo
- UC3.4 — Investigar una discrepancia y ver la hipótesis que propone el sistema
- UC3.5 — Generar documentación de exportación para un lote dictando los datos faltantes

---

## Flows detallados (ejemplos representativos)

### Flow A — UC2.1: Registrar orden de trabajo por voz (N01, Vertical 02)

1. Operario abre la app en el celular desde el lote, toca "Nuevo registro"
2. Dicta: _"Terminé de aplicar fungicida en el lote 8, usé 3 litros, todo bien"_
3. Sistema transcribe (STT) y extrae: `{lote: 8, tarea: "aplicación fungicida", insumo: "fungicida X", cantidad: 3L, fecha: hoy}`
4. Sistema valida el insumo contra el diccionario provisto → insumo reconocido, dosis dentro de rango recomendado
5. Muestra un resumen editable en pantalla para confirmación
6. Operario confirma (o corrige un campo tocándolo)
7. Sistema guarda la orden estructurada, marca timestamp y usuario, encola sincronización si está offline
8. Confirmación visual + opción de "agregar foto"

**Caso alternativo:** si el insumo dictado no está en el diccionario → sistema pide aclaración ("No reconozco 'producto verde', ¿podés elegir de la lista?") en vez de adivinar.

### Flow B — UC1.1: Consulta conversacional sobre histórico (N01, Vertical 01)

1. Analista escribe/dicta: _"¿Cómo rindió la variedad Spunta en la campaña 2021?"_
2. Sistema traduce la pregunta a una consulta estructurada sobre la base histórica (no le pasa la pregunta cruda al LLM para "recordar" datos)
3. Ejecuta la consulta, obtiene el resultado numérico real
4. LLM redacta la respuesta en lenguaje natural usando ese resultado como contexto verificado
5. Responde: _"Spunta rindió X ton/ha en 2021, citando fuente: registro campaña 2021, lote Y"_
6. Si la pregunta es ambigua (ej. no especifica campaña) → el sistema repregunta en vez de asumir

### Flow C — UC3.3: Bloqueo por falta de stock (N02, Vertical 03)

1. Operario de depósito intenta emitir remito para 500kg del lote 42 desde el frigorífico A
2. Sistema consulta la vista consolidada de stock en tiempo real
3. Detecta que el stock verificado en frigorífico A es de 480kg (20kg menos que lo declarado en planilla)
4. Bloquea la emisión y muestra la discrepancia
5. Sistema genera hipótesis: _"Un movimiento del 12/08 posiblemente no se registró en destino"_
6. Operario puede investigar, corregir el registro, o escalar a un supervisor
7. Una vez resuelta la discrepancia, el remito puede emitirse

### Flow D — UC2.4: Alerta por imagen satelital sin orden asociada (N03, Vertical 02)

1. Proceso automático (batch o agente) compara semanalmente imágenes satelitales de los lotes vs. órdenes de trabajo activas
2. Detecta una zona del lote 8 con signos visuales de estrés hídrico
3. Verifica si existe una orden de riego reciente para ese lote → no existe
4. Agente genera alerta: _"Posible estrés hídrico en el lote 8, sin orden de riego reciente"_
5. Notifica al ingeniero responsable del lote
6. Ingeniero revisa desde el campo, confirma o descarta, y si corresponde genera la orden de trabajo correspondiente (reutilizando Flow A)

### Flow E — UC3.5: Generación de documentación de exportación (N03, Vertical 03)

1. Administrativo selecciona el lote a exportar
2. Sistema cruza automáticamente los datos de trazabilidad del lote (origen, movimientos, certificaciones) con los requisitos documentales del organismo de control correspondiente
3. Pre-completa el formulario/factura proforma con los campos que ya conoce
4. Señala los campos faltantes y permite completarlos por dictado
5. Administrativo revisa, corrige si hace falta, y confirma
6. Sistema genera el documento final (PDF) listo para envío
