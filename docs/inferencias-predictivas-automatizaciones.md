---
tags: [architecture, post-hackathon, predictive, recommendations, automation, insights]
date: 2026-08-23
---

# Inferencias predictivas, recomendaciones y automatizaciones

Catálogo de lo que se puede construir además del motor de conciliación
([[motor-conciliacion-confianza]]) y de la skill `confidence-indicators` —
todo sobre datos determinísticos y auditables, nunca sobre un LLM
adivinando.

**Antes de leer esto: ya existe un motor bastante completo.** No es un
catálogo desde cero — es la extensión de tres módulos que YA hacen exactamente
este trabajo:

| Módulo | Qué hace hoy |
|---|---|
| `backend/core/oportunidades_neg.py` | 9 hallazgos cerrados, cada uno cruzando ≥2 fuentes, con `naturaleza` (`recuperable`/`accionable`/`riesgo`) para que la plata nunca se cuente dos veces: brotación inminente, ya brotado, kilos en tránsito sin confirmar, embarque frenado, diferencias abiertas, rótulos inconsistentes, análisis por vencer, galpón sin frío, concentración de exportación. |
| `backend/core/tareas.py` | `sugeridas()` cruza esas mismas señales y calcula A QUIÉN le toca cada una (por rol + ubicación, nunca hardcodeado); nada se ejecuta sin el OK de una persona. |
| `backend/core/objetivos_medidos.py` | 7 objetivos que Ángela mide sola contra el dato real (baseline → actual → meta), no metas escritas a mano. |
| `backend/core/anomalias.py` | Detectores sobre datos ya cargados: precio a pérdida, categoría perdida, trazabilidad incompleta, sin análisis, traslado huérfano, conteo sin cerrar, duplicado. |
| `backend/core/confidence.py` + `supabase/migrations/` | El motor de confianza de este sprint: reglas → estadística (Wilson) → agente, con el log de outcomes (`diff_resolutions`) como fuente de toda confianza medida. |

Todo lo de arriba es **reactivo** (mide el estado actual) o de **fecha
conocida** (brotación inminente ya sabe la fecha exacta). Lo que falta —y lo
que arma este documento— es lo que proyecta hacia adelante, rankea
alternativas, empuja en vez de esperar que alguien abra la pantalla, o mira
hacia atrás para decir qué tan confiable es cada pieza del sistema.

**Regla que no se negocia, la misma de todo el proyecto:** cada número sale
de código Python plano. El LLM narra sobre resultados ya calculados; nunca
proyecta, nunca rankea, nunca decide un umbral. Donde hace falta lenguaje
natural (explicar una hipótesis, redactar una recomendación), sigue el mismo
patrón en tres niveles de `motor-conciliacion-confianza.md` — reglas primero,
estadística después, agente sólo para el resto.

---

## Predictivo — proyectar hacia adelante, no sólo señalar lo que ya se sabe

### 1. Proyección de stock comprometido (⚙️ implementado en este commit)
`core/capacity_forecast.py` — cruza `conciliacion.por_ubicacion()` (kg y
`capacidad_kg` actuales) con el ritmo real de ingresos de los últimos N días
(`movimientos.listar()`) para proyectar la fecha de saturación de cada
ubicación, si el ritmo se mantiene. Hoy `objetivos_medidos` mide el hueco
actual (`ocupacion_pct`); esto proyecta cuándo deja de haber hueco.

### 2. Alerta temprana de merma (📋 diseñado, no implementado)
Usar el `stddev_pct` de `shrinkage_curve` (ya está en
`supabase/migrations/20260823120000_core_domain_schema.sql`) para marcar un
lote como "va camino a `excede_merma`" ANTES del próximo conteo formal —
una versión adelantada del z-score de `shrinkage_discrepancies`, corrida
sobre la tendencia de conteos parciales de un lote en vez de esperar el
conteo de cierre. **Por qué no se implementa ahora:** el prototipo JSON
(`backend/core/store.py`) todavía no tiene una curva de merma cargada ni
conteos con suficiente cadencia diaria como para tener una tendencia real —
implementarlo hoy sería simular datos que no existen. Se activa solo
cuando el motor de Supabase esté conectado y haya conteos seriados.

### 3. Vencimiento de análisis atado a compromiso real (⚙️ implementado)
Extiende la card `analisis_por_vencer` de `oportunidades_neg.py`: en vez de
"vence en N días" a secas, cruza contra `ordenes_carga` para decir "vence
ANTES de la fecha del embarque ya comprometido" — mismo dato, prioridad más
filosa porque ata el vencimiento a plata comprometida, no a un calendario
abstracto.

### 4. Agotamiento de capacidad
Ver ítem 1 — es la misma proyección, mirada desde el ángulo de "cuándo se
llena" en vez de "cuánto stock voy a tener".

---

## Recomendaciones — rankear alternativas reales, no sólo señalar el problema

### 5. Cola de recuento priorizada (⚙️ implementado)
`core/recount_priority.py` — rankea las diferencias abiertas de
`conciliacion.abiertas()` por `impacto_pesos × (1 − confianza) × días_abierta`
en vez de sólo por plata. Usa la fuerza de regla (`FUERZA_REGLA`, la misma
tabla que ya alimenta `ConfidenceIndicator` en el frontend) como proxy de
`confianza` hasta que `rule_confidence_stats` esté conectado — en ese
momento el único cambio es la fuente del número, no la fórmula.

