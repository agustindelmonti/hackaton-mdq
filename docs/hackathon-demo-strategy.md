---
tags: [reference, hackathon, strategy, pitch]
date: 2026-08-21
---

# Estrategia de demo y criterios de decisión — [[cursor-hackathon-mar-del-plata-2026]]

Nota complementaria: qué gana este hackathon en particular, dado quién juzga y cuánto tiempo hay.
Ver también [[papasud]], [[papasud-company-research]], [[hackathon-technical-feasibility]], [[polpilot-reusable-assets]], [[polfin-reusable-assets]].

## Las restricciones reales del formato

| Restricción | Implicancia directa |
|---|---|
| ~3 hs de building efectivo (10-16 hs con overhead) | El scope tiene que estar decidido **antes** de entrar. Nada de explorar opciones a las 10:00. |
| Demo de 5 min **obligatoria** | El tiempo de demo es el recurso más escaso, no el de código. Un feature que no se puede mostrar en 5 min no existe. |
| Ganador elegido **en sala** | Decisión emocional/inmediata, sin lectura posterior de código ni README. Lo que se ve en pantalla es el 100% de la evaluación. |
| Sin panel de jueces publicado | Muy probable: organizadores (Luigi Canoro, Franco Petruccelli) + gente de Cursor + **alguien de Papasud**. Mezcla de técnicos y no-técnicos. |
| Sponsor no-tech pagando $1M ARS | Papasud puso la plata. Hay un fuerte incentivo a premiar algo que **Papasud realmente querría usar el lunes**. |
| 102 registrados, cupo lleno | Muchos equipos → varios van a elegir lo mismo. La diferenciación importa. |

## Hipótesis central de estrategia

**El criterio de desempate más probable no es sofisticación técnica, sino: "¿esto le resuelve un problema real a Papasud, y se ve creíble?"**

Evidencia que sostiene esto:
- El brief de Papasud está escrito en lenguaje de negocio, no técnico ("es difícil de consultar", "se descubre recién al momento de entregarle el pedido a un cliente"). Describen **dolor**, no especificaciones.
- El brief define explícitamente que los niveles existen para que equipos de distinta experiencia tengan "una meta alcanzable en un día" — es decir, N03 **no** vale automáticamente más que N01. Un N01 impecable > un N03 a medio funcionar.
- La guía general de hackathones con jurado no-técnico es consistente: valor de negocio, claridad, UI/UX pulida, y minimizar jerga. La profundidad técnica es casi imposible de transmitir en 5 minutos.

**Corolario contraintuitivo pero importante:** ir al N03 "avanzado" es probablemente una trampa. Es donde está el mayor riesgo de que la demo falle en vivo (satélite = dependencia de API externa + wifi del venue; modelo predictivo = necesita datos de entrenamiento que recién se ven ese día y que probablemente sean insuficientes para un modelo honesto). Y si falla, no hay nada que mostrar.

## El patrón de demo que gana

Estructura de 5 min, cronometrada y ensayada dos veces:

1. **0:00-0:45 — El dolor, en las palabras de Papasud.** Citar el brief textualmente. "Las diferencias entre lo que dice la planilla y lo que hay en la realidad suelen descubrirse recién al momento de entregarle el pedido a un cliente." Que la gente de Papasud asienta con la cabeza en el segundo 30. Ese asentimiento es la mitad del premio.
2. **0:45-1:15 — El "antes".** Mostrar la planilla / el proceso manual. Concreto, visual, incómodo.
3. **1:15-3:45 — La demo en vivo, un solo flujo, de punta a punta.** Un caso, no cinco. Hablarle al micrófono en castellano, que aparezca el dato estructurado, que se guarde, que se vea reflejado. **El momento donde la voz se convierte en dato estructurado en pantalla es el "live moment"** — es lo que la gente recuerda.
4. **3:45-4:30 — El momento de credibilidad: mostrar que el sistema NO inventa.** Enseñar a propósito un caso donde el sistema dice "no reconozco este insumo, elegí de la lista" o "hay una discrepancia, no puedo emitir el remito". Para un jurado no-técnico esto es más impresionante que un feature extra, porque es lo que diferencia un juguete de algo que se puede usar en producción. Papasud vive de la confianza de sus clientes — un sistema que se sabe frenar les habla directo.
5. **4:30-5:00 — Qué sigue.** Una frase por vertical adyacente ("lo mismo aplica a órdenes de trabajo y a documentación de exportación"), y el costo/tiempo de ponerlo en producción. Cerrar con la sensación de que es el paso 1 de algo real, no un experimento.

## Reglas de riesgo para el día

- **Nada que dependa de wifi del venue en el camino crítico.** Si la demo necesita una API externa, tener un fallback local pre-cargado (el patrón de POLPILOT: audio de muestra matcheado por hash → transcripción canónica). Grabar además un video de respaldo de la demo funcionando.
- **Datos de Papasud llegan el mismo día, formato desconocido.** No construir nada que asuma un esquema específico. Construir el esqueleto (voz → extracción estructurada → DB → vista) y **mapear el esquema real recién cuando se vean los datos**. El brief admite que los assets todavía no están definidos.
- **Mobile-first, no desktop.** Dos de las tres verticales tienen usuarios con el celular en la mano (ingeniero en el lote, operario en el frigorífico). Una demo hecha en un navegador de escritorio maximizado le habla peor al jurado que una vista de teléfono. Demo desde el celular real, o al menos en viewport de teléfono.
- **Castellano en toda la UI.** Los usuarios finales son operarios argentinos. Una UI en inglés le resta credibilidad a la propuesta de "esto es para Papasud".
- **Escribir el guion de la demo ANTES de escribir código.** El guion define qué features hacen falta. Al revés se construyen cosas que no entran en 5 minutos.

## Cómo pondera esto la elección de vertical

Criterios de decisión, en orden de peso:

1. **¿Se puede demostrar el dolor y la solución en 5 min sin explicar nada técnico?**
2. **¿Funciona sin depender de datos que recién veo a las 10 am?** (favorece flujos de captura sobre flujos de análisis: capturar dato nuevo por voz no necesita el histórico; consultar el histórico sí lo necesita, y si el Excel viene sucio se pierde una hora limpiándolo)
3. **¿Cuánto riesgo de falla en vivo tiene?** (favorece stack local/simple sobre APIs externas)
4. **¿Cuán probable es que otros 20 equipos hagan lo mismo?** (el copiloto conversacional sobre el Excel es el más obvio y el más saturado — hay que asumir que muchos equipos van por ahí)
5. **¿Le habla al dolor que Papasud describió con más emoción?** (releyendo el brief, la descripción más visceral es la de stock: "nadie tiene una visión única y confiable", "se descubre recién al momento de entregarle el pedido a un cliente" — eso es plata perdida y un cliente enojado, y está redactado con más bronca que las otras dos)

## Nota sobre diferenciación

Predicción: la mayoría de equipos va a elegir **V1-N01 (copiloto conversacional sobre el Excel)** porque es el más reconocible, el más parecido a un demo de ChatGPT y el que sale más rápido con cualquier boilerplate de chat. Eso lo vuelve el terreno más competitivo y el que menos sorprende.

El diferencial está en elegir algo donde el **flujo operativo** sea el protagonista y la IA sea invisible pero indispensable — es decir, donde la IA reemplaza un paso manual que hoy le cuesta plata a Papasud, en vez de agregar un chat encima de datos que ya tienen.
