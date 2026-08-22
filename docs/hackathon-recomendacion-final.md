---
tags: [hackathon, papasud, recomendacion, plan]
date: 2026-08-21
status: decision
---

# Recomendación final y plan de build — [[cursor-hackathon-mar-del-plata-2026]]

Síntesis de toda la investigación. Fuentes internas:
[[papasud-company-research]] · [[papa-semilla-modelo-de-datos]] · [[hackathon-demo-strategy]] · [[polfin-reusable-assets]] · [[polpilot-reusable-assets]] · [[hackathon-technical-feasibility]] · [[papasud]]

---

## Decisión: **Vertical 03 — N01 + N02**, con N03 como stretch demostrativo

> **"Una sola verdad" — sistema de stock y cadena de custodia para las 4 ubicaciones, con carga por voz y bloqueo de despacho ante discrepancias.**

### Por qué V03 y no V01 (que es la tentación obvia)

| Criterio | V01 (Excel/copiloto) | V02 (campo) | **V03 (stock)** |
|---|---|---|---|
| Depende de la calidad de los datos que llegan el día del evento | **Alta** — si el Excel viene sucio se pierde 1h limpiando | Media | **Baja** — se puede sembrar data sintética creíble |
| Saturación esperada entre 102 participantes | **Muy alta** — es el demo más reconocible | Media | **Baja** |
| Respaldo de la investigación como dolor real | Alto | Medio | **El más alto** |
| Riesgo de falla en vivo | Bajo | **Alto** (N03 satelital, vision) | Bajo |
| Encaje con boilerplate propio | Muy alto | **Bajo** (no hay upload/storage/vision) | Alto |
| Validaciones demostrables en vivo | Pocas | Pocas | **Tres, contundentes** |

**El argumento decisivo:** la investigación mostró que las "4 ubicaciones" del brief son el **final de una cadena de custodia de 3 a 7 años que cruza 1.800 km y dos provincias** (laboratorio → El Calafate → Tres Arroyos/Gonzales Chaves/San Cayetano → General Pueyrredón). Y el **76,3% de las exportaciones argentinas de papa semilla** dependen de que esa genealogía sea reconstruible. El "conflicto de versiones en una planilla" no es un problema de inventario: es un problema de **trazabilidad fiscalizada**.

Nadie más va a llegar con ese encuadre. Es el diferencial.

### Por qué N01+N02 juntos y no N03

El brief dice explícitamente que los niveles existen para que equipos de distinta experiencia tengan "una meta alcanzable en un día" — **N03 no vale automáticamente más**. N01+N02 es la unidad natural: N02 (vista única + bloqueo + hipótesis) *necesita* los datos que genera N01 (carga por voz). Entregar ambos completos y pulidos > entregar N03 a medias.

De N03 se muestra **una sola pantalla** al final (pre-completado de documentación de exportación desde la trazabilidad del lote) como "hacia dónde va", sin construirlo entero.

---

## Qué se construye, concretamente

### El núcleo (no negociable)

1. **Modelo de datos de linaje** — `lote` con `lote_padre_id`, `variedad` como entidad con obtentor/licencia, `movimiento` como append-only, `stock` como **vista derivada** (nunca una celda editable). Esquema completo listo en [[papa-semilla-modelo-de-datos]].
   → Esto es lo que elimina el conflicto de versiones. **Decirlo en la demo: "el problema de la planilla no lo resuelve la IA, lo resuelve el modelo de datos. La IA resuelve la captura."**

2. **Carga de movimientos por voz (es-AR)** — dictar *"pasé 20 bolsones del lote 42 del frigorífico 2 al galpón"* → transacción estructurada `{lote, kg, origen, destino}` → resumen editable → confirmación humana → persistencia.
   Patrón: **forced tool call** con schema estricto (de [[polpilot-reusable-assets]]); el LLM extrae *lenguaje*, un matcher determinístico resuelve *identificadores* contra el catálogo real y propone candidatos ranqueados. Nunca deja que el modelo elija el lote solo. Nunca inventa una cantidad no dicha (`null` + `confianza: 'dudosa'`).

3. **Vista única de las 4 ubicaciones** — tabla/tablero del saldo derivado por lote × ubicación, con drill-down a los movimientos que lo componen.

### Las tres validaciones que se demuestran en vivo

