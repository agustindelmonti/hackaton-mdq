# POLPILOT × Papasud — Cursor Hackathon Mar del Plata

**Evento:** sábado 22 de agosto de 2026, 10:00–16:00, Line Up Coworking, Playa Grande, Mar del Plata.
**Formato:** ~3 h de building, demo obligatoria de **5 minutos**, ganador elegido en sala.
**Premio:** $1.000.000 ARS, puesto por **Papasud** (el sponsor también escribió los desafíos).

Toda la investigación previa está en `docs/`. Empezar por `docs/hackathon-recomendacion-final.md` y `docs/papasud-features-y-flows.md`.

---

## Objetivo

Construir **"una sola verdad"**: un sistema de stock y cadena de custodia para las 4 ubicaciones de Papasud, con **carga de movimientos por voz en castellano** y **bloqueo de despacho ante discrepancias reales**, sobre un modelo de datos de **linaje** (no de inventario).

**Desafío elegido:** Vertical 03 (stock, trazabilidad y compliance), niveles **N01 + N02** completos. N03 (documentación de exportación) sólo como pantalla de cierre, no como módulo.

### Por qué este y no el copiloto sobre el Excel

La Vertical 01 se lleva un 50-70 % de los equipos: es el demo más reconocible y el que sale más rápido con cualquier boilerplate de chat. También es el que más depende de que el Excel que Papasud entregue a las 10 esté limpio. La Vertical 03 se puede sembrar con datos sintéticos creíbles, tiene tres validaciones demostrables en vivo, y es el dolor que el brief describe con más bronca.

---

## La idea de producto en una frase

> Los "4 lugares físicos" del brief no son 4 depósitos: son el **final de una cadena de custodia de 3 a 7 años que cruza 1.800 km y dos provincias**. Un lote no es una fila de stock — es un nodo en un árbol genealógico fiscalizado. El conflicto de versiones en la planilla es la punta de un problema de trazabilidad.

**Frase para la demo:** *"el problema de la planilla no lo resuelve la IA — lo resuelve el modelo de datos. La IA resuelve la captura."*

---

## Reglas de arquitectura (no negociables)

1. **Núcleo determinístico + narración del LLM.** Todos los números salen de código Python/TS plano que computa sobre la base. **El LLM nunca calcula, nunca recuerda un número, nunca lo reformatea.** Recibe strings ya formateados y los copia verbatim.
2. **Stock es una vista derivada de un libro append-only de movimientos.** Nunca una celda editable. Esto es lo que elimina el conflicto de versiones.
3. **El LLM extrae lenguaje; una capa determinística resuelve identificadores.** Fuzzy-match contra el catálogo real, candidatos ranqueados. El modelo **nunca** elige un lote o un insumo solo.
4. **Nada persiste sin confirmación humana.** Una nota de voz usa el mismo camino de inserción que la carga manual — un solo riel, no dos.
5. **Nunca inventar un dato no dicho.** Cantidad ausente → `null` + `confianza: 'dudosa'`. Preguntar, no asumir.
6. **Tools tipadas fijas, no SQL libre.** Set acotado con schema estricto (`tool_choice` forzado). Imposible de romper por inyección, cero riesgo de número inventado.
7. **Offline-tolerante.** Frigoríficos y lotes no tienen señal. Cola de sincronización con badges de estado.

---

## UI

- **Castellano rioplatense en toda la interfaz.** Los usuarios son operarios argentinos. Una UI en inglés le resta credibilidad al pitch.
- **Mobile-first.** El usuario está con el celular en la mano dentro de una cámara a 4 °C, con guantes. Targets ≥44 px, controles en la zona del pulgar, nav fija abajo.
- **El color codifica estado epistémico, no decoración:**

| Estado | Color | Significado |
|---|---|---|
| `inferido` | azul acero | la máquina lo escuchó o lo dedujo |
| `confirmado` | verde brote | una persona lo validó |
| `dudoso` | ámbar ocre | la máquina duda y pregunta |
| `error` | rojo ladrillo | discrepancia real, sync fallida |

