# Cadena de custodia real — planta, campo y frío

Fuente: charla del 22 de agosto de 2026 con Leandro y Sergio Pérsico (Papasud).
Primera mano. Esto pisa el supuesto de las "4 ubicaciones = 4 depósitos".

## El mapa no es un layout de fábrica

Textual: *"no es una fábrica convencional, no quiero un layout de que se hace
todo en el lugar. Las mercaderías se hacen en los campos, vienen a una planta
y de ahí puede tener distintos orígenes o almacenamiento o venta."*

El flujo que hay que pintar, y que el seed ahora genera:

```
laboratorio in vitro
        ↓
CAMPO ── lote (una variedad) ── orden de carga (papel)
        │
        │  tolva, a granel, con tierra
        ↓
PLANTA Mar del Plata
   1. recepción / báscula     → planilla de recepción
   2. reclasificación/empaque → granel → bolsas calibradas
   3. playa de carga
        │
        ├──────────────► CLIENTE
        ├──────────────► FRIGORÍFICO ──► vuelve a PLANTA ──► CLIENTE
        └──────────────► FRIGORÍFICO ──► CLIENTE          (poco común)

Atajos (existen, son menos):
  campo → cliente
  campo → frigorífico
```

La planta es el **hub**. El frigorífico es almacenamiento subcontratado, no el
mostrador. *"No sale la papa usualmente del frigorífico a la venta de clientes,
sale de la planta."* El circuito más común es planta → frío → planta → cliente.

## Campo → lote (regla dura)

- Un **campo** (Santa Ana, Marisol, Trevelin, Oriente, **Cayetano Chávez** en
  partido San Cayetano) tiene muchos lotes.
- Un **lote** es una superficie inscripta en INASE. *"Cuando decimos lote 300,
  está en un determinado campo."*
- **Un lote, una variedad.** *"El lote 300 son peras, el 101 son manzanas, son
  totalmente diferentes."* Pueden convivir varios lotes de la misma variedad en
  el mismo campo; nunca dos variedades en un mismo lote.
- El lote 300, en este dataset, vive en Cayetano Chávez — lo citaron juntos.

## Lo que hay EN EL MEDIO (campo → frío)

No es un salto. Cada camión deja rastro:

| Entidad | Dónde nace | Qué registra |
|---|---|---|
| **Orden de carga** | Campo, en papel | Lote, variedad, camión, chofer, kg *estimado* (pendiente de pesaje). A veces no hay señal. A veces sale **sin remito**. |
| **Tolva** | El viaje | *"Tolva se llama el camión que trae la papa a granel."* Suelta, con tierra. |
| **Recepción / báscula** | Planta, primer ingreso | Peso real, camionero, producto, lote. Nace la **planilla de recepción**. El remito a menudo se carga acá, no en el campo. |
| **Reclasificación** | Planta | De granel con tierra a bolsas. Calibre (exportación / granel / sin chicas). No es un depósito: el stock sigue en `planta_mdp`. |
| **Playa de carga** | Planta | Sale a cliente, a frío, o recibe el retiro de frío. |
| **Envío a frío** | Planta → frigorífico | Ya en bolsas. Remito nuevo (el 651 de ingreso no es el de salida). |
| **Retiro de frío** | Frigorífico → planta | Movimiento **interno**. *"Viene a la planta."* De acá recién se despacha. |
| **Entrega a cliente** | Planta (lo normal) | Exportación sale calibrada. El comercial pregunta stock **antes** de vender. |

Observaciones que ellos cargan hoy a mano: temperatura de cosecha, estado de
la mercadería, quién trajo el camión, flete a pagar.

## Frigoríficos

Dospanca, Galpón Mar del Plata, Pancani, Sasula. **Subcontratados** — Papasud
paga el servicio. Por eso liquidar kilos y fletes sale del mismo libro de
movimientos, no de otra planilla.

El desfasaje que ellos viven: *"Tengo que ver. Agatha 24, guardamos 7.000
bolsas. Retiramos 6.000. Tendría que haber mil. A mí me da que había 800."*
Eso es exactamente `kilos_no_cierran` en el detector.

## Lo que NO es el problema

No es un problema de Excel vs. IA. Es un problema de **información**: que entre
verificable, que esté lo más al día posible, y que cada rol vea el recorte que
necesita (campo, planta, frío, administración, comercial) sin filtrar solapas.

Albor Agro se queda: usan sólo el paquete contable. Esta plataforma no lo
reemplaza; el movimiento confirmado es lo que después se liquida allá.

WhatsApp no alcanza: quieren centralizado, con permisos, y que un audio o una
foto no se pierda en el grupo.

## Dónde vive en el código

- Catálogos y reglas: `data-papasud/dominio_real.py`
- Seed: `data-papasud/generar_real.py` → `ordenes_carga_real.json`,
  `recepciones_planta_real.json`, `reclasificaciones_real.json`
- Grafo del mapa: `backend/core/mapa_real.py` → `GET /api/papasud/mapa`
- Planta como hub: `GET /api/papasud/planta`
- Pantalla: `frontend/src/sections/MapaFlujoPapasud.jsx`