Son el corazón de la demo. Cada una es imposible en una planilla:

| # | Validación | Qué se ve en pantalla |
|---|---|---|
| 1 | **Stock insuficiente** | Intentar emitir remito por 500 kg cuando el saldo da 480 → **bloqueo**, con los movimientos que componen ese saldo |
| 2 | **Linaje inválido** (el diferencial) | Registrar un lote `inicial_I` cuyo padre es `certificada` → **rechazo citando Art. 2 de la Res. INASE 171/2000** en la UI |
| 3 | **Discrepancia declarado vs. contado** | Comparar saldo vs. último conteo → listar movimientos candidatos (sin espejo en destino, o `confianza: dudosa`) → **el LLM redacta la hipótesis sobre esa lista acotada**, nunca sobre la base entera |

La #2 es la que separa "hicimos un CRUD con voz" de "entendimos que este negocio está fiscalizado". Ningún otro equipo va a citar una resolución del INASE en su UI.

### El momento de credibilidad (0:45 del final)

Mostrar **a propósito** que el sistema se frena: *"no reconozco este insumo, elegí de la lista"* / *"hay una discrepancia, no puedo emitir el remito"*. Para un jurado no-técnico esto pesa más que un feature extra — Papasud **vive de la confianza de sus clientes**, y un sistema que se sabe frenar les habla directo. Ver [[hackathon-demo-strategy]].

---

## Stack

**Next.js + el boilerplate propio, reutilizado abiertamente.** Ver [[polfin-reusable-assets]] para rutas exactas.

Ya resuelto y reutilizable:
- `WebSpeechDictationAdapter` a **`es-AR`** — voz, ya cableada, gratis, sin API key, sin backend
- Loop agéntico de tool-use de Anthropic con manejo de rate-limit y degradación elegante
- **Tools presentacionales** (`mostrarGrafico`/`mostrarTabla`) que devuelven `{ok:true}` con los datos en los args → React renderiza desde `props.args`. **Cero riesgo de alucinación numérica.**
- `tool-call.tsx` — disclosure colapsable request/result = **la UI de cita de fuente** que el desafío pide
- `scripts/migrate.mjs` — runner de migraciones `pg` standalone, sin CLI de Supabase
- Paleta: `#fbfbfa` / `#21201d`, y `hielo #2b7a8c` ya tokenizado como "capital congelado" — apropiado para frigoríficos

> ⚠️ **Sobre la reutilización: declararla, no esconderla.** Existe `scripts/clone-for-hackathon.sh` en polfin, que reescribe los timestamps de todos los commits para que la historia parezca creada entre 10:20 y 15:40 del 22/08. **No usarlo.** Su única función es ocultar que el trabajo preexistía, frente a 102 competidores y un premio de $1M ARS puesto por Papasud.
>
> Y no hace falta: partir de boilerplate propio es legítimo y habitual. La versión honesta es **más fuerte** en la sala — *"vinimos con nuestro andamiaje propio (loop de tools, dictado es-AR, runner de migraciones) y usamos el día para construir el dominio de Papasud encima"*. Los jurados desconfían de un producto sospechosamente terminado; premian un día de trabajo visible y bien acotado. Además, un evento sponsoreado por Cursor valora el *proceso* de construir con IA, y los organizadores pueden pedir verlo.

**Nota sobre Python vs React:** la investigación de scaffolding concluye que Gradio/Streamlit llegan a una pantalla en 3-6 min vs 20-35 min de React+AI SDK desde cero. **Para nosotros no aplica**: no partimos de cero, y dos de tres verticales tienen usuarios con el celular en la mano (operario en el frigorífico) — Streamlit es malo en mobile. El boilerplate propio invierte la ecuación.

---

## Plan hora por hora (10:00 – 16:00)

