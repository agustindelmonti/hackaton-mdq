---
tags: [architecture, post-hackathon, supabase, reconciliation, confidence]
date: 2026-08-23
---

# Motor de inferencia y confianza para conciliación de stock

De la hackathon al sistema real: cómo la "confianza" que hoy es un string fijo
(`"alta"` / `"media"` / `"baja"`) en `backend/core/conciliacion.py` se convierte
en un número calculado, auditable y que mejora con el tiempo.

Complementa [[papa-semilla-modelo-de-datos]] (el esquema de dominio) y el
código vivo en `backend/core/conciliacion.py` / `backend/core/anomalias.py`
(el prototipo de la hackathon, que sigue funcionando sobre el store JSON).

---

## El problema que esto resuelve

La pantalla de conciliación no solo señala una diferencia entre lo declarado
y lo contado: propone una **hipótesis de causa** y una **confianza** sobre esa
hipótesis. Durante la hackathon eso se resolvió con una cascada de reglas
determinísticas (`conciliacion.hipotesis()`) que es rápida, auditable y
honesta — pero la confianza que devuelve cada regla es una constante escrita
a mano en el código, no algo medido contra la realidad.

Dos preguntas distintas se estaban resolviendo con el mismo mecanismo:

1. **¿Esta causa es la correcta?** — es un problema de calibración: necesita
   casos históricos resueltos para saber qué tan seguido acierta cada regla.
2. **¿Esta anomalía es estadísticamente significativa?** — el caso de la
   merma, que sí se puede resolver con una prueba estadística real (varianza
   de la curva de merma) sin esperar ningún historial.

Este documento separa ambas y define un modelo de datos y una arquitectura
de tres niveles para resolverlas de verdad.

---

## Arquitectura: tres niveles, escalando por costo y por confianza

Cada diferencia entra por el Nivel 0. Sólo sube de nivel si el anterior no
llega a un umbral de confianza suficiente. Nunca al revés: no se le pregunta
al agente algo que ya resuelve una regla determinística.

```
diferencia detectada
        │
        ▼
┌─────────────────────┐   confianza suficiente?  ──sí──▶  se muestra,
│ Nivel 0 · Reglas     │                                    queda logueada
│ determinísticas      │
│ (conciliacion.py)    │
└─────────┬────────────┘
          │ no / empate entre candidatos
          ▼
┌─────────────────────┐   confianza suficiente?  ──sí──▶  se muestra,
│ Nivel 1 · Estadística │                                   queda logueada
│ sobre outcomes        │
│ (diff_resolutions,    │
│  rule_confidence_stats,│
│  z-score de merma)    │
└─────────┬────────────┘
          │ no / no hay volumen suficiente todavía
          ▼
┌─────────────────────┐   (opcional, con volumen)
│ Nivel 2 · Ranker      │
│ liviano sobre         │
│ candidatos empatados  │
└─────────┬────────────┘
          │
          ▼
┌─────────────────────┐
│ Nivel 3 · Agente      │  siempre ámbar, nunca persiste
│ (LLM sobre evidencia  │  sin confirmación humana
│  acotada)             │
└──────────────────────┘
```

El costo y la latencia crecen en cada nivel (microsegundos → milisegundos →
segundos y USD). La confiabilidad narrable ante una auditoría baja en cada
nivel: "esto lo dice un movimiento registrado" pesa más que "esto lo dice un
modelo". El agente debe resolver la cola larga, no el caso común.

### Nivel 0 — Reglas determinísticas (ya existe)

`conciliacion.hipotesis()` tal cual está hoy: movimiento sin confirmar, cero
de más/menos, nota con testigo, tara de bolsón. No cambia — es rápido, cero
costo, cien por ciento auditable. Lo único que cambia es que su salida deja
de traer una confianza fija: trae un `rule_key` (`unconfirmed_transfer`,
`digit_entry_error`, `physical_shrinkage_witnessed`, `bag_tare`) que el
Nivel 1 usa para buscar la confianza medida.

### Nivel 1 — Estadística sobre datos concretos y trackeables

Esto es lo que hoy no existe y es donde está la mayor parte del valor. Dos
mecanismos, cada uno resolviendo una de las dos preguntas de arriba:

**a) Precisión empírica por regla.** Cada vez que una diferencia se cierra —
un traslado se confirma en destino, un movimiento se corrige, una merma se
da de baja, un recuento manual cierra la cámara — se guarda una fila en
`diff_resolutions`: qué hipótesis se había propuesto y si resultó correcta.
Con eso, la confianza de una regla deja de ser una constante y pasa a ser
"de las veces que esta regla disparó, ¿qué porcentaje se confirmó cierto?".

