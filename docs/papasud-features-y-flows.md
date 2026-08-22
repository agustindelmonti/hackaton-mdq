---
tags: [hackathon, papasud, features, flows, especificacion]
date: 2026-08-21
status: spec
---

# Papasud — features, casos de uso y flows

Versión ampliada de [[papasud]], reescrita con todo el contexto de la investigación.

**Fuentes internas:** [[papasud-company-research]] · [[papa-semilla-modelo-de-datos]] · [[seed-potato-domain-reference]] · [[hackathon-technical-feasibility]] · [[voice-first-mobile-ux-design]] · [[agtech-landscape-and-positioning]] · [[hackathon-winning-strategy]] · [[hackathon-demo-strategy]] · [[hackathon-recomendacion-final]] · [[polfin-reusable-assets]] · [[polpilot-reusable-assets]]

> **Cómo leer este documento.** `[F]` = respaldado por fuente pública o normativa · `[C]` = propuesta de diseño propia · `[?]` = dato en disputa entre fuentes, verificar con Papasud antes de mostrarlo en pantalla.
>
> Las 9 sub-verticales del brief están todas cubiertas, pero **no todas valen lo mismo**. La priorización está al final; la recomendación operativa vive en [[hackathon-recomendacion-final]].

---

## 0. Lo que cambió respecto de la primera versión

La primera versión de este documento trataba el problema como el brief lo presenta: tres verticales sueltas, lotes como filas de stock, órdenes de trabajo como formularios. La investigación desarmó cuatro supuestos:

1. **Los "4 lugares físicos" no son 4 depósitos.** Son el final de una cadena de custodia de **3 a 7 años** que cruza **1.800 km y dos provincias**: laboratorio in vitro → **El Calafate, Santa Cruz** (junto al glaciar Perito Moreno, cuya ruptura periódica usan como desinfectante natural del suelo) → **Tres Arroyos / Gonzales Chaves / San Cayetano** (Zona Diferenciada bonaerense) → **General Pueyrredón** (acondicionamiento y despacho). `[F]`
2. **Un lote no es una fila: es un nodo en un árbol genealógico fiscalizado.** Cada lote desciende de otro, y su categoría está acotada por la del padre. Eso es integridad referencial, y es lo que una planilla compartida no puede hacer. `[F]`
3. **La diferencia entre lo declarado y lo contado no siempre es un error.** La papa pierde peso en el frigorífico: es **merma legítima**. Y no es lineal — **55-70 % de la pérdida de la temporada ocurre en los primeros 30 días**. `[F]`
4. **La documentación de exportación no es "llenar una proforma".** Es que el pliego fitosanitario **depende del destino**, Papasud exporta a ~9 países con protocolos distintos, y la evidencia que sustenta el documento se generó 3 a 7 años antes, en otra provincia. `[F]`

Todo el resto del documento sale de ahí.

---

## 1. Actores del sistema

| Actor | Contexto físico real | Restricciones que impone al diseño |
|---|---|---|
| **Ingeniero agrónomo de campo** | En el lote, a la intemperie, guantes, sol directo, posiblemente sobre un tractor. A veces en Santa Cruz. | Sin señal. Pantalla ilegible al sol. Una mano ocupada. **Voz > teclado.** Targets ≥44 px. |
| **Operario de depósito / frigorífico** | Dentro de una cámara a ~4 °C, con bolsones de ~700 kg, autoelevador. | Guantes gruesos (touch impreciso), ruido, sin señal dentro de la cámara. Registro *después* del movimiento físico, no durante. |
| **Encargado de acondicionamiento y empaque** | General Pueyrredón. Rotula, pesa, arma pallets. | Genera el dato que después sustenta la exportación. Es el eslabón donde el rótulo se vuelve verdad legal. |
| **Administrativo de comercio exterior** | Escritorio, múltiples portales oficiales (TAD, CERT-POV, ePhyto). | Trabaja con 5+ sistemas que no se hablan. Necesita *pre-completado*, no un sistema más. |
| **Analista / gerencia (Leandro Pérsico y equipo)** | Escritorio. Decide reasignación de superficie **ahora mismo**, tras un 2025 de 11 meses de pérdidas y −12 % de superficie sembrada nacional. | Necesita respuestas con cita, no un chatbot simpático. Un número inventado destruye la confianza. |
| **Inspector de INASE** *(actor externo)* | Visita el lote 2 veces por campaña. | No es usuario del sistema, pero **define el esquema de datos**: lo que él pide es lo que hay que registrar. |
| **Sistema / agente IA** | — | **Nunca calcula. Nunca inventa. Extrae lenguaje y narra resultados que otro computó.** |