| Hora | Qué | Nota |
|---|---|---|
| **10:00–10:10** | **Deploy hello-world a Netlify.** | Activa el AI Gateway (requiere un deploy previo) y confirma el pipeline de deploy con 5 horas de margen. |
| **10:10–10:20** | Ver los assets reales de Papasud. **Decidir el mapeo de esquema recién acá.** | El brief admite que los assets no estaban definidos. No asumir formato antes. |
| **10:20–10:40** | Escribir el **guion de la demo** de 5 min, cronometrado. | **Antes de escribir código.** El guion define qué features hacen falta; al revés se construye lo que no entra. |
| **10:40–11:30** | Migraciones + seed. Modelo de linaje andando, datos sembrados y creíbles. | Esquema ya escrito en [[papa-semilla-modelo-de-datos]] — es transcribir, no diseñar. |
| **11:30–12:45** | Captura por voz → movimiento estructurado → confirmación → persistencia. | El camino crítico. Si esto no anda, no hay demo. |
| **12:45–13:30** | Vista única de las 4 ubicaciones + drill-down a movimientos. | |
| **13:30–14:15** | Las **tres validaciones** (stock insuficiente, linaje inválido, discrepancia + hipótesis LLM). | Acá está el puntaje. No sacrificar esto por pulido visual. |
| **14:15–14:45** | Pulido mobile + castellano en toda la UI. Deploy a URL pública. | Demo desde el **celular real**, o al menos viewport de teléfono. |
| **14:45–15:15** | Pantalla stretch de N03 (pre-completado de doc de exportación). **Cortar sin culpa si algo anterior está flojo.** | |
| **15:15–15:40** | **Ensayar la demo dos veces contra reloj.** Grabar video de respaldo. | Ver [[hackathon-demo-strategy]] para la estructura de 5 min. |
| **15:40–16:00** | Buffer. No tocar código. | |

### Reglas de riesgo

- **Nada crítico dependiendo del wifi del venue.** La voz vía Web Speech API es del navegador (no necesita key); el LLM sí necesita red → tener fallback local pre-cargado (patrón POLPILOT: audio de muestra matcheado por hash → transcripción canónica) y **video de respaldo grabado**.
- **⚠️ Render queda descartado del camino de demo en tier gratuito**: los servicios free se apagan tras 15 min de inactividad y tardan ~1 min en despertar → **va a estar frío justo cuando el jurado haga clic**. Con los US$100 de crédito del evento se puede usar un tier pago (que no duerme), pero verificar eso explícitamente. Si hay duda, **Netlify** (créditos del evento) es la apuesta segura.
- **Netlify AI Gateway elimina la API key del código**: Netlify inyecta `ANTHROPIC_API_KEY` / `ANTHROPIC_BASE_URL` como env vars y los créditos pagan el uso → `new Anthropic()` sin argumentos funciona. **Pero requiere un deploy a producción previo para activarse** → hacer un deploy hello-world en los primeros minutos, no a las 14:30.
- **Backup de red: `cloudflared tunnel --url`** — sin cuenta, ~30 segundos, sale sólo por 443 (sobrevive wifi hostil con aislamiento de clientes). Muy superior a `vite --host` (el aislamiento AP/cliente del wifi del venue hace que nadie alcance la IP de LAN) y a ngrok free (la página intersticial de advertencia queda delante de todo el HTML — inaceptable frente a un jurado).
- **Castellano en toda la UI.** Los usuarios finales son operarios argentinos. UI en inglés le resta credibilidad al pitch.
- **Sembrar el vocabulario del STT** con la lista de [[papa-semilla-modelo-de-datos]] (subcategorías, variedades, ubicaciones, jerga) antes de tener el diccionario real de Papasud.

---

## Para preparar esta noche

- [ ] `ANTHROPIC_API_KEY` en el `.env` del repo nuevo, verificada con una llamada real
- [ ] Postgres andando (local o Render con los US$100 de crédito) + `scripts/migrate.mjs` corriendo en verde
- [ ] Repo nuevo inicializado desde el boilerplate, **con commit inicial honesto** que diga qué se reutilizó
- [ ] Transcribir el esquema de [[papa-semilla-modelo-de-datos]] a una migración (es lo único diseñable de antemano)
- [ ] Probar `WebSpeechDictationAdapter` en `es-AR` en el celular que se va a usar para la demo
- [ ] Cuenta de **Netlify** lista + créditos del evento reclamados (formulario en el Luma). Verificar si el crédito de Render evita el spin-down de 15 min antes de contar con Render.
- [ ] `cloudflared` instalado y probado (`cloudflared tunnel --url http://localhost:3000`) como plan B de red
- [ ] Si se quiere fallback offline real: `ollama pull` del modelo **esta noche** (no se puede descargar sin wifi mañana)

---

## Tres cosas para no decir en la sala

