# PolPilot × Papasud — Vertical 3: stock, trazabilidad y compliance

> **Sobre los datos.** La empresa es real y el modelo del negocio está calcado de
> su operación —cuatro ubicaciones, ~150 lotes, semilla de papa fiscalizada,
> exportación—, pero **todo el dataset es sintético**: lo genera
> `data-papasud/generar.py` con seed fija. Las seis personas del equipo son
> inventadas. Ningún número de este repositorio sale de un sistema de Papasud.

Hackathon Cursor Mar del Plata · 22 de agosto de 2026.

---

## El problema, en las palabras del brief

> «El stock de semilla está repartido en cuatro ubicaciones físicas (tres
> frigoríficos y un galpón), con alrededor de 150 lotes. El registro se hace en
> una planilla que varias personas editan al mismo tiempo, lo que genera errores
> de versión. Nadie tiene una visión única y confiable de cuánto stock hay y
> dónde está en un momento dado — **y las diferencias entre lo que dice la
> planilla y lo que hay en la realidad suelen descubrirse recién al momento de
> entregarle el pedido a un cliente**.»

El dolor no es el desorden: es el papelón. El camión en la playa, el cliente
esperando, y ahí aparece que faltan dieciocho bolsones.

---

## Los tres niveles

### N01 · Movimientos por voz o texto, sin planillas

Un operario dice *«pasé dieciocho bolsones de Spunta de Ruta 226 al galpón»* y
eso se convierte en una transacción con lote, cantidad, origen y destino.

**Dónde está el límite.** El modelo interpreta el **lenguaje**: de qué lote
habla, si movió o despachó, a qué ubicación le dice «el galpón». El código
valida los **números y los identificadores**, y **rechaza** si el origen no tiene
los kilos — no advierte, rechaza. «Dieciocho» y «ochenta» suenan parecido
adentro de una cámara con el motor andando.

Si hay varios lotes candidatos, **elige una persona**. El sistema nunca desempata
solo: mover el lote equivocado son bolsones reales en una cámara real.

La pieza que hoy no existe en la planilla es el estado **`en tránsito`**: entre
que los bolsones salen de una cámara y alguien los confirma en la otra, esos
kilos no están en ningún lado. Ahí nacen las diferencias.

`core/movimientos.py` · `core/movimientos_nl.py` · `sections/Movimientos.jsx`

### N02 · Vista única de las cuatro ubicaciones

Un tablero con los cuatro sitios en una sola lectura, que **previene la emisión
de órdenes de carga sin stock real verificado**.

Y cuando hay diferencia entre lo declarado y lo contado, **propone la causa**.
Acá está la decisión que sostiene todo el proyecto: **la hipótesis no la inventa
el modelo, la busca el código**, con reglas explícitas y trayendo la evidencia:

```
[movimiento_sin_confirmar]  El movimiento MOV-2026-0912 del 12/08 sacó 18.000 kg
   de Frigorífico Ruta 226 hacia Galpón Chapadmalal y nadie lo confirmó en
   destino. Son exactamente los kilos que faltan acá.

[cantidad_mal_tipeada]  MOV-2026-0873 del 04/08 registró 42.000 kg. Si hubieran
   sido 4.200 — un cero de más al cargarlo — la cámara cerraría exacta.

[merma_fisica]  Faltan 3.100 kg y ningún movimiento los explica. Dalia anotó el
   18/08: «El lote de Spunta de la Cámara 3 está brotando antes de tiempo…»

[sin_explicacion]  No hay nada en los datos que lo explique. Hay que recontar.
```

Sería fácil pasarle la diferencia a un LLM y pedirle que especule. Suena bien y
no sirve: en una empresa que audita cada lote, una causa inventada es peor que
ningún dato. Cada hipótesis viaja con su evidencia — número de movimiento,
fecha, quién lo cargó, qué nota lo respalda — y se puede abrir y verificar.

`core/conciliacion.py` · `sections/Ubicaciones.jsx` · `sections/Conciliacion.jsx`

### N03 · Copiloto de documentación de exportación

Los seis papeles de una carpeta de exportación, **pre-completados desde la
trazabilidad del lote**, y cada campo diciendo **de dónde salió**:

| Documento | Organismo | Fuente de los campos |
|---|---|---|
| Factura proforma | Papasud | campos de la Factura E (AFIP WSFEX), sin CAE |
| Packing list | Papasud | contenedor marítimo · NCM 0701.10.00 |
| Solicitud de exportación de semilla | INASE | Res. 56/18 Anexo II · Res. SAGYP 715/94 |
| Certificado Fitosanitario | SENASA | modelo IPPC / NIMF 12 |
| Rótulo oficial | INASE | Res. 171/2000 art. 16 · Ley 20.247 art. 9 |
| Certificado de origen | Cámara de Comercio | MERCOSUR / ALADI |

Y el **control cruzado**, que ningún formulario hace solo: que los kilos, los
bultos y la descripción digan lo mismo en la factura, el packing list y la
solicitud del INASE. Ese descuadre es la causa número uno de demora en aduana, y
es trivial de verificar cuando los tres salen de la misma fuente.

`core/exportacion.py` · `sections/Exportacion.jsx`

---

## Más allá del brief

**El freno del remito.** Cinco controles antes de emitir: stock verificado,
conteos en discusión, análisis sanitario vigente, calibre consistente con el
grado del rótulo, y brotación. Con un bloqueo abierto **no hay botón de emitir**:
hay motivo con su número exacto. El freno vive en el core, no en la pantalla —
no hay puerta de atrás por la que salga un remito sin verificar.

