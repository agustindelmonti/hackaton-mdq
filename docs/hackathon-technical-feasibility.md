---
tags: [reference, hackathon, technical, ai-tools]
date: 2026-08-21
status: researched
---

# Viabilidad técnica — 9 sub-desafíos Papasud (hackathon 3 hs)

Companion docs: [[cursor-hackathon-mar-del-plata-2026]] (evento, sponsors, créditos) · [[papasud]] (verticales, features, flows) · [[polpilot-reusable-assets]] (código reusable ya auditado)

**Premisa de todo el documento:** no son 6 horas de build, son **~3 horas reales** (10:00–16:00 menos kickoff, entrega de datos de Papasud, almuerzo, y 30 min de preparación de demo). El deliverable no es un producto, es **una demo de 5 minutos que un jurado no-técnico entienda en la sala**. Todo lo que sigue está ordenado por *tiempo hasta que se pueda mostrar en pantalla*, no por elegancia.

---

## 0. Los 6 hallazgos que cambian el plan

Antes de los desafíos, lo que la investigación de hoy cambió respecto de lo que uno asumiría:

1. **Netlify AI Gateway inyecta `ANTHROPIC_API_KEY` solo.** En planes con créditos (los 3.000 del sponsor), toda Netlify Function recibe `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` + sus `BASE_URL` ya configurados. **No hace falta cuenta de Anthropic ni tarjeta.** ⚠️ Requiere **un deploy a producción para activarse** → deployar en el minuto 10, no en el 150.
2. **Wispr Flow NO tiene API usable.** Existe una "Voice Interface API" pero es *exclusive access*, aprobada por su equipo comercial vía enterprise@wisprflow.ai. **Es la herramienta con la que vos dictás en Cursor, no un componente de la app.** No la pongas en la arquitectura.
3. **El Web Speech API ahora tiene sesgo de vocabulario.** La propiedad `phrases` (`SpeechRecognitionPhrase {phrase, boost 0–10}`) permite inyectar "Spunta", "lote", "frigorífico" gratis, sin backend. Esto vuelve al STT del navegador competitivo, no solo "el barato".
4. **En agosto los lotes de Balcarce están en barbecho.** Papa del sudeste es siembra primavera / cosecha verano-otoño. Una demo de NDVI "actual" muestra una línea plana y parece un bug. **Hay que consultar la campaña 2025/26 cerrada (oct-2025 → abr-2026)**, que además elimina el riesgo de nubes porque elegís las escenas limpias.
5. **Existe dato oficial argentino de rendimiento de papa a nivel partido.** Las Estimaciones Agrícolas del MAGyP son CSV abierto, sin key, con columnas por **partido** → *Balcarce es directamente consultable*. Casi ningún equipo va a traer estadística nacional real; es un diferenciador de credibilidad enorme y cuesta 10 minutos.
6. **Las categorías de papa semilla NO son el escalón genérico de cereales.** Res. INASE 245/98 define **Básica** (Preinicial 0/I/II, Inicial I/II/III, Fundación) y **Certificada** (Registrada, Certificada A/B). Decir "prebásica/básica/registrada/certificada" delante de gente de Papasud te delata. Papasud vende **G3 (tercera generación)** y eso es su diferencial comercial declarado.

---

## 1. Shared foundation — construir ESTO primero

**El argumento:** a las 10:00 nadie sabe qué datos va a entregar Papasud (formato, cantidad, anonimización sin definir). Construir el andamio común mantiene abiertas las 9 opciones y no desperdicia ni un minuto si el dataset resulta ser otra cosa. Son ~50 minutos que sirven para 8 de los 9 desafíos.

### 1.1 Orden de ejecución (los primeros 50 minutos)

| # | Bloque | Min | Por qué primero |
|---|---|---|---|
| 1 | `pnpm dlx shadcn@latest init -t vite` | 3 | Vite 8 + React + Tailwind v4 + shadcn en un comando |
| 2 | **`netlify deploy --prod`** | 7 | **Activa el AI Gateway** y te da el origen HTTPS que la cámara y el micrófono exigen |
| 3 | `npm i @netlify/vite-plugin` + `netlify()` | 5 | Emula functions, AI Gateway, DB y Blobs dentro de `npm run dev` |
| 4 | Function `/api/llm` con `new Anthropic()` sin key | 8 | El proxy que evita exponer credenciales; en Netlify no lleva key |
| 5 | Seed determinístico (JSON local, no DB) | 10 | Primer render sin red — mata una clase entera de fallas de demo |
| 6 | Componente `<VozInput/>` | 12 | Web Speech + fallback; lo usan V1-N01, V2-N01, V3-N01, V3-N03 |
| 7 | Shell mobile (`h-dvh`, bottom nav, safe-area) | 5 | Dos de tres verticales son usuarios en campo/depósito |

### 1.2 Los cinco componentes reusables

**(a) `<VozInput/>` — entrada por voz con degradación honesta.** Patrón de tres niveles, lifteado de `voz.py`/`transcripcion.py` en [[polpilot-reusable-assets]]:

```js
// 1. Web Speech API, gratis, sin key, transcribe en el cliente
const r = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
r.lang = 'es-AR';
r.interimResults = true;
r.phrases = [   // sesgo de vocabulario — nuevo en 2026
  {phrase:'Spunta',boost:5}, {phrase:'Innovator',boost:5}, {phrase:'Asterix',boost:4},
  {phrase:'Kennebec',boost:4}, {phrase:'Atlantic',boost:4}, {phrase:'lote',boost:3},
  {phrase:'fungicida',boost:4}, {phrase:'frigorífico',boost:4}, {phrase:'remito',boost:4},
  {phrase:'tonelada por hectárea',boost:3}, {phrase:'Balcarce',boost:3}
];
// 2. Fallback: MediaRecorder → Groq whisper-large-v3-turbo con el glosario en `prompt`
// 3. Sin transcriptor: decirlo (`sin_transcriptor`), NUNCA inventar la transcripción
```

Trigger del fallback: `!('webkitSpeechRecognition' in window) || esIOS`. **iOS es la mina:** nominalmente soportado desde Safari 14.5 pero roto en la práctica (no dispara `onresult` con Siri activo, necesita 2–3 s tras dar permiso) y *todos* los browsers en iOS son WebKit, así que Chrome-iOS hereda el bug. Si un jurado agarra un iPhone, el fallback es lo que te salva. Son ~15 líneas.