De [[papasud-company-research]] — errores fácticos que costarían credibilidad frente al sponsor:

1. **Juan Pérsico falleció** (homenajeado post mortem por FENAPP). Muchas fuentes online todavía lo describen en presente como presidente de APPASBA. Asumir que el interlocutor es **Leandro Pérsico** (4ª generación) o su equipo; no mencionarlo a Juan como activo.
2. **"140 años" no está respaldado.** La prensa dice "más de 120 años", desde **Giuseppe Pérsico**, de Capri, llegado en **1888**. Decir *"familia con más de 120 años en la papa, 4ª generación"*.
3. **La DJVE no aplica** a papa semilla — es instrumento de granos.

> **Corrección (investigación posterior, [[seed-potato-domain-reference]] §6.4):** en la primera versión de esta nota dije que *packing list* y *certificado de origen* eran "solo documentos comerciales". **Eso era demasiado cauto.** El trámite de INASE (Res. 56/18, vía TAD) **exige explícitamente "Factura y/o Packing List"**, y el **certificado de origen MERCOSUR** es un formulario estandarizado real que emite una Cámara de Comercio Exterior. Sí se pueden nombrar.
>
> El set documental verificado y completo es:
> - **INASE (Res. 56/18, vía TAD):** formulario de solicitud, nota de compromiso de no difusión (material fuera del Catálogo Nacional de Cultivares), **factura y/o packing list**, comprobante VEP, inscripción RNCyFS. Específico de papa: **Res. SAGyP 715/94**.
> - **SENASA (vía CERT-POV):** inscripción en el Registro de Operadores de Comercio Exterior (AFIP), solicitud de Certificado Fitosanitario, **AFIDI / permiso de importación del país destino**, copia del permiso de embarque, **copia del Certificado INASE para material de propagación**, documentación oficial de los requisitos de la ONPF importadora, comprobante de aranceles.
> - **Comercial:** factura comercial/proforma, packing list, **certificado de origen MERCOSUR**, conocimiento de embarque / CRT para flete terrestre a Brasil y Paraguay.
> - **ePhyto** es el canal oficial hacia Brasil desde el 04/08/2023.
> - Marco de equivalencias: **MERCOSUR/GMC Res. 29/22** (lote máximo a muestrear 200 t, tamaño de muestra para virus, métodos de laboratorio para nematodos, reconocimiento del análisis visual).

### Dos datos nuevos que conviene incorporar al pitch

- **La posición de Papasud se está erosionando.** Sobre la década 2013-2023 concentró el **82,2%** de las exportaciones, pero en **2023 Drakar S.R.L. saltó de 87 t a 1.113 t y se quedó con el 46,46% de ese año**. Ya no es un monopolio cómodo: hay un competidor creciendo rápido. Eso vuelve la eficiencia administrativa una ventaja competitiva, no un lujo.
- **Egipto pidió 5.000 t** (un solo cliente) e **Indonesia y Malasia también pidieron**, pero **SENASA no abrió esos mercados**. Demanda concreta y desatendida.

### Una feature extra que la investigación regala

**Tabla de equivalencia de categorías entre países.** Las tolerancias de categoría de Brasil **son distintas (más laxas) que las argentinas**, así que una *Certificada* argentina puede reofrecerse en Brasil bajo otro nombre de categoría — y **no hay criterios unificados**. La investigación lo marca como *"un problema de negocio genuinamente sin resolver"*. Encaja perfecto sobre el modelo de linaje: si el lote ya conoce su subcategoría, mapearla al equivalente del destino es un agregado chico y muy creíble.

Además, Brasil y Uruguay **exigen semilla lavada**, lo que sube el costo y el riesgo sanitario — Canadá y la UE no. Y los análisis que exige el AFIDI **se repiten en destino**, reteniendo la semilla del comprador **20 a 30 días** antes de poder plantarla.

Y un dato que sí conviene usar, porque demuestra que se investigó: **PepsiCo apunta a que el 100% de su papa semilla en Brasil sea local para 2028.** El canal que le abrió Vietnam y Brasil a Papasud tiene vencimiento anunciado → diversificar destinos es prioridad, y **cada destino nuevo es un pliego documental nuevo**. Un sistema que les deje abrir el próximo país sin contratar a nadie habla el idioma de su problema real.