Narrable en una frase: *"el azul es lo que la IA cree, el verde es lo que una persona confirmó, el ámbar es lo que está preguntando"*. Es la decisión de diseño de mayor apalancamiento del proyecto.

- **Números con `tabular-nums`.** Tablero de las 4 ubicaciones con números grandes, sin gráficos.

---

## Dominio: lo que hay que saber para no escribir código incorrecto

### Categorías y linaje

- **Básica:** Preinicial 0 · Preinicial I · Preinicial II · Inicial I · Inicial II · Inicial III · Fundación
- **Certificada:** Registrada · Certificada A · Certificada B

**Regla de linaje:** todo lote desciende de una subcategoría **igual o superior** a la propia. Implementar esta regla como validación.

⚠️ **Las fuentes se contradicen** sobre qué norma rige (Res. INASE **245/98** vs **171/2000**) y sobre la cola de la escalera. **Mostrar la regla, NO un número de artículo**, hasta confirmarlo con Papasud en los primeros 20 minutos.

**Papasud vende G3** (tercera generación) — su diferencial comercial declarado. Etiquetar `Categoría: Certificada – Registrada · Generación: G3`.

### Merma (esto es lo que vuelve creíble el motor de discrepancias)

La papa **pierde peso en el frigorífico** por respiración y deshidratación: es **merma legítima, no un error**. Y **no es lineal** — el **55-70 % de la pérdida de la temporada ocurre en los primeros 30 días**.

→ La validación no es `declarado vs contado` sino **`declarado − merma esperada vs contado`**, clasificando `dentro_de_merma` / `excede_merma`. **El LLM sólo redacta hipótesis cuando excede.**

**Frase de la demo:** *"no te aviso cuando la papa pierde peso; te aviso cuando pierde más peso del que debería"*.

La normativa **admite cantidad indeterminable** para productos primarios → `kg estimado, pendiente de pesaje` es un estado **legítimo en ámbar**, no un error en rojo.

### Unidades

- **Un bolsón son ~700 kg** (la densidad de la papa lo topea muy por debajo de la capacidad nominal). **NO 1.000 ni 1.250.** Sembrar con 700 para que la aritmética cierre: "20 bolsones" = 14 t.
- Envase rotulado: **≤50 kg** (campo) / **≤20 kg** (Preiniciales).

### Cosas que delatan — NO usar

| ❌ No decir | ✅ Correcto |
|---|---|
| Carta de Porte / CTG | **DTV-e** (SENASA) + **COT de ARBA** desde 4.500 kg |
| DJVE | No aplica a papa semilla (es de granos y oleaginosas) |
| "prebásica / básica / registrada / certificada" | La escalera real de arriba (es el escalón genérico de cereales) |
| Bolsón de 1.000 kg | ~700 kg |
| "140 años de empresa" | "familia con más de 120 años en la papa, 4ª generación" |

Y **Juan Pérsico falleció** — el interlocutor es **Leandro Pérsico** (4ª gen). Muchas fuentes online todavía lo describen en presente.

---

## Modelo de datos

Esquema completo y listo para transcribir en **`docs/papa-semilla-modelo-de-datos.md`**. Entidades:

- `variedad` — con `obtentor` y `licencia` (Papasud importa el 93,2 % de la semilla del país; el régimen de derechos sobre Innovator/HZPC está en disputa). **La variedad es una entidad, no un string en una celda.**
- `ubicacion` — tipo (`frigorifico` / `galpon` / `campo` / `laboratorio`), localidad, provincia, `geom`
- `lote` — **con `lote_padre_id`**. El linaje es el modelo.
- `movimiento` — append-only, con `fuente` (`voz`/`texto`/`conteo`), `transcripcion` guardada para auditoría, `confianza`, `confirmado_por`
- `conteo` — separado de los movimientos, para que la discrepancia sea computable
- `merma_curva` — curva no lineal por días de almacenamiento
- `stock` — **VIEW** derivada, no tabla

---

## Las tres validaciones que ganan la demo

Cada una es imposible en una planilla compartida:

1. **Stock insuficiente** — emitir remito por 500 kg con saldo de 480 → **bloqueo**, mostrando los movimientos que componen el saldo (no un error genérico: la evidencia).
2. **Linaje inválido** — lote `inicial_I` con padre de categoría inferior → **rechazo por regla de linaje INASE**, explicada en la UI. *Ningún otro equipo va a validar la genealogía fiscalizada de un lote.*
3. **Discrepancia neta de merma** — clasificar `dentro_de_merma` / `excede_merma`, y sólo en el segundo caso dejar que el LLM redacte la hipótesis **sobre la lista acotada** de movimientos candidatos.

**El momento de credibilidad:** mostrar **a propósito** que el sistema se frena (*"no reconozco este insumo, elegí de la lista"*, *"hay una discrepancia, no puedo emitir el remito"*). Papasud vive de la confianza de sus clientes; un sistema que se sabe frenar les habla directo. Para un jurado no técnico esto pesa más que un feature extra.

---

## Reutilización de código

Este repo parte de boilerplate propio, y **eso se declara abiertamente**. La versión honesta es más fuerte en la sala: *"vinimos con nuestro andamiaje —loop de tools, dictado es-AR, runner de migraciones— y usamos el día para construir el dominio de Papasud encima"*. Los jurados desconfían de un producto sospechosamente terminado y premian un día de trabajo visible y bien acotado.

Qué se levanta de dónde (detalle en `docs/polfin-reusable-assets.md` y `docs/polpilot-reusable-assets.md`):

- **`WebSpeechDictationAdapter` a `es-AR`** — voz del navegador, gratis, sin API key, sin backend
- **Loop agéntico de tool-use** con manejo de rate-limit y degradación elegante
- **Tools presentacionales** que devuelven `{ok:true}` con los datos en los args → React renderiza desde `props.args`. Cero riesgo de alucinación numérica.
- **`tool-call.tsx`** — el disclosure colapsable request/result **es** la UI de cita de fuente
- **`scripts/migrate.mjs`** — runner de migraciones `pg` standalone
- **`voz.py` / `transcripcion.py`** de POLPILOT — pipeline de voz con fallback por hash de audio

⚠️ **NO usar `clone-for-hackathon.sh`** (existe en polfin). Reescribe los timestamps de todos los commits para que la historia parezca creada durante el evento. No lo necesitamos y no es lo que queremos hacer.

---

## Infra

- **Deploy: Netlify.** Su **AI Gateway inyecta `ANTHROPIC_API_KEY`** en cada Function en planes con crédito → no hace falta cuenta propia de Anthropic. **Pero requiere un deploy a producción para activarse** → hacer el hello-world en el minuto 10, no a las 14:30.
- ⚠️ **Render queda fuera del camino de demo en free tier**: se apaga tras 15 min de inactividad con ~1 min de arranque en frío → va a estar frío justo cuando el jurado haga clic.
- **Plan B de red: `cloudflared tunnel --url`** — sin cuenta, ~30 s, sale sólo por 443 (sobrevive wifi con aislamiento de clientes). Superior a `vite --host` (el aislamiento AP/cliente lo vuelve inalcanzable) y a ngrok free (página intersticial delante del HTML).
- **Wispr Flow no tiene API usable** (sólo enterprise): es con lo que uno le dicta a Cursor, no un componente. La voz de la app es **Web Speech API**.
- **Nada crítico dependiendo del wifi del venue.** Fallback local pre-cargado y **video de respaldo grabado**.

---

## Orden de construcción

Por valor de demo por minuto. **Cortar desde abajo.**

1. **Tokens de color** — 10 min, y todo lo demás lo hereda
2. **Migraciones + seed** con datos creíbles (bolsones de 700 kg, ~150 lotes, 4 ubicaciones)
3. **Tarjeta de confirmación de campos parseados** — la pantalla más distintiva
4. **Botón de voz con barras de amplitud reales** (audio real, no animación falsa)
5. **Marco de teléfono** — 5 min, cambia cómo se lee todo en el proyector
6. **Vista única de las 4 ubicaciones** + drill-down a movimientos
7. **Las tres validaciones** ← acá está el puntaje, no sacrificarlas por pulido
8. **Badges de sync + toggle offline** — 15 min para el beat más memorable
9. Chips de pregunta aclaratoria
10. Pantalla de cierre de documentación de exportación