### 6. Camino de reclasificación (📋 diseñado, no implementado)
`anomalias._categoria_perdida()` ya detecta el lote brotado con categoría
vieja — falta que recomiende la subcategoría válida según la escalera INASE
(`docs/papa-semilla-modelo-de-datos.md`), no sólo marcar el problema. Es
mecánico (buscar la subcategoría inmediatamente inferior en la escalera que
siga siendo válida como padre) pero toca la regla de linaje que
`CLAUDE.md` marca como "verificar con Papasud antes de mostrar en pantalla"
— se deja diseñado, no implementado, hasta confirmar la escalera exacta.

### 7. Reporte de confiabilidad de reglas (⚙️ implementado)
`core/rule_reliability.py` — muestra, para cada regla de
`conciliacion.hipotesis()`, su fuerza declarada hoy (`FUERZA_REGLA`) y
cuántas veces disparó en el período reciente, como preparación directa para
el día en que haya outcomes reales medidos (`diff_resolutions`). El campo
`calibrado: false` en cada fila es intencional: nunca se disfraza de
medición lo que todavía es juicio del oficio.

### 8. Rebalanceo entre cámaras (📋 diseñado, no implementado)
Cuando una ubicación proyecta agotamiento de capacidad (ítem 1) y otra tiene
lugar, recomendar qué lotes mover — sólo entre destinos válidos por linaje y
por tipo de ubicación. Depende de tener 1 y una noción de "distancia/costo
de traslado" entre ubicaciones que hoy no está modelada; queda para cuando
haya una segunda ubicación con headroom real en los datos sembrados.

---

## Automatizaciones proactivas — empujar, no esperar a que alguien mire la pantalla

### 9. Condiciones de recordatorio nuevas (📋 diseñado, no implementado)
`crear_recordatorio` (en `angela.py`) ya soporta condiciones como
`vencimiento_deposito`, `entrega_pendiente`, `dormido_supera`,
`cliente_atraso_dias`, `programado`. Sumar `capacidad_proxima` (dispara
desde el ítem 1) y `traslado_huerfano` (desde `anomalias._traslados_huerfanos`)
para que estas señales lleguen por la campanita en vez de requerir que
alguien abra Conciliación o Depósito. Es mecánico una vez que 1 esté en
producción — se deja para la siguiente pasada porque toca `recordatorios.py`
y el árbol de condiciones de `core/recordatorios.py`, que no se tocó en este
commit.

### 10. Auto-cierre de lo chico y confiable (📋 diseñado, no implementado)
Mismo patrón que ya existe para la tara de bolsón
(`conocimiento.umbral_tara_pct`, en `conciliacion.py`): si una regla tiene
confianza medida alta Y el impacto es chico, resolverla sola (logueada,
reversible), en vez de pedir un click por cada centavo. Depende de tener
outcomes reales (`diff_resolutions`) para que "confianza alta" sea medida y
no una etiqueta — se activa junto con el ítem 7 cuando deje de ser
`calibrado: false`.

### 11. Bloqueo real de compliance (📋 diseñado, no implementado)
`sin_analisis` / `trazabilidad_incompleta` (`anomalias.py`) hoy son
anomalías que se muestran. Convertirlas en bloqueo duro de
`movimientos.registrar()`/`ordenes_carga` cuando el destino es exportación
(`destino_presuntivo`) es una validación real, no sólo una alerta — pero
cambia el comportamiento de un flujo de escritura ya en producción
(`registrar_movimiento`), así que se documenta para decidirlo con el
producto antes de tocar ese camino sin avisar.

---

## Insights — analítica agregada hacia atrás

### 12. Reporte de confiabilidad de reglas
Ver ítem 7 — es el mismo módulo, mirado como insight en vez de como
recomendación de priorización.

### 13. Atribución de varianza de merma (📋 diseñado, no implementado)
Qué cámaras/operarios/temporadas producen más `excede_merma` del que
predice la curva — un insight real sobre `diff_resolutions` agregado. Mismo
bloqueo que el ítem 2: necesita el motor de Supabase conectado y volumen de
casos resueltos.

### 14. Score de trazabilidad por lote (📋 diseñado, no implementado)
% de la documentación INASE/SENASA requerida (`anomalias.CAMPOS_TRAZABILIDAD`)
presente, agregado por campaña o variedad — una extensión directa de
`_trazabilidad_incompleta()` a nivel agregado en vez de por lote.

---

## Qué se entrega en este commit

Implementado, con módulo + endpoint API + tool de Ángela, verificado contra
los datos reales de `data-papasud`:

- `core/capacity_forecast.py` — ítems 1 y 4.
- `core/recount_priority.py` — ítem 5.
- `core/rule_reliability.py` — ítems 7 y 12.
- Extensión de `oportunidades_neg._card_analisis()` — ítem 3.

Diseñado y documentado arriba, sin implementar todavía — cada uno dice por
qué: ítems 2, 6, 8, 9, 10, 11, 13, 14. La mayoría comparte un bloqueador
real: necesitan el motor de Supabase (`diff_resolutions`,
`rule_confidence_stats`, `shrinkage_curve` con volumen real) conectado para
dejar de ser una simulación. El resto (9, 11) toca código de escritura en
producción (recordatorios, bloqueo de despacho) que merece una decisión de
producto explícita antes de cambiar el comportamiento sin avisar.