> **Asimetría que define todo:** ~20 empleados permanentes (~80 en pico) sosteniendo el **82,2 %** de las exportaciones argentinas de papa semilla de la década 2013-2023, **sin sitio web**. Complejidad de multinacional, estructura administrativa de PyME familiar. `[F]`

---

## 2. Núcleo de dominio compartido

Las tres verticales comparten estas entidades. Construir esto primero mantiene abiertas las tres opciones hasta ver los datos reales de Papasud.

### 2.1 Categorías y linaje

**Clase fiscalizada**, dividida en dos categorías: `[?]`

- **Básica:** Preinicial 0 · Preinicial I · Preinicial II · Inicial I · Inicial II · Inicial III · Fundación
- **Certificada:** Registrada · Certificada A · Certificada B

**Regla de linaje:** todo lote desciende de una subcategoría **igual o superior** a la propia. `[F]`

> ⚠️ **`[?]`** Las fuentes se contradicen sobre la norma que rige (**Res. INASE 245/98** vs. **171/2000**) y sobre la cola de la escalera (una fuente incluye "Prefundación" y termina en "Certificada" sola). **Implementar la regla, no citar un número de artículo en pantalla** hasta confirmarlo con Papasud en los primeros 20 minutos.
>
> **Vocabulario:** no decir "prebásica / básica / registrada / certificada" — es el escalón genérico de cereales y delata. **Papasud vende G3** (tercera generación), su diferencial comercial declarado. Etiquetar `Categoría: Certificada – Registrada · Generación: G3`. `[F]`

### 2.2 Identidad de un lote

Clave natural, tomada del rótulo oficial: `[F]`

`(semillero + N° RNCyFS, variedad, categoría/subcategoría, zona de producción, año de cosecha, N° de lote)`

El **rótulo oficial** lleva además: clase fiscalizada, **"MATERIAL TRATADO CON VENENO" en letras rojas** si corresponde, grado con sello de tinta, y tope de **50 kg** (producido a campo) / **20 kg** (Preiniciales). Envases abiertos >50 kg deben mostrar **"PAPA SEMILLA FISCALIZADA EN PROCESO"**, nombre del campo donde se produjo, lote de producción, variedad, peso y zona. `[F]`

→ *Esa última línea es la especificación de trazabilidad, regalada por la normativa.*

### 2.3 Unidades

- **Bolsón ≈ 700 kg** — la densidad de la papa lo topea muy por debajo de la capacidad nominal del envase. **No 1.000 ni 1.250.** `[F]`
- Envase rotulado: ≤50 kg campo / ≤20 kg preinicial. `[F]`

### 2.4 Merma

Curva **no lineal** de pérdida de peso en almacenamiento: **55-70 % de la merma de la temporada en los primeros 30 días**. `[F]`
La normativa **admite cantidad indeterminable** para productos primarios → `kg estimado, pendiente de pesaje` es un **estado legítimo**, no un error. `[F]`

### 2.5 Documentos de tránsito

- **DTV-e** (Documento de Tránsito Vegetal electrónico, SENASA) `[F]`
- **COT de ARBA** a partir de **4.500 kg** — alcanza a prácticamente todo camión de Papasud `[F]`
- ❌ **NO Carta de Porte / CTG** (instrumento de granos) · ❌ **NO DJVE** (granos y oleaginosas). Nombrarlos delata. `[F]`

### 2.6 Estados epistémicos (el color como información)

La decisión de diseño de mayor apalancamiento. `[C]`

| Estado | Color | Significado |
|---|---|---|
| `inferido` | azul acero | la máquina lo escuchó o lo dedujo |
| `confirmado` | verde brote | una persona lo validó |
| `dudoso` | ámbar ocre | la máquina duda y pregunta |
| `error` | rojo ladrillo | discrepancia real, sincronización fallida |

Narrable en una frase: *"el azul es lo que la IA cree, el verde es lo que una persona confirmó, el ámbar es lo que está preguntando"*.

---

## 3. Vertical 01 — El cerebro de Papasud

**Problema real:** 20+ años de datos productivos y comerciales en un Excel. Difícil de consultar, sin protección contra error humano, sin proyección. El conocimiento depende de que alguien sepa dónde buscar. `[F]`

