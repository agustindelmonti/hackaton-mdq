# Track B → Track A / Track C — el modelo real está definido

Rama `feat/modelo-real`. Esto es lo que ya pueden consumir.

## Qué cambió respecto al dataset viejo

El dataset viejo (`data-papasud/dominio.py` + `generar.py`, backend `core/store.py`
y todo lo que cuelga de `data_store.py`) sigue andando — **no lo tocamos, no lo
rompimos**. Es el modelo de "4 depósitos de semilla fiscalizada" que se pensó
antes de hablar con Papasud.

El modelo real vive **aparte**, en un namespace propio, para que ustedes puedan
migrar a su ritmo sin que nada se caiga en el medio:

- `data-papasud/dominio_real.py` — catálogos reales (variedades, campos
  incluyendo Cayetano Chávez, lotes, laboratorio in vitro, **planta con zonas**,
  tipos de vehículo/tolva, frigoríficos, clientes, transportistas, roles,
  Albor Agro como sistema a no reemplazar)
- `data-papasud/generar_real.py` — generador determinista del dataset real
  (correr con `python data-papasud/generar_real.py`)
- `backend/core/modelo_real.py` — loader + regla de linaje
- `backend/core/stock_real.py` — stock derivado + motor de bloqueo-con-alternativa
  + `detalle_planta` / `resumen_sitios`
- `backend/core/mapa_real.py` — grafo del flujo real (campo → planta ⇄ frío → cliente)
- `backend/core/inconsistencias_papasud.py` — detector de "arreglar el pasado"
- `backend/core/liquidacion.py` — kg movidos y $ a pagar por transportista/frigorífico
- `backend/core/importer_papasud.py` — importador tolerante de la planilla real
  de 12 solapas (no la tenemos en el repo todavía — el importador está escrito
  contra las columnas documentadas en PLAN_TRACKS_PAPASUD.md y testeado con
  planillas sintéticas equivalentes; falta validarlo contra el .xlsx real de
  Papasud cuando lo tengamos)

## El modelo

**Campo → Pivote (A, B) → Cuadrante (1-8) → Lote.** Cada lote tiene una sola
variedad (regla dura, validada al cargar — `modelo_real.validar_regla_linaje`).

**Flujo real:** `lote (campo) → planta → cliente`, con el circuito
`planta → frigorífico → vuelve a planta → cliente` como el más común. En el
medio viven entidades de verdad: **orden de carga** (papel, a veces sin señal /
sin remito), **tolva**, **planilla de recepción con báscula**, **reclasificación**
(granel con tierra → bolsas). Atajos reales: campo→frío y campo→cliente.
Ver `docs/cadena-planta-papasud.md`. Todo queda en un libro de movimientos
**append-only** (`movimientos_real.json`): el stock es SIEMPRE la suma de ese
libro, nunca una celda editable.

Datos reales usados (nada inventado): variedades `agata, spunta, asterix,
king_russet` · campos `santa_ana, marisol, trevelin, oriente` · lotes
`L30..L79` + `14, 18, 222, 223, 224, 241, 300, 810, 811, 910` · frigoríficos
`dospanca, galpon_mdp, pancani, sasula` · clientes `wemar_mc_cain, parmentier`
· 8 transportistas reales · categorías `inicial_2, inicial_3` · calibres
`exportacion, granel, sin_chicas` · kg por bolsa entre 47 y 54.

## Endpoints nuevos (`/api/papasud/...`, requieren sesión igual que el resto)

| Endpoint | Para qué |
|---|---|
| `GET /api/papasud/catalogos` | variedades, campos (5, incl. Cayetano Chávez), laboratorio, planta+zonas, tolva, frigoríficos, clientes, transportistas, roles, Albor Agro |
| `GET /api/papasud/lotes` | los 60 lotes reales con su campo/pivote/cuadrante/variedad. Lote 300 = Cayetano Chávez |
| `GET /api/papasud/mapa` | grafo del flujo real (`nodos`/`aristas`/`capas`) **más** `filas` de stock vivo. La planta es el hub |
| `GET /api/papasud/planta` | zonas (báscula, reclasificación, playa), stock, recepciones recientes |
| `GET /api/papasud/sitios` | kg vivos agrupados: planta / cada frío / cada campo |
| `GET /api/papasud/ordenes-carga` | el papel del campo (kg estimado, pendiente de pesaje) |
| `GET /api/papasud/recepciones` | planilla de recepción: peso de báscula, chofer, lote |
| `GET /api/papasud/disponibilidad?variedad_id=spunta` | "¿tengo X de Spunta?" — la consulta que abre la demo (Track A) |
| `POST /api/papasud/pedido/verificar` | el motor de bloqueo-con-alternativa. Body: `{variedad_id, kg_pedido, lote_id?, ubicacion_id?, calibre_requerido?}`. Devuelve `bloqueado`, `mensaje` ya armado, y `alternativas` (lote, ubicación, kg, si requiere traslado desde frigorífico) |
| `GET /api/papasud/pedido/verificar-demo` | el caso plantado en el dataset, listo para la demo, sin tener que armar el body a mano |
| `GET /api/papasud/inconsistencias` | la lista de "arreglar el pasado", cada hallazgo con los movimientos que lo sostienen |
| `GET /api/papasud/liquidacion/transportistas?desde=&hasta=` | kg movidos y $ a pagar por transportista |
| `GET /api/papasud/liquidacion/frigorificos?desde=&hasta=` | kg movidos por frigorífico |
| `POST /api/papasud/importar-planilla` (multipart) | sube la planilla real de 12 solapas, la estructura, **no persiste nada** |

**Regla de arquitectura que ya está resuelta acá:** `stock_real.verificar_pedido`
es 100% Python determinista. Ángela (Track A) llama a este endpoint y **narra
el resultado verbatim** — nunca elige un lote alternativo por su cuenta.

## El escenario de demo ya está sembrado

`GET /api/papasud/pedido/verificar-demo` devuelve, sin armar nada:
- un pedido que excede lo disponible en un lote/planta puntual,
- bloqueado,
- con al menos una alternativa real (mismo variedad, calibre compatible con
  exportación, en otro lote/ubicación).

## Lo que falta de mi lado (Track B)

- Validar el importador contra la planilla real de Papasud (`Planilla_de_movimientos_2026.xls`,
  12 solapas) en cuanto la tengamos — hoy sólo está probado contra planillas
  sintéticas con las mismas columnas documentadas.
- Si el modelo cambia (nombres de campo, nuevas entidades), aviso acá mismo.

Cualquier cosa, todo esto vive bajo `core.modelo_real`, `core.stock_real`,
`core.inconsistencias_papasud`, `core.liquidacion` e `importer_papasud` —
no rompe nada de lo que ya construyeron.