**(b) `/api/extraer` — extracción estructurada con tool call forzado.** Un solo endpoint que sirve a V2-N01 (orden de trabajo), V3-N01 (movimiento de stock) y V3-N03 (campos de documento). El patrón, que es *la* disciplina que hay que copiar:

- `tool_choice: {type:"tool", name:"..."}` — forzado, más `strict: true` con `additionalProperties:false`.
- El LLM extrae **lenguaje**; una capa determinística resuelve **identificadores** (fuzzy match contra el diccionario real de insumos/lotes). Nunca dejes que el modelo elija el lote solo: proponé una lista rankeada de candidatos para confirmación humana.
- Nunca adivinar un faltante: `dosis: null` + `confianza:"dudosa"`, no un número inventado.
- Nada persiste sin aprobación humana — mismo riel de inserción que la carga manual.

**(c) Núcleo determinístico + narración LLM.** El anti-alucinación que resuelve la exigencia explícita de Papasud ("sin inventar números"). Todo número sale de código plano; Claude recibe **tools** que llaman a ese núcleo y solo narra. Cada valor viaja con su par `_fmt` preformateado (`rendimiento: 32.4174`, `rendimiento_fmt: "32,4 t/ha"`) y el system prompt ordena copiar `_fmt` **literal**, sin reformatear ni redondear. Más la cita de la fila fuente. Esto es copy-paste desde [[polpilot-reusable-assets]].

**(d) Persistencia.** `@netlify/blobs` (cero provisioning, `getStore("x").set/get`) para casi todo. `netlify database init` (Postgres/Neon, migraciones aplicadas en el deploy) **solo** si el desafío necesita SQL de verdad — V1 y V3-N02 lo justifican, el resto no.

**(e) Red de seguridad de demo.** Datos semilla como fixture local; escrituras optimistas con badge "Sincronizado ✓"; banner "Sin conexión — 3 registros en cola" manejado por `navigator.onLine`. Si se cae el wifi en vivo parecés previsor en vez de roto. Y un **video de 90 s del happy path** en una pestaña abierta.

### 1.3 Munición para el pitch (verificada, con n)

Cinco de los nueve desafíos son en el fondo la misma historia — "la planilla es peligrosa" — y una estadística real en el minuto 1 de la demo compra atención barata. Estas están verificadas contra la fuente primaria:

- **65% de ~370.000 registros de inventario resultaron inexactos**, sobre 37 sucursales de un retailer ([DeHoratius & Raman, *Management Science* 54(4), 2008](https://doi.org/10.1287/mnsc.1070.0789)). **Es la mejor bala para V3** — habla exactamente del dolor declarado de Papasud (la planilla no coincide con la realidad y se descubre tarde).
- **94% de 85 planillas operativas inspeccionadas intensivamente contenían errores** ([Panko, EuSpRIG 2015, arXiv:1602.02601](https://arxiv.org/abs/1602.02601)). Declará el n. ⚠️ **El "88%" que circula atribuido a Panko no está en ninguno de sus papers** — no lo uses.
- **Tasa de error por celda 3,9%** (14 estudios, 967 participantes) — *aproximadamente la misma tasa que las líneas de código de producción*. Ese encuadre funciona muy bien con jurado técnico.
- **Overconfianza:** la estimación mediana de los autores fue 10% de probabilidad de error; **86% efectivamente había cometido uno** ([arXiv:0802.3457](https://arxiv.org/abs/0802.3457)).
- Si querés el ejemplo emocional: **Public Health England perdió 15.841 casos de COVID por el límite de 65.536 filas de un XLS** (~1.500 muertes estimadas). Es el mismo modo de falla que "20 años en un Excel".

❌ **No uses** el "$7,6 billones" ni "1 de cada 5 empresas" de F1F9: el informe ya no está publicado y la fuente está muerta.

### 1.4 Elección de stack por tipo de desafío

No hay un stack ganador único, y forzar uno cuesta tiempo:

- **V1 (datos/ML) → Python + Gradio o Streamlit.** `pip install gradio` + `gr.ChatInterface` + `launch(share=True)` = URL HTTPS pública **en menos de 5 minutos**, corriendo en tu laptop, con la key server-side por construcción. pandas/scikit-learn ya están en proceso; no hay que marshalear datos a JSON para Recharts. Para un desafío de datos con demo de 5 minutos esto es inequívocamente lo correcto.
- **V2 y V3 (campo/depósito, cámara, móvil) → React + Netlify.** Streamlit no es creíble como app de campo y necesitás `capture="environment"`.
- ⚠️ **Hugging Face Spaces ya no sirve como hosting gratis instantáneo:** Gradio y Docker Spaces requieren plan pago (PRO en cuentas personales); las cuentas gratis tienen 2 Gradio Spaces en ZeroGPU y Streamlit desapareció como SDK. Usá `share=True` local o Streamlit Community Cloud.

---

## 2. Vertical 01 — El cerebro de Papasud

### V1-N01 · Copiloto conversacional (texto + voz) sobre 20 años de histórico

**Stack recomendado:** Excel → pandas → **SQLite/DuckDB en memoria** + Claude con **tools tipadas** (no text-to-SQL crudo) + Gradio.

**Por qué es el más rápido:** 20 años de historia de ~200 ha son *miles* de filas, no millones. Esto cambia todo: no hace falta RAG (nada que recuperar, el dataset entero entra en contexto), y no hace falta text-to-SQL genérico (que es donde se pierde precisión y donde el modelo inventa columnas que no existen). Lo más rápido *y* lo más preciso es lo mismo: **4-6 tools determinísticas con firma fija** (`rendimiento_por_variedad(variedad, campaña)`, `comparar_campañas(a, b)`, `serie_historica(indicador, desde, hasta)`, `buscar_registros(filtros)`) que ejecutan pandas o SQL parametrizado y devuelven números + `_fmt` + `fuente`.

Text-to-SQL libre es la trampa: es más impresionante en el papel y bastante peor en vivo. Con tools fijas el espacio de fallas es enumerable y lo podés probar en 10 minutos.

**Tiempo a demo funcionando:** 60–75 min (30 parsear el Excel real, que siempre es peor de lo esperado: headers combinados, filas de subtotal, años como columnas; 25 las tools; 20 el chat).

**Wow factor:** preguntar **por voz, en español rioplatense, con jerga** — *"¿cómo rindió la Spunta en la campaña 2021 comparada con la 2019?"* — y que responda con el número real **y la cita de la fila**. El momento que gana el desafío es el inverso: preguntá algo que **no está en los datos** y que el sistema diga *"no tengo ese dato"* en vez de inventar. Delante de una empresa cuyo dolor declarado es "sin inventar números", demostrar el rechazo vale más que demostrar el acierto. Nadie más va a demostrar su propio límite.

**Gotchas:** el parseo del Excel se come el presupuesto (blindá con `header=None` y normalización manual); ambigüedad → repreguntar, no asumir; si el histórico tiene unidades mezcladas (kg vs t, qq/ha) normalizá explícitamente y mostralo, porque un agrónomo lo va a notar; SheetJS/`xlsx` tiene fricción de licencia/registro en npm — en Python `pandas.read_excel` + `openpyxl` y listo.

### V1-N02 · Dashboard de KPIs + narrativa automática de variaciones

**Stack recomendado:** Streamlit + pandas + Plotly/Altair, y **la narrativa generada desde deltas ya calculados**.

**Por qué es el más rápido:** es el desafío con mejor relación resultado/esfuerzo de los 9. `st.dataframe` + 3 gráficos + `st.metric` con delta es literalmente media hora. La parte "IA" es un solo prompt que recibe una tabla de variaciones **ya computadas** (`{campaña, indicador, valor, delta_pct, magnitud}`) y escribe dos párrafos. El LLM no hace aritmética: detecta *qué es notable* y lo redacta. Eso es exactamente lo que un LLM hace bien y donde no puede alucinar un número, porque los números vienen en la entrada.

**Tiempo a demo funcionando:** 45–60 min.

**Wow factor:** el dashboard es bonito pero legible como "otro dashboard". Lo que levanta la sala es el párrafo que dice *"la campaña 2023/24 cayó 18% en rendimiento respecto de 2022/23, la mayor caída de la serie; superficie se mantuvo, así que la caída es de rendimiento y no de escala"* — porque eso es análisis, no gráfico. **Enriquecelo con las Estimaciones Agrícolas del MAGyP** (CSV abierto, nivel partido, papa, Balcarce) y compará el rendimiento de Papasud contra el promedio del partido: pasa de "gráfico de mis datos" a "mi performance vs. la zona". Casi nadie va a traer eso.

**Gotchas:** riesgo de que quede "solo un dashboard" — la narrativa es el diferencial, no los gráficos; cuidado con la campaña agrícola como etiqueta (2023/24 cruza años calendario, no lo trates como año simple); si hay pocos años con datos completos, mostrá n explícitamente.

### V1-N03 · Modelo predictivo de aptitud de variedad por lote + clima (avanzado)

**Stack recomendado:** scikit-learn (`HistGradientBoostingRegressor` o incluso Ridge) + **Open-Meteo archive** para el clima + importancias de features narradas por LLM. Streamlit.

**Por qué es el más rápido:** el clima es gratis y sin key — `archive-api.open-meteo.com/v1/archive` con ERA5-Land (~11 km, desde 1950) da temperaturas, precipitación y `et0_fao_evapotranspiration` directo, así que podés derivar grados-día y balance hídrico sin otra fuente. ⚠️ **Ojo con el lag de 5 días** de ERA5; para la cola reciente encadená la forecast API. NASA POWER (`community=AG`, sin key, diario desde 1981) sirve como cross-check y para radiación solar — **cacheá la respuesta a un JSON local en la primera llamada**, porque su doc advierte que bloquean a quien pide la misma coordenada en loop (un dev server con hot-reload es exactamente ese patrón).

**El problema real de este desafío no es el modelo, es la honestidad.** Con ensayos in-situ de 20 años probablemente haya cientos de filas, no miles. Un gradient boosting sobre 200 filas con 15 features overfittea y lo va a decir cualquiera que sepa. La respuesta defendible:

- Modelo simple e interpretable (Ridge o un GBM con `max_depth` bajo), validación cruzada honesta, y **reportar el intervalo, no el punto**: "32–38 t/ha" en vez de "34,7 t/ha".
- **Mostrar el n de entrenamiento en la pantalla.** "Basado en 47 ensayos de esta variedad en suelos comparables" es más convincente que cualquier decimal.
- Feature importances (o SHAP si sobra tiempo) → LLM que las traduce a lenguaje de agrónomo: *"la predicción baja principalmente por las precipitaciones acumuladas de diciembre, que en este lote fueron 40% menores al promedio de los ensayos"*.

**Tiempo a demo funcionando:** 90–120 min. **Es el más caro de los tres de V1** y el que más depende de que los datos de Papasud realmente tengan ensayos por variedad × sitio × año. Decisión go/no-go a los 20 minutos de ver el dataset.

**Wow factor:** alto si funciona — es el único de los 9 que produce una *predicción*. La explicación en lenguaje de agrónomo es lo que lo hace legible para el jurado.

**Gotchas:**
- 🚨 **Footgun concreto de sklearn:** en `HistGradientBoostingRegressor`, `early_stopping='auto'` **solo se activa con n≥10.000**. Con tus cientos de filas está **silenciosamente apagado** y el modelo overfittea sin avisar. Seteá `early_stopping=True` explícitamente.
- Dejá un `RidgeCV` **visible** al lado como baseline. Si el GBM no le gana, decilo — y usá el Ridge, que además es explicable sin SHAP.
- Si los datos no soportan un modelo, **pivotear a V1-N02 sin culpa**.
- Nunca presentar un R² de test sobre 30 filas como evidencia; validá **por año**, no aleatorio (leakage temporal).
- No prometas "predice el rendimiento" sino "estima aptitud relativa", que es lo que el dato soporta.

---

## 3. Vertical 02 — Campo inteligente

### V2-N01 · Orden de trabajo desde habla/texto libre

**Stack recomendado:** React + Netlify Function + `<VozInput/>` + tool call forzado + diccionario de insumos con fuzzy match.

**Por qué es el más rápido:** es el desafío que **ya está resuelto en código auditado**. `voz.py` + `transcripcion.py` de [[polpilot-reusable-assets]] hacen exactamente esto: transcripción de tres niveles, interpretación por tool forzado con schema estricto, resolución determinística de identificadores contra catálogo, `confianza:"dudosa"` cuando falta algo, nada persiste sin confirmación. Cambiás `INTENCIONES` (faltante/entrega/reposición) por las de Papasud (tarea/insumo/dosis/lote) y el target del fuzzy matcher de productos a insumos. Vale una decisión go/no-go de 10 minutos al inicio: clonar y vaciar vs. escribir de cero.

**Tiempo a demo funcionando:** 45–60 min desde cero; ~30 si se reusa el código.

**Wow factor:** muy alto y muy legible. Hablar al teléfono *"terminé de aplicar fungicida en el lote 8, tiré 3 litros, todo bien"* y ver aparecer la orden estructurada con lote, tarea, insumo, dosis y fecha es un momento de demo que se entiende sin explicación. **El segundo momento, más fuerte:** decí un insumo que no existe ("le puse producto verde") y que el sistema pregunte *"no reconozco 'producto verde', ¿elegís de la lista?"* en vez de adivinar. Y validá la dosis contra el rango recomendado del diccionario: *"3 l/ha está dentro del rango (2–4)"* — eso es el diccionario que Papasud provee, usado de verdad.

**Gotchas:** el permiso de micrófono necesita **HTTPS** (ver §5.2, el error de los 30 minutos); iOS necesita el fallback; el diccionario de insumos de Papasud puede llegar en un formato imprevisto, así que abstraé la carga; ruido de fondo en la sala del hackathon degrada el STT — grabá el audio de demo antes o hablá cerca del micrófono.

### V2-N02 · Auto-vinculación de fotos + reconocimiento de estado del cultivo

**Stack recomendado:** **EXIF (GPS + timestamp) para vincular** + **LLM multimodal con schema forzado para describir**. React + Netlify Function.

**Por qué es el más rápido:** *la mitad de "auto-vincular" no necesita IA en absoluto.* Si la foto trae GPS y timestamp en EXIF, con `exifr` (JS) leés las coordenadas y con `turf.booleanPointInPolygon` resolvés en qué lote cayó; el timestamp la ata a la orden de trabajo activa de esa fecha. Es **determinístico, instantáneo, explicable y no puede alucinar**. Presentarlo así — "el vínculo es geometría, no un modelo" — es un punto de credibilidad técnica.

🚨 **Pero el EXIF falla más seguido de lo que uno espera, y por eso el orden de construcción es al revés del intuitivo.** Tres razones acumulativas: **Android 10+ redacta la ubicación por defecto** para apps sin permiso explícito; **iOS no incluye GPS cuando la captura viene de la cámara web en vivo**; y **WhatsApp/Telegram re-encodean y borran el EXIF**. Sumado a que Papasud puede haber juntado las fotos por WhatsApp, la probabilidad de que el gallery llegue sin GPS es alta. **Construí el selector manual de lote PRIMERO y el auto-linking por EXIF como mejora encima** — al revés te quedás sin demo. El timestamp sobrevive mucho más seguido que el GPS, así que la vinculación por fecha a la orden activa es el fallback razonable. Nota aparte: **el LLM no ve el EXIF** — hay que leerlo en código y pasárselo, si lo necesita.

Para el reconocimiento, **LLM multimodal con tool forzado gana en una ventana de 3 horas** — pero por tiempo, no por precisión, y conviene ser honesto sobre eso. La evidencia 2026 es dura en ambas direcciones: sobre 27 datasets agrícolas, el mejor VLM (Gemini-3 Pro) llega a **~62% de accuracy en closed-set y &lt;25% en open-ended**, y un YOLO11 supervisado los supera a todos ([arXiv 2512.15977](https://arxiv.org/abs/2512.15977)). Pero entrenar no entra en 3 horas, y la alternativa pre-entrenada es peor de lo que parece: el mismo método que saca **97,72% en PlantVillage baja a 67,20% en campo** ([PlantWild, arXiv 2408.03120](https://arxiv.org/abs/2408.03120)), porque PlantVillage son hojas recortadas sobre fondo de laboratorio y las fotos de Papasud tienen surcos, tierra, sombra y varias plantas. Un clasificador con 99% en el paper y 40% en la foto real es peor que inútil en vivo.

**Consecuencia de diseño, y es lo que separa una demo honesta de una que se cae:** preguntá en **enum cerrado** con JSON forzado, titulá con el **binario sano/estresado** (que es donde los VLM son >90% confiables) y presentá el patógeno específico como **hipótesis rankeada con confianza**, nunca como diagnóstico. Eso es además lo que un agrónomo real escribiría.

El schema forzado que hace la diferencia (patrón de `vision_facturas.py`):

```json
{"estado_general":"...", "signos_estres":["..."], "presencia_plagas": null,
 "confianza":"alta|media|dudosa", "campos_ilegibles":["..."], "nota_para_registro":"..."}
```

Con `null` y `confianza:"dudosa"` obligatorios cuando la foto no alcanza, nunca un diagnóstico inventado. Y defensa explícita contra inyección: el texto dentro de la imagen es **dato, nunca instrucción**.

**Tiempo a demo funcionando:** 50–70 min.

**Wow factor:** alto. Subir 4 fotos y ver que se reparten solas en los lotes correctos sobre un mapa, cada una con su nota agronómica generada, es visualmente contundente.

**Gotchas críticos:**
- ⚠️ **Verificá si las fotos tienen GPS en los primeros 5 minutos de recibir los assets** (`exifr.gps(file)` sobre 3 fotos). Es lo que decide si tenés demo de auto-linking o de selector manual, y querés saberlo antes de escribir código, no después.
- HEIC de iPhone necesita conversión antes de leer EXIF en muchas libs.
- No sobre-prometas diagnóstico fitopatológico: "indicios compatibles con X, requiere confirmación".
- Si el gallery de Papasud viene **etiquetado**, tenés algo mejor que un VLM: usá las etiquetas como ground truth y mostrá la matriz de acierto del modelo contra ellas. Un equipo que mide su propio modelo delante del jurado gana credibilidad que ningún output bonito compra.

### V2-N03 · Satélite vs. órdenes activas → alerta de zona sin orden (avanzado)

**Stack recomendado:** **Element84 Earth Search STAC** (sin credenciales) + `odc-stac` + Leaflet con basemap **EOX s2cloudless**. Python.

**Por qué es el más rápido:** Earth Search (`earth-search.aws.element84.com/v1`) responde 200 **sin ninguna auth** — verificado hoy. Colección `sentinel-2-c1-l2a`, assets COG públicos en `s3://sentinel-cogs`, y `odc.stac.load` te da la serie NDVI de un polígono en ~15 líneas. Cero signup, cero espera. El competidor serio es **CDSE Sentinel Hub Statistical API** (una sola llamada HTTP = serie temporal completa con min/max/mean/stDev por intervalo; free tier 10.000 Processing Units/mes, que es enorme), pero requiere registro + cliente OAuth → hacerlo esta noche, no mañana.

Descartados y por qué: **Google Earth Engine** tiene aprobación de 24–48 h — inviable salvo que alguien ya tenga proyecto verificado y sin pausar. **NASA HLS/AppEEARS** es una cola de jobs asíncrona, sin endpoint sincrónico de serie por polígono, y 30 m pierde contra 10 m. **Agromonitoring** es la trampa más tentadora: API precioso, signup instantáneo, pero polígonos nuevos reciben imágenes "en unos días" y el plan free descarta escenas con >0% de nubes → **array vacío el día del hackathon**. Solo funciona si creás los polígonos con días de anticipación.

**Chequeo de resolución (decilo en la demo, suma credibilidad):** B04/B08 son 10 m → 1 píxel = 100 m², **1 ha = 100 píxeles**. Un lote de 5 ha son ~500 píxeles, uno de 20 ha ~2.000. Suficiente de sobra para media/mediana/desvío y para dibujar variabilidad intra-lote. Aplicá un buffer interno de 1–2 píxeles para no contaminar con caminos y cabeceras. Revisita: 2B + 2C garantizan 5 días nominales → **2–3 días a la latitud de Balcarce (~37,8°S)**. (No afirmes constelación de 3 satélites sin verificar el estado de 2A después del 13-mar-2026.)

**Tiempo a demo funcionando:** 90–120 min. El más riesgoso de los 9.

**Wow factor:** el más alto de todos si sale — un mapa con lotes coloreados por NDVI, una zona en rojo, y la alerta *"posible estrés hídrico en lote 8, sin orden de riego en los últimos 21 días"*. Es la narrativa completa del desafío en una pantalla.

**Gotchas críticos:**
- 🚨 **El problema del calendario, no de la nube.** En agosto los lotes están en barbecho: NDVI bajo y plano, y va a parecer que tu código está roto. **Hardcodeá la ventana a la campaña 2025/26 (oct-2025 → abr-2026)** y obtenés una curva hermosa de green-up y senescencia, además de poder elegir escenas limpias de un archivo cerrado.
- Filtrar por `eo:cloud_cover < 20` a nivel escena es demasiado grueso para 20 ha: una escena 60% nublada puede tener tu lote perfectamente despejado. Filtrá por **fracción de píxeles válidos del polígono** (`sampleCount` vs `noDataCount`, o el ratio de la máscara SCL) y descartá fechas bajo ~70%.
- Si usás `sentinelhub-py`: su `sh_base_url` por defecto apunta al servicio **comercial**, contra el cual tus credenciales CDSE **no autentican**. Olvidar las dos líneas de config es el error clásico de 30 minutos.
- Los nombres de asset difieren entre colecciones (`red`/`nir` vs `B04`/`B08`) — imprimí `items[0].assets.keys()` primero.
- Earth Search no tiene SLA ("no guaranteed service") → **cacheá los resultados a disco antes de la demo**.

---

## 4. Vertical 03 — Stock, trazabilidad y compliance

### V3-N01 · Stock unificado de 4 ubicaciones + movimientos por voz/texto con validación

**Stack recomendado:** React + Netlify DB (Postgres) o Blobs + `<VozInput/>` + el mismo `/api/extraer`.

**Por qué es el más rápido:** reusa el 90% de V2-N01 con otro schema (`{lote, cantidad, origen, destino, fecha}`) y agrega una sola regla de negocio: validar disponibilidad en origen antes de confirmar. ~150 lotes × 4 ubicaciones es un dataset trivial. Si ya hiciste V2-N01, esto son 30 minutos.

**Tiempo a demo funcionando:** 40–55 min (o ~30 si V2-N01 ya existe).

**Wow factor:** medio-alto. El momento fuerte no es registrar el movimiento exitoso, es **el rechazo**: *"querés mover 500 kg del lote 42 desde Frigorífico A, pero A tiene 480 kg verificados"* → bloqueo con el número real. Un operario de depósito en la sala entiende ese dolor inmediatamente. La otra mitad del valor es conceptual y vale decirla: la planilla compartida que varias personas editan a la vez es un problema de *concurrencia*, y una base con validación al escribir lo elimina por construcción, no por disciplina.

**Gotchas:** modelá movimientos como **libro de asientos append-only** (origen −, destino +) y derivá el stock, no guardes un saldo mutable — es más rápido de escribir *y* es lo que habilita el N02; cuidado con las unidades (kg vs bolsas vs big bags de 1.000 kg); mostrá siempre las 4 ubicaciones aunque estén en cero.

### V3-N02 · Panel en tiempo real que BLOQUEA remitos + hipótesis de discrepancia

**Stack recomendado:** lo de N01 + una vista de conciliación + un prompt de hipótesis alimentado con el historial de movimientos del lote.

**Por qué es el más rápido:** si el stock es un libro append-only, la discrepancia declarado-vs-contado **ya es computable** y la hipótesis es un prompt sobre una lista de asientos que el LLM lee para encontrar el eslabón faltante. No hace falta nada estadístico: los patrones son enumerables (un movimiento con salida registrada y sin entrada en destino, un conteo sin ajuste, una unidad mal cargada) y el LLM los reconoce y los redacta en castellano llano.

**Tiempo a demo funcionando:** 60–75 min sobre N01.

**Wow factor:** alto — es el desafío con la narrativa de negocio más nítida de los 9. El guion se cuenta solo: intento emitir el remito → **bloqueo** → discrepancia de 20 kg → hipótesis *"un movimiento del 12/08 salió de Frigorífico B y nunca se registró en destino"* → click al asiento sospechoso → corrijo → ahora sí emite. Esos son los 5 minutos completos, con principio y final, y termina en un resultado. El dolor declarado de Papasud es "las discrepancias se descubren al entregar el pedido del cliente"; esta demo mueve el descubrimiento a *antes* de emitir. Eso es plata, y el jurado lo ve.

**Gotchas:** sembrá la discrepancia a propósito en los datos de demo (si no, no hay nada que mostrar); la hipótesis debe presentarse como hipótesis ("probablemente", con el asiento citado y clickeable), nunca como certeza; "tiempo real" con un solo usuario en la demo es fácil — no prometas resolución de conflictos multi-usuario que no construiste.

### V3-N03 · Copiloto de documentación de exportación (avanzado)

**Stack recomendado:** trazabilidad del lote (de N01) → pre-llenado → **HTML + CSS `@page` → print-to-PDF del navegador**, o WeasyPrint + Jinja2 si el equipo va en Python.

**Por qué es el más rápido:** el camino más veloz a un PDF que se vea bien es HTML con `@page` y el diálogo de impresión — cero dependencias, cero binarios. Si necesitás generar el archivo server-side, **WeasyPrint + Jinja2** (ya probado en [[polpilot-reusable-assets]]) evita el dolor de empaquetar Chromium en serverless, que es el gotcha clásico: Puppeteer/Playwright en Netlify Functions choca contra límites de tamaño del bundle. `pdf-lib` rellenando AcroForms de un PDF real es más "creíble" conceptualmente pero mucho más lento de montar y requiere tener el formulario oficial.

**Este es el desafío donde el conocimiento de dominio vale más que el código,** y donde la investigación de hoy da una ventaja desproporcionada. El set documental real:

| Documento | Organismo | Detalle que da credibilidad |
|---|---|---|
| **Factura E** (electrónica de exportación) | ARCA/DGA | `CAE` + vto., NCM **0701.10.00**, Incoterm 2020, peso neto/bruto, se imputa a **hasta 5 permisos de embarque** |
| **Certificado Fitosanitario de Exportación** | SENASA, vía **CERT-POV** (módulo de SIGPV) | Modelo **CIPF/NIMF 12**, 14 casilleros; `Nombre botánico: Solanum tuberosum L.`; casillero **Declaración Adicional** |
| **Certificado de Origen MERCOSUR (ACE 18)** | Cámara de comercio | Layout post-Decisión CMC 05/23: **se agregó campo 11 `N° y fecha DJO`**, se quitaron consignatario/país destino/medio de transporte. Emisión: dentro de **60 días** de la factura; validez **180 días** |
| **Packing list** | Exportador | Por línea: variedad, categoría, generación, N° de lote INASE, **rango de rótulos**, calibre, bultos, peso neto/bruto |
| **Certificado INASE de exportación** | INASE, Res. 56/18 vía TAD | + Res. SAGYP 715/94 (Papa); **válido 60 días corridos** |
| **Rótulo oficial de papa semilla** | INASE (entregado con el **DAV**) | Clase fiscalizada, categoría/subcategoría, variedad, zona, año de cosecha, N° R.N.C. y F.S.; **"MATERIAL TRATADO CON VENENO" en letras rojas** si corresponde; máx. 50 kg (Inicial I y menores) / 20 kg (Preiniciales) |
| **Permiso de embarque OM-1993-A** | SIM/MALVINA | Destinación `EC01`; certificados adjuntos vía **Servicio de Recepción de LPCO** |

Para hacerlo concreto con Brasil (mercado principal): **IN MAPA 18/2004** exige que la papa semilla argentina esté libre de *Premnotrypes latithorax*, *Nacobbus aberrans* y *Meloidogyne chitwoodi*, con Declaración Adicional sobre *Meloidogyne fallax* según análisis oficial. Y Brasil exige además un **"Certificado de Batata-Semente" o equivalente** que pruebe fiscalización oficial — o sea, el papeleo de INASE es requisito de importación duro, no un adorno. Uruguay pide además libre de *Spongospora subterranea* y *Ralstonia solanacearum* raza 1 → **branching por destino**, que es un gran momento de demo.

**Tiempo a demo funcionando:** 75–100 min.

**Wow factor:** alto con el jurado correcto (si hay alguien de Papasud que haya sufrido este trámite, es el ganador absoluto), más bajo si el jurado es puramente técnico — un PDF es menos vistoso que un mapa satelital. **El movimiento que lo hace ganar no es generar el documento, es detectar el error:** NCM 0701.10.00 vs 0701.90.00 (semilla vs consumo); certificado de origen emitido a más de 60 días de la factura; peso neto que no cuadra entre Factura E y packing list; falta la Declaración Adicional de la plaga que exige *ese* destino; rótulo que excede el tope de kg de su categoría; certificado INASE vencido. Eso es un copiloto, no un generador de plantillas.

**Gotchas:** ⚠️ **marcá todo PDF con `DEMO — SIN VALOR LEGAL / NO OFICIAL`** — son documentos que imitan instrumentos oficiales argentinos y no querés ambigüedad; las tolerancias sanitarias numéricas viven en los Anexos I–V de la Res. 245/98 que no están online, así que presentalas como filas `Tolerancia (%)` marcadas DEMO y no las inventes con tono de autoridad; **DJVE no aplica** (es para granos y oleaginosas, no papa semilla) — mencionarla te delata; usá `Categoría: Certificada – Registrada · Generación: G3` para alinear con lo que Papasud realmente vende.

---

## 5. Ranking: mejor demo alcanzable en menos de 3 horas

Puntajes 1–5. **Riesgo** invertido (5 = menos riesgo). "Legibilidad" = qué tan rápido un jurado no-técnico entiende el valor.

| # | Sub-desafío | Velocidad | Wow | Legibilidad | Riesgo↓ | **Total** |
|---|---|:---:|:---:|:---:|:---:|:---:|
| 🥇 | **V2-N01** Orden de trabajo por voz | 5 | 4 | 5 | 5 | **19** |
| 🥈 | **V3-N02** Bloqueo de remito + hipótesis | 3 | 5 | 5 | 4 | **17** |
| 🥉 | **V1-N01** Copiloto conversacional | 4 | 4 | 5 | 4 | **17** |
| 4 | **V1-N02** Dashboard + narrativa | 5 | 3 | 4 | 5 | **17** |
| 5 | **V3-N01** Stock unificado por voz | 4 | 3 | 4 | 5 | **16** |
| 6 | **V2-N02** Fotos: EXIF + visión | 3 | 4 | 4 | 3 | **14** |
| 7 | **V3-N03** Documentación de exportación | 2 | 4 | 4 | 3 | **13** |
| 8 | **V2-N03** Satélite vs. órdenes | 1 | 5 | 4 | 2 | **12** |
| 9 | **V1-N03** Modelo predictivo | 2 | 4 | 3 | 2 | **11** |

**Lectura del ranking.** V2-N01 gana por construcción: código reusable auditado, wow inmediato, y el menor riesgo de los 9. V3-N02 y V1-N01 empatan detrás con más upside y más costo. Los tres avanzados (V1-N03, V2-N03, V3-N03) tienen el techo más alto y son donde mueren los equipos — **elegí uno avanzado solo si el nivel de dificultad pesa explícitamente en el criterio del jurado** (el documento de Papasud dice que cada equipo elige un nivel, así que probablemente pese algo).

**Tres de los nueve puntajes dependen de un dato que todavía no tenés**, y conviene tratarlos como condicionales hasta las 10:30: V1-N03 necesita que existan ensayos por variedad × sitio × año (si no, no hay modelo); V2-N02 necesita que las fotos conserven GPS (si no, cae a selector manual y pierde el wow del auto-linking); V2-N03 necesita las coordenadas de los lotes. **Los tres son go/no-go a los 20 minutos de ver los assets**, y los tres degradan a un desafío N01/N02 de la misma vertical sin tirar código a la basura — que es precisamente el argumento del andamio compartido de §1.

### 5.1 La recomendación

**Combo ganador: V2-N01 + V3-N01/N02 como una sola app.** Comparten el 90% del código (voz → extracción estructurada → validación → confirmación humana) y juntos cuentan una historia mucho más grande que cualquiera de los dos: *"el ingeniero dicta desde el lote, el operario dicta desde el frigorífico, y administración ve un solo stock que no la deja emitir un remito falso"*. Cubre 2 de las 3 verticales y 2 niveles de dificultad, en el presupuesto de tiempo de un solo desafío bien elegido.

**Si el equipo es 1 sola persona:** V1-N02 (dashboard + narrativa) en Streamlit. Es el único que garantiza algo terminado y presentable, y "terminado" gana a "ambicioso y roto" en una demo de 5 minutos con ganador elegido en la sala.

**Si el equipo son 3 y uno es fuerte en datos/Python:** V2-N01 + V3-N02 en React (dos personas) y V1-N02 en paralelo (una persona), unificados por el mismo seed. Tres pantallas, una historia.

### 5.2 Riesgos de día de demo, en orden de probabilidad

1. 🚨 **El error de los 30 minutos: `http://192.168.x.x:5173` no es contexto seguro.** Los orígenes confiables son HTTPS, `localhost` y `127.0.0.1` — **las IP de LAN privada no están incluidas**. Abrir tu dev server desde el teléfono por IP da **cámara, micrófono y service worker todos muertos**, con `navigator.mediaDevices` literalmente `undefined` (guardá con `if (!navigator.mediaDevices)`, no con try/catch). Se arregla deployando a HTTPS en los primeros 20 minutos. Alternativa en Android: port forwarding por USB de Chrome DevTools, que hace que el teléfono lo cargue como `localhost` por cable — inmune al wifi del venue.
2. **Olvidar el deploy a producción que activa el AI Gateway** → tus llamadas locales al LLM fallan y vas a debuggear lo incorrecto.
3. **Wifi del venue.** Mitigación en orden: seed local (10 min, mata una clase entera de fallas) → **hotspot del celular, ignorando el wifi del venue** → video de 90 s pregrabado. Para móvil en proyector: **scrcpy por USB** en Android (35–70 ms, nada que instalar en el teléfono, cero wifi); device toolbar de Chrome como fallback. **AirPlay depende del wifi — no lo uses acá.** El QR para que los jurados abran la app: mostralo **al final** como "probalo vos", nunca como el camino de la demo.
4. **Quemar los 3.000 créditos de Netlify.** $1 de inferencia = 180 créditos → tu asignación completa son **~US$16,60 de LLM**. Deploy a producción cuesta 15 créditos cada uno; **deploy previews y branch deploys son 0** → iterá en una branch. Usá un modelo chico en el camino de demo.
5. **`capture="environment"` sobre `getUserMedia`.** Una línea, sin máquina de estados de permisos, soportado desde iOS Safari 6, y abre la **cámara nativa** — lo que además *parece* más una app de campo real que un `<video>` en un div. Si necesitás `getUserMedia`, usá `facingMode: {ideal:"environment"}`, nunca `{exact:...}` (con `exact` la request entera falla si no hay cámara que matchee).
6. **PWA: hacé el manifest, salteá la ceremonia de instalación** (~8 min). No necesitás service worker para instalabilidad. `beforeinstallprompt` sigue siendo solo-Chromium y **no existe en iOS**. Lo eficiente: **instalá la app en tu propio teléfono de demo durante la hora 2** y presentá desde el ícono del home screen. Misma óptica sin chrome de browser, cero código.

---

## 6. Para hacer ESTA NOCHE (21-ago)

Cuentas y claves — ninguna toma más de 10 minutos, todas son bloqueantes si faltan mañana:

### Bloqueante — hacelo sí o sí
- [ ] **Reclamar los créditos de los sponsors.** Netlify (formulario en el Luma), Render (`credits-portal-mmdm.onrender.com/claim/cafe-cursor`), Exa (`EXA50CURSOR`), Firecrawl (`FIRECRAWL10KCURSOR`), Wispr Flow (`ref.wisprflow.ai/cursor`, tocar "Upgrade to Pro").
- [ ] **Netlify: crear el proyecto Y HACER UN DEPLOY A PRODUCCIÓN.** Es lo que activa el AI Gateway. Verificá que `ANTHROPIC_API_KEY` llegue a una function con un `console.log(!!process.env.ANTHROPIC_API_KEY)`. **Si mañana esto no está hecho, perdés la primera hora.**
- [ ] `npm i -g netlify-cli` y `netlify login`.
- [ ] **Groq API key** (`console.groq.com`) — el fallback de STT. Free tier: 20 RPM, 8 h de audio/día. Gratis, 2 minutos.
- [ ] Instalar y probar **Wispr Flow** en tu propia máquina — para dictarle a Cursor, que es su único uso válido acá. Probalo antes, no en el hackathon.

### Alto valor — 10 minutos cada uno, gran retorno
- [ ] **CDSE (Copernicus Data Space):** registro + verificación por email + **crear el OAuth client y guardar el secret AHORA** (no es recuperable después). Probá una llamada de token. Solo si vas a intentar V2-N03.
- [ ] **Descargar las Estimaciones Agrícolas del MAGyP** (`datos.magyp.gob.ar`, dataset `estimaciones-agricolas`), filtrar a `papa` + Buenos Aires, y commitearlo. Resolvé la URL del recurso desde la página del dataset, no la hardcodees. **Este es el enriquecimiento de mejor relación valor/minuto de toda la lista.**
- [ ] **Dibujar 2–3 polígonos de lotes de Balcarce** en geojson.io y commitearlos como GeoJSON.
- [ ] Probar `earth-search.aws.element84.com/v1/collections` (sin auth, debe dar 200) y una carga de `odc-stac`.
- [ ] Probar una llamada a Open-Meteo archive para Balcarce (`-37.85, -58.25`) y cachear el JSON.

### Andamio — que mañana sea copiar, no escribir
- [ ] `pnpm dlx shadcn@latest init -t vite` en un repo limpio + `@netlify/vite-plugin`, deployado y verificado.
- [ ] Escribir `<VozInput/>` con el array `phrases` del glosario papero ya cargado.
- [ ] Escribir el esqueleto de `/api/extraer` con tool call forzado y `strict: true`.
- [ ] Decisión go/no-go sobre [[polpilot-reusable-assets]]: clonar el repo y ojear `voz.py`, `transcripcion.py` y `paleta.js` **esta noche**, para que mañana sea una decisión de 2 minutos y no de 20.
- [ ] Preparar el `seed.json` con datos sintéticos plausibles: variedades reales (Spunta, Innovator, Asterix, Kennebec, Atlantic), rendimientos creíbles (**Spunta/Kennebec/Atlantic 20–35 t/ha; Asterix/Innovator 35–47 t/ha** con buen manejo, según ensayos de INTA Balcarce), 4 ubicaciones, ~150 lotes, **y una discrepancia sembrada a propósito** para V3-N02.
- [ ] Grabar audio de demo en español con la jerga, por si la sala está ruidosa.

### No hagas
- ❌ No pierdas tiempo con la API de Wispr Flow (aprobación comercial).
- ❌ No cuentes con Google Earth Engine (24–48 h de aprobación).
- ❌ No cuentes con Agromonitoring salvo que crees los polígonos **hoy**.
- ❌ No planifiques sobre Hugging Face Spaces (Gradio/Docker requieren plan pago).
- ❌ No metas LLM local (Ollama / Prompt API de Chrome): la descarga del modelo necesita justo la red en la que no confiás.

---

## 7. Fuentes

**Voz/STT:** [MDN SpeechRecognition](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition) · [MDN phrases (sesgo)](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition/phrases) · [caniuse speech-recognition](https://caniuse.com/speech-recognition) · [Groq STT](https://console.groq.com/docs/speech-to-text) · [OpenAI STT](https://developers.openai.com/api/docs/guides/speech-to-text) · [Deepgram keyterm](https://developers.deepgram.com/docs/keyterm) · [Wispr Flow API — acceso exclusivo](https://api-docs.wisprflow.ai/introduction)

**Satélite/clima:** [Earth Search v1 (live, sin key)](https://earth-search.aws.element84.com/v1/collections) · [CDSE Quotas](https://documentation.dataspace.copernicus.eu/Quotas.html) · [CDSE Statistical API](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Statistical/Examples.html) · [GEE Noncommercial Tiers](https://developers.google.com/earth-engine/guides/noncommercial_tiers) · [Agromonitoring FAQ](https://agromonitoring.com/faq) · [EOX Maps](https://maps.eox.at/) · [Open-Meteo Historical](https://open-meteo.com/en/docs/historical-weather-api) · [NASA POWER](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) · [MAGyP Estimaciones Agrícolas](https://datos.magyp.gob.ar/dataset/estimaciones-agricolas)

**Comercio exterior / semilla:** [INASE Res. 245/98 (papa semilla)](https://servicios.infoleg.gob.ar/infolegInternet/anexos/50000-54999/53715/norma.htm) · [INASE Res. 42/00 (rótulos, DAV)](https://servicios.infoleg.gob.ar/infolegInternet/anexos/60000-64999/62748/texact.htm) · [INASE import/export de semillas](https://www.argentina.gob.ar/servicio/solicitar-la-importacion-y-exportacion-de-semillas) · [SENASA CERT-POV](https://www.argentina.gob.ar/Senasa/portal-de-certificacion-fitosanitaria-de-exportacion/inicio-de-tramite-de-exportacion-cert-pov) · [CDA — Régimen de Origen MERCOSUR](https://www.cda.org.ar/detalle_noticia.php?id=41518) · [Cultivar — exigências batata-semente](https://revistacultivar.com.br/artigos/exigencias-de-importacao-de-batata-semente) · [MAGyP informe papa (NCM)](https://www.argentina.gob.ar/sites/default/files/magyp-informe-papa-mayo-2021.pdf)

**Deploy/scaffold:** [Netlify AI Gateway](https://docs.netlify.com/build/ai-gateway/overview/) · [Netlify Database](https://docs.netlify.com/build/data-and-storage/netlify-database/getting-started/) · [Netlify Functions config](https://docs.netlify.com/build/functions/configuration/) · [Cómo funcionan los créditos](https://docs.netlify.com/manage/accounts-and-billing/billing/billing-for-credit-based-plans/how-credits-work/) · [Render free tier](https://render.com/docs/free) · [Gradio sharing](https://www.gradio.app/guides/sharing-your-app) · [MDN BeforeInstallPromptEvent](https://developer.mozilla.org/en-US/docs/Web/API/BeforeInstallPromptEvent)

**Visión/ML:** [VLMs en agricultura — 27 datasets (arXiv 2512.15977)](https://arxiv.org/abs/2512.15977) · [PlantWild — brecha lab vs. campo (arXiv 2408.03120)](https://arxiv.org/abs/2408.03120)

**Estadística para el pitch:** [DeHoratius & Raman, Management Science 2008](https://doi.org/10.1287/mnsc.1070.0789) · [Panko, EuSpRIG 2015](https://arxiv.org/abs/1602.02601) · [Panko, overconfianza](https://arxiv.org/abs/0802.3457) · [EuSpRIG horror stories](https://eusprig.org/research-info/horror-stories/)

**Agronomía:** [INTA — variedades y rendimientos](https://intainforma.inta.gob.ar/el-cultivo-de-papa-renace-en-el-valle-sureno/) · [La Capital MdP — Papasud, papa semilla G3](https://www.lacapitalmdp.com/tradicion-tecnologia-y-paciencia-en-la-produccion-de-papa-semilla/)

## 8. Sin verificar / preguntar mañana

- Formato, volumen y anonimización reales de los datos de Papasud (bloquea V1-N03 y V2-N02 en particular).
- Si las fotos del gallery conservan EXIF/GPS — **medilo, no lo preguntes**: `exifr.gps(file)` sobre 3 fotos en los primeros 5 minutos. Entre Android 10+ redactando ubicación, iOS omitiéndola en captura web, y WhatsApp borrando EXIF, lo más probable es que no haya GPS.
- Si el gallery viene etiquetado y con qué taxonomía (habilita medir el modelo contra ground truth).
- Estado de Sentinel-2A después del 13-mar-2026 (no afirmar constelación de 3 satélites sin chequear).
- Tolerancias sanitarias numéricas de los Anexos Res. 245/98 (no publicados online).
- Límites de recursos de Streamlit Community Cloud; fricción de DuckDB-WASM/PGlite con Vite; emulación de viewport móvil en Cursor Browser.
- Si el criterio del jurado premia explícitamente el nivel de dificultad elegido.