**Contexto que le da urgencia:** vienen de **11 meses consecutivos de pérdidas en 2025** y **−12 % de superficie sembrada** nacional en 2025/26. Están decidiendo reasignación de superficie **ahora**, con 20 años de evidencia que no pueden consultar. `[F]`

### Features

| ID | Feature | Nivel |
|---|---|---|
| **F1.1** | Consulta en lenguaje natural (texto y voz es-AR) sobre el histórico | N01 |
| **F1.2** | Traducción pregunta → **tools tipadas fijas** sobre los datos reales (no SQL libre) | N01 |
| **F1.3** | Respuesta con **cita de fuente**: qué campaña, qué lote, qué fila lo sustenta | N01 |
| **F1.4** | Repregunta ante ambigüedad, en vez de asumir (¿qué campaña? ¿qué variedad?) | N01 |
| **F1.5** | Números pre-formateados que el modelo copia **verbatim**, nunca recalcula | N01 |
| **F1.6** | Dashboard de indicadores (rendimiento, superficie, producción) por año / variedad / zona | N02 |
| **F1.7** | Resumen narrativo automático de variaciones año a año, con magnitud | N02 |
| **F1.8** | **Benchmark contra la zona**: comparar Papasud vs. promedio de partido con datos abiertos de MAGyP (Estimaciones Agrícolas, Balcarce consultable) | N02 `[C]` |
| **F1.9** | Detección de outliers de campaña (qué año se salió de la curva y por qué) | N02 |
| **F1.10** | Modelo predictivo de aptitud de variedad por lote + clima | N03 |
| **F1.11** | Explicación de la predicción en términos de agrónomo (feature importance → texto) | N03 |
| **F1.12** | Declaración honesta de incertidumbre cuando los datos de entrenamiento no alcanzan | N03 `[C]` |

### Casos de uso

- **UC1.1** — Consultar rendimiento histórico de una variedad en una campaña específica
- **UC1.2** — Comparar dos campañas o dos variedades entre sí
- **UC1.3** — Leer el resumen automático del dashboard y entender qué cambió
- **UC1.4** — Preguntar *"¿cómo rindió esta variedad en las campañas de precios bajos?"* — la pregunta que tienen sobre la mesa hoy
- **UC1.5** — Comparar el rendimiento propio contra el promedio del partido
- **UC1.6** — Pedir proyección de aptitud de una variedad para un lote nuevo
- **UC1.7** — Detectar que una pregunta **no se puede responder con los datos disponibles** y que el sistema lo diga

### Decisión técnica clave

**Tools tipadas fijas, no text-to-SQL libre.** `[C]` El dataset es chico (20 años de campañas = miles de filas, no millones). Un set acotado de tools —`rendimiento_por(variedad, campaña, zona)`, `serie_anual(indicador)`, `comparar(a, b)`— con los números devueltos ya formateados es más rápido de construir, imposible de romper con una inyección, y **cero riesgo de que el modelo invente un número**. El patrón está implementado y auditado en [[polpilot-reusable-assets]] y [[polfin-reusable-assets]] (tools presentacionales que devuelven `{ok:true}` con los datos en los args).

---

## 4. Vertical 02 — Campo inteligente

**Problema real:** las órdenes de trabajo se arman a mano, muchas veces después de un día entero en el campo. Proceso lento, propenso a errores, sin conexión con ningún sistema central. `[F]`

**Contexto:** es la vertical **menos atacada** del evento (intimida: visión, satélite, mobile). Es el hueco estratégico. `[F]`

### Features

| ID | Feature | Nivel |
|---|---|---|
| **F2.1** | Captura de orden de trabajo por voz o texto libre, desde el celular en el lote | N01 |
| **F2.2** | Extracción de entidades (lote, tarea, insumo, dosis, fecha) vía **tool forzada con schema estricto** | N01 |
| **F2.3** | **Resolución determinística de identificadores**: fuzzy-match contra el diccionario real de insumos, candidatos ranqueados — el LLM nunca elige el insumo solo | N01 |
| **F2.4** | Nunca inventar una cantidad no dicha → `null` + `confianza: dudosa` | N01 |
| **F2.5** | Validación de dosis contra el rango recomendado del diccionario | N01 |
| **F2.6** | Chips de pregunta aclaratoria ante ambigüedad, resolubles con un toque | N01 |
| **F2.7** | **Modo offline con cola de sincronización** y badges de estado | N01 `[C]` |
| **F2.8** | Selector manual de lote como camino primario, con GPS/EXIF como *sugerencia* | N02 `[C]` |
| **F2.9** | Foto vinculada a la orden de trabajo activa | N02 |
| **F2.10** | Clasificación visual **binaria sano/estresado** como titular | N02 |
| **F2.11** | Patógeno como **hipótesis ranqueada**, nunca como diagnóstico | N02 `[C]` |
| **F2.12** | Nota de texto generada desde la imagen, vinculada al registro | N02 |
| **F2.13** | NDVI por polígono de lote cruzado con órdenes activas | N03 |
| **F2.14** | Alerta de zona sin cobertura, con acción concreta sugerida | N03 |