**Principios de scope:** esqueleto vergonzoso pero **desplegado y andando de punta a punta en los primeros 45 min**. **Congelamiento de código en los últimos 45** — sólo pulido, seed y ensayo. Ninguna feature nueva después de las 15:00.

**Escribir el guion de la demo ANTES del código.** El guion define qué features hacen falta; al revés se construye lo que no entra en 5 minutos.

---

## Coreografía de la demo (5 min)

1. **0:00-0:45** — El dolor, citando el brief textualmente: *"las diferencias entre lo que dice la planilla y lo que hay en la realidad suelen descubrirse recién al momento de entregarle el pedido a un cliente"*. Que la gente de Papasud asienta en el segundo 30.
2. **0:45-1:15** — El "antes": la planilla, el proceso manual. Concreto e incómodo.
3. **1:15-3:45** — Demo en vivo, **un solo flujo de punta a punta**: dictar un movimiento → señalar la transcripción y el lote resuelto → responder la pregunta en ámbar con un toque → **Confirmar** → activar modo avión, dictar otro, reconectar y dejar que los badges caigan en cascada a verde → abrir la alerta de discrepancia, leer la hipótesis, tocar "Ver en Galpón 2".
4. **3:45-4:30** — El momento de credibilidad: mostrar el sistema frenándose.
5. **4:30-5:00** — Qué sigue, y cerrar con la frase del color epistémico.

**Ensayar dos veces contra reloj. Demo desde el celular real.**

---

## Verificar con Papasud en los primeros 20 minutos

- **La escalera exacta de categorías** y qué norma la rige — antes de mostrar cualquier cita
- Confirmar que venden **G3** y cómo lo etiquetan internamente
- **Qué variedades trabajan realmente** (la investigación NO lo pudo confirmar; Innovator/Atlantic es inferencia por el vínculo con PepsiCo — no afirmarlo en la demo)
- Cuánto es un bolsón **para ellos**
- Si tienen curva de merma propia, o un porcentaje que usen de regla
- Cómo nombran las 4 ubicaciones en el día a día
- Las ~200 ha y 7.500 t del brief **no se pudieron verificar públicamente** — usarlas como dato que ellos dieron

---

## Índice de `docs/`

| Archivo | Qué tiene |
|---|---|
| `hackathon-recomendacion-final.md` | **Empezar acá.** Decisión, plan hora por hora, reglas de riesgo |
| `papasud-features-y-flows.md` | 38 features, 20 casos de uso, 9 flows detallados, priorización |
| `papa-semilla-modelo-de-datos.md` | Esquema SQL listo, curva de merma, vocabulario para el STT |
| `hackathon-demo-strategy.md` | Qué gana este hackathon en particular |
| `papasud-company-research.md` | La empresa: familia, escala, mercados, crisis 2025, regulación |
| `seed-potato-domain-reference.md` | Dominio agronómico: ciclo, variedades, plagas, certificación |
| `argentina-stock-documentation-reference.md` | Documentos de stock y tránsito argentinos (DTV-e, COT, remitos) |
| `hackathon-technical-feasibility.md` | Stack recomendado por sub-desafío, checklist de API keys |
| `voice-first-mobile-ux-design.md` | Spec de UX de voz, patrones industriales, sketches shadcn |
| `agtech-landscape-and-positioning.md` | Competencia agtech, el "Excel gap", ideas de UX |
| `hackathon-winning-strategy.md` | Psicología del jurado, control de scope, qué fakear |
| `polfin-reusable-assets.md` / `polpilot-reusable-assets.md` | Qué código levantar y de dónde |
| `cursor-hackathon-mar-del-plata-2026.md` | Logística del evento, sponsors, créditos |
| `papasud.md` | Notas originales del brief (previas a la investigación) |