No se usa la proporción cruda (`n_correct / n`): con pocos casos eso hace
que "2 de 2 aciertos" se muestre como 100% de confianza, que es una mentira
estadística. Se usa el **intervalo de Wilson** (95%, `z = 1.96`), calculado
en SQL plano dentro de la vista `rule_confidence_stats` — no hay ningún
paso de LLM ni de ML acá, es aritmética sobre conteos.

**b) z-score contra la curva de merma.** En vez de un umbral fijo
(`declarado − merma_esperada vs contado`, con un ±1% arbitrario como en el
prototipo), se usa la varianza histórica real de la merma por bucket de días
de almacenamiento (`shrinkage_curve.stddev_pct`). La vista
`shrinkage_discrepancies` calcula:

```
z = (contado − declarado × (1 − merma_esperada))
    / (declarado × desvío_estándar_merma)
```

`|z| ≥ 2` clasifica como `excede_merma` — un umbral con significado
estadístico (≈95% de que la diferencia no es variación normal de merma), no
un número inventado. La confianza que se narra es directamente ese z-score
o su p-value asociado.

### Nivel 2 — Ranker liviano (opcional, para más adelante)

Cuando `diff_resolutions` acumule volumen (cientos de casos), un modelo
simple (logística o gradient boosting sobre features interpretables: % de
diferencia, días desde el movimiento, operario, temporada) puede reordenar
mejor que reglas fijas cuando dos candidatos empatan. Nunca genera
candidatos nuevos — sólo rankea los que el Nivel 0 ya encontró por búsqueda
determinística, así que sigue siendo auditable: cada feature es explicable.
No hace falta implementarlo ahora; el modelo de datos de este documento ya
deja el camino libre (los mismos `diff_resolutions` son el dataset de
entrenamiento).

### Nivel 3 — Agente, sólo para el residuo `sin_explicacion`

Cuando ningún nivel anterior encuentra nada, un agente lee evidencia acotada
(notas recientes de esa cámara, patrones de otros lotes de la misma
variedad) y arma una hipótesis en lenguaje natural. Reglas no negociables,
heredadas de la arquitectura de la hackathon (regla 1 y 4 de `CLAUDE.md`):

- El agente **no calcula ni inventa un número** — narra sobre datos que el
  código ya resolvió y le pasó formateados.
- Sale marcado `tier = 3` en la UI, confianza siempre tope ámbar, nunca
  verde.
- **No se guarda como outcome de entrenamiento hasta que una persona lo
  confirme.** La tabla `agent_hypotheses` guarda la propuesta separada de
  `diff_resolutions.outcome`, que arranca en `pending`.
- Si se confirma, ahí sí entra al pool de datos del Nivel 1 —
  `agent_hypotheses.promoted_to_rule` es el flag que marca cuándo un patrón
  que hoy resuelve el agente se volvió lo bastante frecuente como para
  escribirse como regla de Nivel 0.

---

## Modelo de datos

Ver el detalle completo en las migraciones (`supabase/migrations/`). Resumen
de las tablas nuevas:

| Tabla | Para qué |
|---|---|
| `hypothesis_rules` | Registro de qué reglas existen y en qué nivel viven — así las consultas de confianza no hardcodean la lista en el código de la app. |
| `diff_resolutions` | El log de outcomes. Una fila por diferencia cerrada: qué se propuso, qué nivel la propuso, qué evidencia tenía, si se confirmó correcta. Es el dataset del que sale toda confianza medida. |
| `agent_hypotheses` | Sólo Nivel 3: contexto extra que necesita una propuesta de agente (modelo usado, payload de evidencia, respuesta cruda) sin ensuciar las filas de niveles 0-2. |
| `rule_confidence_stats` | Vista: intervalo de Wilson por regla, calculado en vivo desde `diff_resolutions`. |
| `shrinkage_curve` (con `stddev_pct`) / `shrinkage_discrepancies` | La curva de merma con desvío estándar, y la vista que calcula el z-score. |

El resto de las tablas de las migraciones (`varieties`, `locations`, `lots`,
`movements`, `counts`, …) son el esquema de dominio de
[[papa-semilla-modelo-de-datos]], necesario porque hoy no existe ninguna
base Postgres real — el prototipo de la hackathon corre sobre un store JSON
(`backend/core/store.py`). Se migran acá con **nombres en inglés** (la
convención de este documento y de las migraciones), aunque el backend
Python de la hackathon siga usando los nombres en castellano
(`declarado_kg`, `ubicacion_id`, etc.) — la tabla de equivalencia está al
final de este documento para cuando se porte esa lógica.