### Casos de uso

- **UC2.1** — Registrar una tarea de campo dictando en lenguaje natural
- **UC2.2** — Corregir un campo mal interpretado tocándolo
- **UC2.3** — Dictar sin señal y ver la sincronización completarse al recuperar conexión
- **UC2.4** — Sacar una foto del lote y que quede asociada a la orden del día
- **UC2.5** — Recibir la nota "signos de estrés visible" y confirmarla o descartarla
- **UC2.6** — Recibir alerta de posible estrés hídrico detectado por satélite sin orden asociada

### Dos correcciones importantes

**EXIF no es confiable.** `[F]` Android 10+ redacta la ubicación, iOS la omite en captura vía web, y WhatsApp la borra entera. El auto-vinculado por GPS de la foto **no puede ser el camino primario** — construir el selector manual de lote primero y el automático como mejora. *(Esto corrige el encuadre inicial de la investigación, que proponía EXIF como la vía determinística.)*

**La visión no es confiable al nivel de patógeno.** `[F]` El mejor VLM alcanza ~**62 %** en conjunto cerrado sobre datasets agronómicos, y los modelos tipo PlantVillage caen de **97,7 % a 67,2 %** al pasar de laboratorio a campo. Titular el binario **sano/estresado** —que sí funciona— y presentar el patógeno como hipótesis ranqueada para que un agrónomo la confirme. Prometer detección de plagas es prometer lo que la tecnología no da.

**El satélite tiene un problema de calendario.** `[F]` **En agosto los lotes de Balcarce están en barbecho** — un demo de "NDVI actual" muestra una línea plana. Consultar la campaña 2025/26 ya cerrada, no la fecha de hoy.

---

## 5. Vertical 03 — Stock, trazabilidad y compliance

**Problema real:** ~150 lotes en 4 ubicaciones (3 frigoríficos + 1 galpón), en una planilla que varias personas editan a la vez. Nadie tiene una visión única confiable, y las diferencias entre planilla y realidad **se descubren recién al entregarle el pedido a un cliente**. `[F]`

Es la redacción más visceral del brief entero: eso es plata perdida y un cliente enojado.

### Features

| ID | Feature | Nivel |
|---|---|---|
| **F3.1** | Movimiento de stock por voz o texto (lote, cantidad, origen, destino) | N01 |
| **F3.2** | Validación de disponibilidad **antes** de confirmar | N01 |
| **F3.3** | **Stock como vista derivada de un libro append-only**, nunca celda editable | N01 `[C]` |
| **F3.4** | Confirmación humana obligatoria — nada persiste desde una nota de voz sin aprobación | N01 |
| **F3.5** | Estado `kg estimado, pendiente de pesaje` en ámbar (admitido por normativa) | N01 `[C]` |
| **F3.6** | **Validación de linaje**: rechazar un lote cuyo padre es de categoría inferior | N01 `[C]` |
| **F3.7** | Vista consolidada en tiempo real de las 4 ubicaciones, con drill-down a movimientos | N02 |
| **F3.8** | **Bloqueo** de emisión de remito / orden de carga sin stock verificado | N02 |
| **F3.9** | **Discrepancia neta de merma**: `declarado − merma esperada vs. contado`, clasificando *dentro de merma* / *excede merma* | N02 `[C]` |
| **F3.10** | Hipótesis en lenguaje llano, redactada por el LLM **sólo** sobre la lista acotada de movimientos candidatos | N02 |
| **F3.11** | Genealogía del lote navegable (de dónde viene, por dónde pasó, cuántos años) | N02 `[C]` |
| **F3.12** | Pre-completado de documentación de exportación cruzando trazabilidad + requisitos del destino | N03 |
| **F3.13** | **Detección de inconsistencias documentales** (ver abajo) | N03 `[C]` |
| **F3.14** | Tabla de equivalencia de categorías por país destino | N03 `[C]` |
| **F3.15** | Marca `DEMO — SIN VALOR LEGAL / NO OFICIAL` en todo PDF generado | N03 `[C]` |

