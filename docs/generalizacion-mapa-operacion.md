# Generalización del "mapa de la operación" a un modelo multi-industria

> Documento post-hackathon. Analiza cómo está construido hoy el mapa de operación de Papasud y propone cómo generalizarlo — en datos, backend y UI — para que la misma feature (cadena de custodia con linaje jerárquico y curva de decaimiento) sirva para cualquier industria, no solo papa semilla. Pensado como input para portar la feature a otro repo.

## 1. Cómo está construido hoy

Hay **dos mapas paralelos**, ambos con React Flow (`@xyflow/react`), sin base de datos relacional — todo vive en JSON/Python hardcodeado a un único tenant (Papasud):

- **Mapa "viejo"**: `frontend/src/sections/MapaOperacion.jsx` (674 líneas) + `backend/core/mapa.py` (634 líneas), función `mapa()` (línea 493) y `genealogia()` (línea 527). Endpoints `GET /api/mapa-operacion` y `GET /api/genealogia/{lote}` (`backend/main.py:1141-1165`).
- **Mapa "real"** (planta como hub, más nuevo): `frontend/src/sections/MapaFlujoPapasud.jsx` + `backend/core/mapa_real.py`, endpoint `GET /api/papasud/mapa`.

No hay `CREATE TABLE` en el repo. El "modelo de datos" es:

- `data-papasud/dominio.py` — constantes Python fijas: `UBICACIONES` (4 ubicaciones con tipo `frigorifico`/`galpon`, `capacidad_kg`, `temp_objetivo`), `CATEGORIAS` INASE con `orden` (escalera de pedigrí) y `virus_max_pct`.
- `data-papasud/catalogos.json` — variedades, clientes, campos.
- `backend/core/movimientos_nl.py:45` / `exportacion.py:73` — `KG_POR_BOLSON = 1000` (⚠️ desalineado con CLAUDE.md, que fija ~700 kg reales — bug a corregir de paso).

### El problema concreto

`backend/core/mapa.py` mezcla, en las mismas funciones, lógica genérica y lógica específica de papa semilla:

- **Genérico y reusable**: agregación de stock por ubicación (línea 83), agregación de movimientos en corredores origen→destino (285-309), resaltado de "camino" en el grafo (316-411).
- **Específico de papa semilla, incrustado ahí mismo**: filtro por string `"Preinicial" in categoria` (línea 184) en vez de una comparación numérica de jerarquía, escalera in-vitro→campo→cámara (176-240), riesgo de brotación con ventana de 45 días hardcodeada (386-410), `requisitos_onpf` por cliente (293).

En el frontend, `NodoOperacion` (MapaOperacion.jsx:108-190) lee campos de negocio fijos (`data.metricas.por_brotar`, `.ya_brotados`, `.ocupacion_pct`) y un switch de íconos hardcodeado a los tipos `frigorifico`/`galpon`/`campo`/`laboratorio`/etc. El motor de layout por capas (`W`, `COL`, `GRID_Y`, semáforo azul/verde/ámbar/rojo por `estado`) sí es genérico y se lleva prácticamente tal cual.

## 2. Modelo de datos genérico propuesto

Ver **`supabase/migrations/0001_custody_chain_config.sql`** para el schema completo, comentado en inglés. Resumen de las tablas nuevas (todas escopeadas por `tenant_id`, reemplazando las constantes Python de `dominio.py`):

| Tabla | Reemplaza | Descripción |
|---|---|---|
| `tenant` | — (no existía) | Un cliente/organización. Todo lo demás cuelga de acá. |
| `location_type` | `UBICACIONES` | Tipos de ubicación (cámara fría, galpón, campo, laboratorio, celda de barricas, sala de curado...) con `attributes jsonb` schema-less por tipo (`capacidad_kg`, `temp_objetivo`, `humedad_objetivo`...). |
| `category` | `CATEGORIAS` (escalera INASE) | Jerarquía de linaje/grado, con `sort_order` (posición en la escalera) y **`lineage_rule`** (`child_gte_parent` \| `child_lte_parent`) — ver más abajo por qué esto no puede asumirse fijo. |
| `unit_of_measure` | `KG_POR_BOLSON` | Unidad de conteo y su peso/capacidad real (bolsón, barrica, pallet, fardo...). |
| `decay_curve` | `VENTANA_BROTACION_DIAS` + lógica de merma en `conciliacion.py` | Curva de pérdida/decaimiento esperado (%) por categoría y días de almacenamiento — no lineal, con FK compuesta a `category`. |

Las entidades que **ya son agnósticas de industria y se llevan tal cual** (no están en esta migración porque no son el problema): `ubicacion`, `lote` (con `lote_padre_id`), `movimiento` (append-only), `stock` (view derivada). Esas cuatro son el corazón de "una sola verdad" y sirven igual para papa semilla, farmacéutica, vino, semiconductores, etc.

### El hallazgo clave: la regla de linaje no siempre va en el mismo sentido

En Papasud, un lote hijo debe ser de categoría **igual o superior** a su padre (`orden(padre) <= orden(hijo)`). Pero en binning de semiconductores la regla corre **al revés**: un die nunca puede clasificarse en un bin de mayor grado que el máximo probado del wafer padre (`orden(hijo) <= orden(padre)`). Por eso `category.lineage_rule` es un campo explícito (`child_gte_parent` / `child_lte_parent`) en vez de asumir una dirección fija como hacía el string-match de `mapa.py:184`.

