# data-planilla — el libro real, en un subtree aparte

El seed de `data-papasud/` sigue siendo el de la demo (cuatro frigoríficos
inventados, rótulo `PS-202526-…`, bolsón de 1.000 kg). Este directorio no lo
pisa.

Acá vive el modelo que sale de `Planilla de movimientos 2026.xls`:

- **lote** namespaced `(chacra, variedad, nro, sufijo)` — el 50 de Santa Ana no
  es el 50 de Trevelin
- **remito** con líneas — un viaje, un DTV, varios lotes
- **color_bolsa + color_hilo** — cómo se reconoce un bulto en el piso
- **ubicaciones reales**, con `frio_tercero` (Pancani, Cecive, Sasula…)
- **calibre comercial** (`recibo`, `exportacion`, `sin_chicas`…) aparte del
  grado INASE en mm
- **envase** bolsa ~50 kg / bolsón 700 kg / granel
- **reproceso** y **retorno**, no sólo traslado
- **lote_padre_id** de verdad, con la regla de linaje

## Generar

```bash
py -m data_planilla.generar
```

desde este directorio. Escribe `inventory.json`, `catalogos.json`,
`apartados.json`, `lotes.json` y `remitos.json`.

## Apuntar el backend (opt-in)

```bash
set POLPILOT_DATA_DIR=..\data-planilla
```

Sin esa env, el backend sigue leyendo `data-papasud/`.

## Endpoints nuevos

- `GET /api/remitos`
- `GET /api/remitos/{id}`
- `GET /api/planilla/lotes?nro=50` — puede devolver varios; nunca desempata
- `GET /api/planilla/modelo`