### Casos de uso

- **UC3.1** — Registrar un traslado entre dos ubicaciones por voz, con guantes, dentro de la cámara
- **UC3.2** — Consultar el stock actual de un lote en las 4 ubicaciones
- **UC3.3** — Intentar emitir un remito sin stock suficiente y recibir el bloqueo
- **UC3.4** — Investigar una discrepancia y **entender si es merma o error**
- **UC3.5** — Ver la genealogía de un lote que está por exportarse
- **UC3.6** — Generar documentación de exportación dictando los datos faltantes
- **UC3.7** — Que el sistema **encuentre el error documental antes que el organismo**
- **UC3.8** — Registrar el intento de un lote `inicial_I` con padre de categoría inferior y recibir el rechazo

### El set documental de exportación

**INASE** (Res. 56/18, vía plataforma **TAD**): `[F]`
formulario de solicitud · nota de compromiso de no difusión (material fuera del Catálogo Nacional de Cultivares) · **factura y/o packing list** · comprobante **VEP** · inscripción **RNCyFS** · específico de papa: **Res. SAGyP 715/94**

**SENASA** (vía **CERT-POV**): `[F]`
inscripción en el Registro de Operadores de Comercio Exterior (AFIP) · solicitud de **Certificado Fitosanitario** · **AFIDI / permiso de importación del país destino** · copia del **permiso de embarque** · **copia del Certificado INASE para material de propagación** · documentación oficial de los requisitos de la **ONPF importadora** · comprobante de aranceles

**Comercial:** `[F]`
factura comercial / proforma · packing list · **certificado de origen MERCOSUR** (lo emite una Cámara de Comercio Exterior) · conocimiento de embarque / **CRT** para flete terrestre a Brasil y Paraguay

**Canal:** **ePhyto** hacia Brasil desde el 04/08/2023. Equivalencias: **MERCOSUR/GMC Res. 29/22** (lote máximo a muestrear 200 t, tamaño de muestra para virus, métodos para nematodos, reconocimiento del análisis visual). `[F]`

### F3.13 — Las inconsistencias que hay que detectar

Generar el PDF es lo menos interesante. **Lo que lo vuelve un copiloto es encontrar el error antes que el organismo:** `[F]`

- **NCM `0701.10.00` vs `0701.90.00`** — semilla contra consumo. El error más caro y el más fácil de cometer.
- Certificado de origen emitido a **más de 60 días** de la factura
- Peso neto que **no cuadra** entre la Factura E y el packing list
- Falta la **declaración adicional de la plaga** que exige *ese* destino
- **Rótulo que excede el tope de kg** de su categoría (50 / 20)
- **Certificado INASE vencido**

### Fricciones de mercado que dan contexto al valor

- **Brasil y Uruguay exigen semilla lavada** — sube costo y riesgo sanitario; Canadá y la UE no lo piden. Desventaja competitiva argentina. `[F]`
- **Las tolerancias de categoría de Brasil son más laxas** que las argentinas y **no hay criterios unificados**: una *Certificada* argentina puede reofrecerse allá bajo otro nombre. Marcado en la investigación como **problema de negocio genuinamente sin resolver** → F3.14. `[F]`
- Los análisis del **AFIDI se repiten en destino**, reteniendo la semilla del comprador **20-30 días** antes de poder plantarla. `[F]`
- **PepsiCo quiere el 100 % de su semilla producida localmente en Brasil para 2028.** El canal que le abrió Vietnam y Brasil a Papasud tiene vencimiento anunciado. `[F]`
- **Egipto pidió 5.000 t** (un solo cliente), Indonesia y Malasia también — **SENASA no abrió esos mercados**. `[F]`
- **Drakar S.R.L. saltó de 87 t a 1.113 t en 2023 = 46,46 % de ese año.** La posición de Papasud se erosiona. `[F]`

→ **La capacidad de abrir un mercado nuevo está limitada por la capacidad administrativa, no agronómica.**

---

## 6. Flows detallados

### Flow A — UC3.1: Movimiento de stock por voz *(camino crítico de la demo)*