**Modo sin conexión.** Adentro de un frigorífico no hay señal. Un service worker
hace que la app **abra**, un snapshot del stock (52 KB) vive en IndexedDB, el
**mismo intérprete determinista corre en el celular**, y lo que se registra queda
en una cola visible que sincroniza sola y **re-valida contra el stock real** al
volver la señal. Lo que no pasa la re-validación no se descarta en silencio:
queda marcado para que decida una persona.

**Trazabilidad punta a punta.** El pedigrí del lote de la cosecha al contenedor:
identidad, campo de origen, sanidad, cadena de custodia con quién movió qué,
compromisos, lo que el equipo dijo, y las alertas. Cada bloque declara su fuente.

**Seis personas, seis PolPilot.** Ernesto (dueño), Cecilia (comercio exterior),
Rubén (encargado), Marcos (operario de frigorífico, mobile), Dalia (agrónoma,
Directora Técnica), Néstor (galpón, recién entrado). Cada rol ve sus secciones,
sus acciones y sus hallazgos: Ernesto ve 9 oportunidades, Marcos 3.

**El reloj real del negocio.** La semilla no vence: **brota**. En cámara a 3–5 °C
el frío estira la dormancia (×3,2) y la brotación se posterga; en el galpón sin
frío corre a reloj natural — por eso el galpón es tránsito y no depósito. Un lote
que brota antes de despacharse deja de ser semilla de su categoría.

---

## El dataset

`data-papasud/generar.py` — determinista, con asserts que **abortan** si un
número no cruza.

| | |
|---|---|
| Superficie | 214,3 ha en 5 campos |
| Producción del ciclo | 7.468,5 t cosechadas · campaña 2025/26 |
| Lotes | **147** · 6 variedades · 9 categorías INASE |
| Stock hoy en cámara | 5.524,7 t · $3.423.852.141 inmovilizados |
| Ocupación | Sierra 83,7% · Ruta 226 73,9% · Batán 90,5% · Galpón 30,9% |
| Exportación | 27,8% del stock |
| Movimientos | 330 · Conteos 60 · Órdenes de carga 13 |

**Apoyado en fuentes, no en invención:** categorías y subcategorías de la
Res. INASE 171/2000; tolerancias de PVY por categoría (Inicial I 0,2% →
Certificada 15%); calibres por grado en mm (art. 25) y grados por peso en gramos
para minitubérculo (Res. 217/2002 art. 22); envase máximo 50 kg a campo
(art. 23); rótulo del art. 16; conservación a 3–5 °C con 85–90% de humedad;
análisis DAS-ELISA. Y el circuito real de Papasud: multiplicación in vitro,
minitubérculo en El Calafate por aislamiento sanitario, multiplicación a campo en
Tres Arroyos, San Cayetano y González Chaves, exportación a Vietnam por el
puerto de Mar del Plata.

**Tres inconsistencias plantadas a propósito**, cada una con su causa adentro de
los datos: el movimiento del 12/08 sin confirmar en destino (el ejemplo textual
del brief), el cero de más al tipear, y la merma por brotación que sólo explica
una nota del equipo.

---

## Cómo se levanta

Requisitos: Python 3.12+, Node 20+.

```bash
cd backend && pip install -r requirements.txt
cp .env.example .env        # y pegá la key del gateway
POLPILOT_DEMO_TODAY=2026-08-22 python -m uvicorn main:app --port 8020
```

```bash
cd frontend && npm ci
POLPILOT_API_PORT=8020 npm run dev -- --port 5210
```

**El «hoy» del dataset es 2026-08-22.** El backend tiene que levantarse con esa
fecha o los análisis no coinciden con la historia sembrada.

**Usuarios:** las contraseñas se generan en el primer arranque y quedan en
`data-papasud/credenciales.json` (gitignoreado). El dueño es `ernesto`.

### Ángela

Va por el **AI Gateway de Vercel**. `config.cliente_llm()` es la única fábrica de
cliente del sistema (chat, visión, voz, intérprete de movimientos), y `LLM_MODE`
conmuta sin tocar código:

- `gateway` — Claude por el AI Gateway (`AI_GATEWAY_API_KEY`). El default.
- `anthropic` — la API directa (`ANTHROPIC_API_KEY`).
- `simulado` — **sin modelo**: el router determinista por intenciones y los
  intérpretes por patrones. El sistema no se cae ni se degrada a un error;
  entiende menos lenguaje y responde con los mismos módulos core.

Ese último modo no es decorativo: es la red de seguridad si el gateway no
responde el día de la demo.

**Ángela no inventa números.** Los datos van al prompt como contexto verificable
y las tools devuelven totales ya calculados; el modelo narra y cita la fuente.
Si alguien pregunta «¿esto lo inventa?», se abre el JSON.

---

## Arquitectura

```
backend/
  core/            el borde determinista — los números salen de cálculo
    movimientos.py       N01 · lenguaje libre → transacción validada
    conciliacion.py      N02 · declarado vs contado, con la causa buscada
    ordenes_carga.py     el freno del remito (5 controles)
    exportacion.py       N03 · los 6 documentos pre-completados
    trazabilidad.py      el pedigrí del lote, punta a punta
    semilla.py           el catálogo del rubro (INASE, calibres, clientes)
  angela.py        el orquestador · 48 tools filtradas por rol
  config.py        EL switch de transporte del modelo
frontend/src/
  sections/        Ubicaciones · Conciliación · Movimientos · Despachos · Exportación
  lib/offline.js   la cola sin señal (IndexedDB) y la sincronización
  lib/interpretarLocal.js   el intérprete que corre en el celular
data-papasud/      el dataset sintético y su generador determinista
```

## Tests

```bash
cd backend && python -m pytest
```

> La suite escribe en el data dir del tenant. Después de correrla, restaurá los
> seeds con `git checkout -- data-papasud/`.