## 3. Ejemplos multi-industria (auto-documentación ejecutable)

**`supabase/seed.sql`** carga 8 tenants de ejemplo, cada uno un caso de uso completo (ubicaciones + escalera de categorías + unidad + curva de decaimiento donde aplica). No es data de producción — es documentación en forma de INSERTs, pensada para copiar el bloque más parecido al armar un tenant nuevo:

1. **Papa semilla** (Papasud, el caso original) — escalera INASE con `child_gte_parent`, curva de merma por respiración/deshidratación, bolsón de 700 kg corregido.
2. **Farmacéutica (cadena de frío)** — grado de API (industrial → farmacéutico → estéril inyectable → dosis terminada), curva = pérdida de potencia por ruptura de frío, no de peso.
3. **Vitivinícola** — clasificación (mesa → denominación de origen → grand cru), curva = evaporación en barrica ("angel's share").
4. **Lácteos (queso)** — pasta blanda/semidura/dura, curva = deshidratación en maduración (mismo mecanismo físico que la papa).
5. **Cannabis medicinal** — outdoor/invernadero/indoor, curva = degradación de THC/terpenos en curado.
6. **Semiconductores** — binning de die (C/B/A) con `lineage_rule = child_lte_parent` (la excepción que prueba la regla) y **sin filas en `decay_curve`** — el silicio no decae en storage, y eso también hay que poder representarlo (tabla vacía es un estado válido, no un error).
7. **Café** — comercial/premium/especialidad (SCA ≥80/≥85), curva = pérdida de humedad en verde.
8. **Textil (algodón)** — fibra corta/media/larga (Pima), sin curva de decaimiento por el mismo motivo que semiconductores.

## 4. Backend: separar motor genérico de adaptador de industria

Partir `mapa.py` en dos capas:

```python
# graph_engine.py — no importa nada de papasud/dominio.py
def construir_nodos(ubicaciones, stock_por_ubicacion) -> list[Nodo]: ...
def construir_corredores(movimientos) -> list[Arista]: ...
def resaltar_camino(nodos, aristas, movimientos_relevantes) -> HighlightPath: ...
```

```python
class IndustriaAdapter(Protocol):
    def metricas_nodo(self, ubicacion, stock) -> list[Metrica]: ...
    def validar_linaje(self, lote_padre, lote_hijo) -> Resultado: ...  # lee category.lineage_rule
    def clasificar_discrepancia(self, declarado, contado, dias_almacenado) -> str: ...  # lee decay_curve

class PapaSemillaAdapter(IndustriaAdapter):
    # acá vive lo que hoy son las líneas 176-410 de mapa.py: brotación, INASE, bolsón
    ...
```

El endpoint queda: motor genérico arma nodos/aristas → adaptador del tenant activo los decora con métricas propias, leyendo `category`/`decay_curve`/`unit_of_measure` en vez de constantes Python. Un tenant nuevo (café, semiconductores) es una fila en las tablas de config, no necesariamente código nuevo — salvo que necesite una hipótesis de discrepancia realmente distinta.

## 5. Frontend: nodo declarativo en vez de campos fijos

`NodoOperacion` deja de leer `data.metricas.por_brotar` a mano. El backend manda una lista de métricas ya formateadas (respetando la regla de arquitectura del proyecto: el LLM/frontend nunca calcula ni reformatea números):

```ts
interface Metrica {
  label: string;        // "Por brotar" | "Bin A disponible" | "Grand cru en barrica"
  valor: string;         // ya formateado, ej "1.240 kg"
  estado?: 'inferido' | 'confirmado' | 'dudoso' | 'error';
}

interface NodoOperacionData {
  tipo: string;          // viene de location_type.id, no de un switch hardcodeado
  icono: string;          // location_type.icon
  metricas: Metrica[];    // longitud variable, el componente solo itera
}
```

El motor de layout por capas y el semáforo de color epistémico (azul/verde/ámbar/rojo) se portan sin cambios — ya son genéricos.

## 6. Plan de migración concreto

1. Cargar `0001_custody_chain_config.sql` + `seed.sql` en el proyecto Supabase destino; correr con el tenant `papa semilla` primero para no romper la demo existente mientras se generaliza.
2. Extraer `graph_engine.py` de `mapa.py` sin tocar lógica, solo separando funciones genéricas.
3. Escribir `PapaSemillaAdapter` con lo que quedó afuera (brotación, INASE, bolsón) — líneas 176-410 de `mapa.py` hoy.
4. Cambiar el endpoint para que arme nodos vía motor genérico + adaptador, devolviendo `metricas: Metrica[]` en vez de campos sueltos.
5. Reescribir `NodoOperacion` para iterar `metricas` en vez de leer campos fijos.
6. Validar regresión contra el seed de papa semilla, y recién ahí escribir un segundo adaptador (ej. farmacéutica) para confirmar que la abstracción generaliza de verdad y no solo en el papel.
7. De paso, corregir `KG_POR_BOLSON = 1000` → 700 (o mejor, leerlo de `unit_of_measure`).

## Archivos de esta entrega

- `supabase/migrations/0001_custody_chain_config.sql` — schema genérico, comentado en inglés.
- `supabase/seed.sql` — 8 tenants de ejemplo (INSERTs comentados en inglés) como auto-documentación de casos de uso.
- Este documento.