1. Operario, dentro del frigorífico, con guantes. Abre la app y mantiene presionado el botón de voz. **Barras de amplitud reales** confirman que lo está escuchando.
2. Dicta: *"pasé 20 bolsones del lote 42 del frigorífico 2 al galpón"*
3. **Web Speech API (es-AR)** transcribe en el navegador — sin API key, sin backend, sin red hacia un STT externo. La transcripción aparece en **azul** (la máquina escuchó).
4. **Tool forzada** con schema estricto extrae: `{lote: "42", cantidad: 20, unidad: "bolson", origen: "frigorifico_2", destino: "galpon"}`
5. **Capa determinística** resuelve identificadores: fuzzy-match de "lote 42" contra los ~150 lotes reales, y de "frigorífico 2" / "galpón" contra las 4 ubicaciones. Si hay ambigüedad → candidatos ranqueados, **nunca el LLM eligiendo solo**.
6. Conversión de unidad: 20 bolsones × ~700 kg = **14.000 kg**. Mostrado explícitamente, no escondido.
7. **Validación de disponibilidad** (F3.2): ¿hay 14.000 kg del lote 42 en el frigorífico 2, netos de merma esperada?
8. Tarjeta de confirmación con los campos como chips: **azules** los inferidos, **ámbar** los dudosos. Cada chip es editable con un toque.
9. Operario confirma → los chips pasan a **verde**. Se persiste el movimiento con `usuario`, `timestamp`, `fuente: 'voz'` y **la transcripción original guardada para auditoría**.
10. Si no hay señal: entra en la cola con badge **ámbar** de pendiente; al recuperar conexión los badges **caen en cascada a verde**.

**Alternativos:**
- Insumo/lote no reconocido → *"No reconozco 'el de la punta', ¿cuál de estos tres?"* — pregunta, no adivina.
- Cantidad no dicha → `null` + `confianza: dudosa`, chip en ámbar exigiendo el dato. **Jamás asume una cantidad.**
- Peso no determinable → estado `kg estimado, pendiente de pesaje` en ámbar. Legítimo por normativa, no un error.

---

### Flow B — UC3.4: Discrepancia, distinguiendo merma de error *(el momento "razona")*

1. Se carga un conteo físico del lote 42 en el frigorífico 2: **13.100 kg**.
2. El sistema computa el saldo declarado desde el libro append-only: **14.000 kg**.
3. **No resta y alarma.** Primero consulta la curva de merma: el lote ingresó hace **22 días** → tramo de mayor pérdida, donde ocurre el 55-70 % de la merma de la temporada. Merma esperada ≈ **4,5 %** → **kg esperado ≈ 13.370**.
4. Delta real contra lo esperado: **−270 kg**, por encima de la tolerancia → **`excede_merma`**.
5. **Sólo ahora** el LLM entra en juego, y **sólo sobre la lista acotada** de movimientos candidatos: los que tienen salida registrada sin entrada espejo en destino, los conteos sin ajuste, los cargados con `confianza: dudosa`.
6. Hipótesis en castellano llano: *"un movimiento del 12/08 posiblemente no se registró en destino — salieron 400 kg del frigorífico 2 y no hay entrada correspondiente en el galpón"*.
7. La tarjeta ofrece la acción: **Ver en Galpón 2** → aterriza en la pantalla que lo prueba.
8. El operario corrige, o escala a un supervisor.

**El contraste que hace el punto:** si el conteo hubiera dado 13.400 kg, el sistema **no dice nada** — está dentro de la merma esperada. Mostrar los dos casos seguidos es lo que demuestra que el sistema entiende el negocio.

> Frase para la demo: **"no te aviso cuando la papa pierde peso; te aviso cuando pierde más peso del que debería"**.

---

### Flow C — UC3.3: Bloqueo de remito por stock no verificado

1. Se intenta emitir un remito por 500 kg del lote 42 desde el frigorífico A.
2. El sistema consulta la vista derivada, neta de merma esperada.
3. Detecta que el stock verificado es de **480 kg** y **bloquea la emisión**.
4. Muestra **los movimientos que componen ese saldo** — no un mensaje de error genérico, la evidencia.
5. Ofrece hipótesis (Flow B) y ruta de resolución.
6. Resuelta la discrepancia, el remito se habilita.
7. Al emitirse, arrastra el documento de tránsito correcto: **DTV-e**, más **COT de ARBA** si el envío supera 4.500 kg. *(No Carta de Porte.)*

---

### Flow D — UC3.8: Rechazo por linaje inválido *(el diferencial)*

1. Se registra un lote nuevo declarando subcategoría **Inicial I** y como padre un lote de categoría inferior.
2. El sistema compara los índices en la escalera y detecta que **la semilla no puede ascender de categoría**.
3. **Rechaza**, explicando la regla de linaje INASE en la propia interfaz: un lote sólo puede provenir de una subcategoría igual o superior.
4. Ofrece las subcategorías válidas dado ese padre.

