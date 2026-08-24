# data-papasud — seed oficial

El backend, sin ninguna env, lee este directorio. El modelo es el de la
**Planilla de movimientos 2026.xls**: lote namespaced por chacra, remito con
líneas, DTV del viaje, bolsa + hilo, frío de terceros, calibre comercial.

Las personas del equipo son inventadas (`backend/usuarios_papasud.py`).

## Generar

```bash
python data-papasud/generar.py
```

Escribe `inventory.json`, `catalogos.json`, `apartados.json`, `lotes.json`,
`remitos.json` y `plantadas.json`.

Los tres beats de la demo viven acá, sobre sitios reales:

1. Stock insuficiente — `OC-2026-2461` pide 24 t de un lote con 18 t en tránsito
   de Pancani al galpón (`MOV-2026-0912`).
2. Linaje inválido — plantado en `plantadas.json`, no persistido como lote.
3. Merma en frío de terceros — conteo de Ágata en Pancani Cámara 1.

## Endpoints

- `GET /api/remitos`
- `GET /api/remitos/{id}`
- `GET /api/planilla/lotes?nro=50` — puede devolver varios; nunca desempata
- `GET /api/planilla/modelo`