---

## Flujo de ejemplo, de punta a punta

1. Se cierra una cámara: `counts` recibe un `counted_kg` para el lote `L-042`
   en `cold-dospanca`, junto con `declared_kg = 18.000` — la foto de lo que
   decía el libro de movimientos justo antes de contar (no un cálculo en
   vivo: si fuera un join contra `stock`, una corrección posterior del
   libro borraría silenciosamente la discrepancia que ese conteo expuso).
   Contaron 17.400.
2. `conciliacion.hipotesis()` (Nivel 0) busca un movimiento `en_transito` de
   ese lote saliendo de esa ubicación por ~600 kg. Lo encuentra: dispara
   `rule_key = 'unconfirmed_transfer'`.
3. Antes de mostrarlo, la app consulta `rule_confidence_stats` para
   `unconfirmed_transfer`: "11 de 13 casos anteriores se confirmaron
   correctos, intervalo de Wilson 95% = [0.56, 0.93]". Esa confianza medida
   — no la palabra "alta" — es lo que se muestra.
4. Un operario va, confirma que los bolsones efectivamente estaban en
   destino sin registrar. Se llama `confirmar_en_destino()` (ya existe en
   `movimientos.py`) y **además** se inserta la fila en `diff_resolutions`
   con `outcome = 'confirmed_correct'`.
5. La próxima vez que `unconfirmed_transfer` dispare, el intervalo de Wilson
   ya tiene un caso más — la confianza mostrada mejora sola, sin tocar
   código.

Para el caso `sin_explicacion` que escala a Nivel 3, el mismo cierre humano
(sea "sí, era esto" o "no, la causa real fue otra") completa
`diff_resolutions.outcome` y decide si esa hipótesis de agente eventualmente
se convierte en regla.

---

## Qué se entrega en este commit

- `supabase/migrations/20260823120000_core_domain_schema.sql` — esquema base
  (variedades, ubicaciones, lotes con linaje, movimientos, conteos, curva de
  merma, vista `stock`), traducido a inglés desde
  [[papa-semilla-modelo-de-datos]].
- `supabase/migrations/20260823120100_reconciliation_inference.sql` — el
  motor de este documento: `hypothesis_rules`, `diff_resolutions`,
  `agent_hypotheses`, la vista `rule_confidence_stats` (Wilson) y la vista
  `shrinkage_discrepancies` (z-score).
- `supabase/seed.sql` — datos de ejemplo: dos lotes con su cadena de
  movimientos, una diferencia de conteo, y sobre todo **casos históricos ya
  resueltos** en `diff_resolutions` para que `rule_confidence_stats` muestre
  números reales (no una tabla vacía) al correr el seed.

## Qué falta (fuera de alcance de este commit)

- Portar `backend/core/conciliacion.py` para que consulte
  `rule_confidence_stats` en vez de devolver el string fijo, y para que
  escriba en `diff_resolutions` cuando algo se cierra. Hoy el prototipo
  sigue sobre el store JSON; conectarlo a Postgres es el siguiente paso.
  concreto.
- El endpoint de "cerrar diferencia" — hoy `conciliacion.py` genera la
  hipótesis pero no hay dónde un operario confirme "sí, era esto", que es el
  prerequisito para que `diff_resolutions` reciba datos reales.
- Nivel 2 (ranker) — no tiene sentido implementarlo hasta tener volumen real
  en `diff_resolutions`.
- Políticas RLS de producción — las migraciones no las definen todavía; el
  acceso hoy se asume vía service role desde el backend, no desde el
  cliente directamente.

## Equivalencia de nombres (inglés Supabase ↔ castellano del prototipo)

| Supabase (inglés) | Prototipo JSON (castellano) |
|---|---|
| `lots.id` | `lote` / `codigo` |
| `locations.id` | `ubicacion_id` |
| `movements.kg` | `kg` (`movimientos.py`) |
| `counts.counted_kg` | `conteos.fisico_kg` |
| `counts.declared_kg` | `conteos.declarado_kg` |
| `counts.declared_kg − counts.counted_kg` | `diferencia_kg` en `conciliacion.diferencias()` |
| `diff_resolutions.rule_key` | `hipotesis()["clase"]` |
| `diff_resolutions.proposed_confidence` | `hipotesis()["confianza"]` (hoy string fijo) |