> ⚠️ Mostrar **la regla**, no un número de artículo, hasta verificar la norma con Papasud. `[?]`

Ningún otro equipo va a validar la genealogía fiscalizada de un lote. Es el detalle que separa "hicimos un CRUD con voz" de "entendimos que este negocio está fiscalizado".

---

### Flow E — UC2.1: Orden de trabajo de campo por voz *(la misma cañería, otro schema)*

1. El ingeniero, en el lote, dicta: *"terminé de aplicar fungicida en el lote 8, usé 3 litros, todo bien"*
2. Misma tubería que el Flow A: Web Speech es-AR → tool forzada → resolución determinística → confirmación humana. **~90 % del código compartido.**
3. Extrae `{lote: 8, tarea: "aplicación fungicida", insumo: "fungicida X", cantidad: 3, unidad: "L", fecha: hoy}`
4. Valida el insumo contra el diccionario provisto y **la dosis contra el rango recomendado**. Si la dosis está fuera de rango → ámbar, preguntando.
5. Resumen editable, confirmación, persistencia con cola offline.
6. Ofrece **"agregar foto"** → Flow F.

**Alternativo:** insumo no reconocido → *"No reconozco 'producto verde', ¿podés elegir de la lista?"*

> **En la demo esto es un aside de 15 segundos, no un segundo flujo.** En cinco minutos no entran dos historias bien contadas. Se muestra funcionando para cobrar el crédito de cubrir dos verticales, sin diluir la narrativa.

---

### Flow F — UC2.4/2.5: Foto de lote con lectura visual honesta

1. El ingeniero saca una foto desde la orden de trabajo activa.
2. **El lote se vincula por el selector manual**, pre-seleccionado con la orden activa. GPS/EXIF, **si existe**, aparece como *sugerencia* a confirmar — nunca como fuente de verdad. `[F]`
3. Un VLM clasifica **sano / estresado** — el binario que sí funciona en campo.
4. Si detecta estrés, ofrece **hipótesis ranqueadas** de causa ("posible estrés hídrico · posible virosis · posible deficiencia"), explícitamente etiquetadas como hipótesis a confirmar por el agrónomo.
5. Genera la nota de texto vinculada al registro, en **azul** (inferido) hasta que el ingeniero la confirme y pase a **verde**.
6. La foto queda asociada al lote y a la orden, con timestamp y usuario.

---

### Flow G — UC2.6: Anomalía satelital sin orden asociada

1. Proceso batch compara NDVI por polígono de lote contra las órdenes de trabajo activas.
2. Detecta una zona del lote 8 con caída de NDVI sostenida.
3. Verifica si existe una orden de riego reciente para ese lote → no existe.
4. Genera la alerta: *"posible estrés hídrico en el lote 8, sin orden de riego reciente"*.
5. Notifica al ingeniero responsable.
6. El ingeniero confirma o descarta desde el campo, y si corresponde genera la orden — **reutilizando el Flow E**.

> ⚠️ **Trampa de calendario:** en agosto los lotes están en barbecho y el NDVI actual da una línea plana. **Consultar la campaña 2025/26 cerrada**, no la fecha de hoy. `[F]`

---

### Flow H — UC1.1/1.4: Consulta conversacional con cita

1. El analista dicta o escribe: *"¿cómo rindió la Spunta en las campañas de precios bajos?"*
2. El sistema **no le pasa la pregunta cruda al LLM para que recuerde números.** Selecciona entre un set de **tools tipadas fijas** y las ejecuta contra los datos reales.
3. Obtiene el resultado numérico, **ya formateado como string**.
4. El LLM redacta la respuesta **copiando ese string verbatim** — tiene prohibido reformatear, redondear o recalcular.
5. Responde citando la fuente: campaña, lote, fila. El disclosure colapsable de la tool call **es** la UI de cita de fuente. `[F]`
6. Si la pregunta es ambigua (no especifica campaña, variedad o zona) → **repregunta** en lugar de asumir.
7. Si la pregunta no se puede responder con los datos disponibles → **lo dice**, en vez de aproximar.

**Extensión F1.8:** enriquecer con **MAGyP Estimaciones Agrícolas** (CSV abierto, rendimientos de papa a nivel partido, Balcarce directamente consultable) para contestar *"¿rendimos mejor o peor que la zona?"* — una pregunta que su Excel **no puede** responder porque no tiene el dato externo. `[F]`

---

### Flow I — UC3.6/3.7: Documentación de exportación

1. El administrativo selecciona el lote a exportar y el país destino.
2. El sistema reconstruye la **cadena de custodia** del lote: linaje completo, ubicaciones sucesivas, campañas, análisis de laboratorio, certificados.
3. Cruza esa trazabilidad con el **pliego de requisitos de la ONPF de ese destino** y pre-completa lo que ya sabe.
4. Señala los campos faltantes; se completan por dictado o selección rápida.
5. **Corre las validaciones de F3.13** y muestra lo que encontró: NCM incorrecto, certificado de origen fuera de los 60 días, peso que no cuadra entre Factura E y packing list, declaración adicional de plaga faltante, rótulo por encima del tope de kg, certificado INASE vencido.
6. Si el destino tiene tolerancias distintas (Brasil), muestra la **equivalencia de categoría** correspondiente (F3.14).
7. Genera el documento, **marcado `DEMO — SIN VALOR LEGAL / NO OFICIAL`**.

> Las tolerancias sanitarias numéricas viven en anexos **no publicados online**. Presentarlas como filas marcadas DEMO y **no inventarlas con tono de autoridad**. `[F]`

---

## 7. Priorización

Criterios, en orden de peso, derivados de [[hackathon-demo-strategy]] y [[hackathon-winning-strategy]]:

1. ¿Se puede demostrar el dolor y la solución en 5 min sin explicar nada técnico?
2. ¿Funciona sin depender de datos que recién se ven a las 10 am?
3. ¿Cuánto riesgo de falla en vivo tiene?
4. ¿Cuán probable es que otros 20 equipos hagan lo mismo?
5. ¿Le habla al dolor que Papasud describió con más emoción?

| Prioridad | Qué | Por qué |
|---|---|---|
| **1** | **F3.1-F3.10 + Flows A, B, C, D** | El núcleo recomendado. Voz → movimiento → vista única → bloqueo → discrepancia neta de merma → linaje. Independiente de la calidad del Excel. Tres validaciones demostrables. Vertical menos disputada en relación a su valor. |
| **2** | **F2.1-F2.7 + Flow E** | ~90 % del código compartido con la prioridad 1. Media hora de trabajo marginal, cubre una segunda vertical. **Aside de 15 s, no segundo flujo.** |
| **3** | F3.11 (genealogía navegable) | Hace visible el insight de la cadena de 3-7 años. Alto valor narrativo, costo bajo si el modelo ya tiene `lote_padre_id`. |
| **4** | F3.12-F3.15 + Flow I | Muy valioso para Papasud (es su cuello de botella para abrir mercados), pero un PDF es poco vistoso y consume mucho tiempo. **Una pantalla de cierre, no un módulo.** |
| **5** | F1.1-F1.5 + Flow H | Excelente feature, terreno saturado (50-70 % de los equipos). Sólo si se cuenta con datos limpios y se lo contra-posiciona: insight proactivo primero, no una caja de chat. |
| **6** | F1.6-F1.9 | El dashboard sin el chat es menos demo-able de lo que parece. F1.8 (benchmark de zona) es el único que sorprende de verdad. |
| **7** | F2.8-F2.12 + Flow F | Tres subsistemas desde cero (upload, storage, visión) sin nada reutilizable, y la visión no es confiable a nivel patógeno. |
| **8** | F1.10-F1.12 | Necesita datos de entrenamiento que recién se ven ese día y que probablemente no alcancen para un modelo honesto. |
| **9** | F2.13-F2.14 + Flow G | Máximo riesgo de falla en vivo: API externa, wifi del venue, y los lotes en barbecho en agosto. |

---

## 8. Lo que hay que verificar con Papasud en los primeros 20 minutos

- **La escalera exacta de categorías** y qué norma la rige `[?]` — antes de mostrar cualquier cita en pantalla
- Confirmar que venden **G3** y cómo lo etiquetan internamente
- Qué variedades trabajan realmente (la investigación **no** pudo confirmarlo; se infiere Innovator/Atlantic por el vínculo con PepsiCo, pero es inferencia)
- Cuánto es un bolsón **para ellos** (la investigación dice ~700 kg, pero su operación manda)
- Si tienen una curva de merma propia, o al menos un porcentaje que usen de regla
- Cómo nombran las 4 ubicaciones en el día a día
- Las ~200 ha y 7.500 t del brief **no pudieron verificarse públicamente** — usarlas como dato que ellos dieron, no como dato de mercado
