---
tags: [reference, hackathon, papasud, domain, data-model]
date: 2026-08-21
---

# Modelo de datos de papa semilla — el detalle que hace creíble la demo

> ## ⚠️ CORRECCIÓN IMPORTANTE — leer antes de usar la escalera de subcategorías
>
> La escalera de **10 pasos** de este documento (con **Prefundación**, y **Certificada** como terminal única) salió de un WebFetch de la Res. 171/2000. **Investigación posterior la contradice.** Ver [[hackathon-technical-feasibility]], que cita [Res. INASE **245/98** en Infoleg](https://servicios.infoleg.gob.ar/infolegInternet/anexos/50000-54999/53715/norma.htm) como la norma de papa semilla, con esta estructura:
>
> - **Categoría Básica:** Preinicial 0 / I / II · Inicial I / II / III · **Fundación**
> - **Categoría Certificada:** **Registrada** · **Certificada A / B**
>
> Diferencias con lo escrito abajo: **no aparece «Prefundación»**, y la terminal es **Certificada A/B**, no «Certificada» sola. También cambia el número de norma (245/98 vs 171/2000).
>
> **Qué sí está corroborado por todas las fuentes** y es lo único que conviene implementar: la división **Básica / Certificada**, y la regla de que **cada lote desciende de una subcategoría igual o superior**.
>
> **No poner un número de artículo en pantalla sin verificarlo** con la gente de Papasud en los primeros 20 minutos. Equivocarse sobre una norma delante de quienes la cumplen todos los días es peor que no citarla.
>
> **Vocabulario:** no decir «prebásica / básica / registrada / certificada» — es el escalón genérico de cereales y delata. **Papasud vende G3** (tercera generación); etiquetar `Categoría: Certificada – Registrada · Generación: G3`.

Contexto de dominio para [[cursor-hackathon-mar-del-plata-2026]] / [[papasud]].
Complementa [[papasud-company-research]] (cadena de 3-7 años, 1.800 km) y [[hackathon-demo-strategy]].

**Por qué importa:** la investigación de contexto mostró que las "4 ubicaciones físicas" del brief son el **final** de una cadena de custodia plurianual, no un problema de inventario. Este documento aporta el vocabulario regulatorio real para modelar eso. Un lote de papa semilla **no es una fila de stock: es un nodo en un árbol genealógico fiscalizado**.

---

## La cadena oficial de subcategorías (INASE, Res. 171/2000)

`[VERIFICADO]` — fuente: [INASE Resolución 171/2000, texto oficial](https://www.argentina.gob.ar/normativa/nacional/norma-64565/texto)

El sistema argentino **no usa** la nomenclatura G0/G1/G2 (esa es europea/holandesa). Usa **clases → categorías → subcategorías**, con una progresión lineal de **10 pasos**:

### Bajo condiciones controladas (laboratorio / invernáculo)

| # | Subcategoría | Qué es |
|---|---|---|
| 1 | **Preinicial 0** | microplantas / microtubérculos **in vitro** |
| 2 | **Preinicial I** | plantines / **minitubérculos** ex vitro |
| 3 | **Preinicial II** | materiales ex vitro |

### A campo

| # | Subcategoría | Categoría |
|---|---|---|
| 4 | **Inicial I** | Básica |
| 5 | **Inicial II** | Básica |
| 6 | **Inicial III** | Básica |
| 7 | **Prefundación** | Básica |
| 8 | **Fundación** | Básica |
| 9 | **Registrada** | Certificada |
| 10 | **Certificada** | Certificada |

**Regla estructural clave (Art. 2):** cada subcategoría debe originarse en *"la misma o superior"* subcategoría anterior — *"Es la semilla obtenida a partir de [subcategoría anterior] o superior"*.

→ **Esto es una restricción de integridad referencial, literalmente.** Todo lote tiene un lote padre, y la subcategoría del hijo está determinada (y acotada) por la del padre. Es una validación que se puede implementar y **demostrar en vivo** — y que hoy una planilla compartida no puede hacer.

**No hay límite explícito de generaciones**: el avance depende de cumplir los estándares fitosanitarios y de calidad. Es decir, la degradación de categoría no es automática por tiempo, es **por resultado de análisis**.

---

## Qué identifica unívocamente a un lote

`[VERIFICADO]` — Art. 16 (rótulos oficiales) y Art. 8/10 (carteles a campo)

**Rótulo oficial debe llevar:**
- clase fiscalizada
- **categoría y subcategoría**
- **variedad**
- **zona de producción**
- **año de cosecha**
- nombre y **número de inscripción** del semillero
- máximo **50 kg por envase** para semilla producida a campo
- grado marcado con sello de tinta
- *"Material tratado con veneno"* en letras rojas si tuvo tratamiento químico

**Cartel a campo debe llevar:** variedad, **número de lote** y subcategoría plantada.

→ La clave natural de un lote es aproximadamente:
`(semillero, variedad, subcategoría, zona de producción, año de cosecha, nro de lote)`

---

## Documentación exigida por lote

`[VERIFICADO]` — Art. 15

1. **Registro de Cultivo** — con los informes de inspección
2. **Certificado de Análisis de Postcontrol** — análisis post-cosecha
3. **Destino presuntivo de la producción**

→ Nótese: **"destino presuntivo"** se declara desde la producción. Eso conecta directamente la Vertical 03 (stock) con el compliance de exportación: el destino no aparece al final, se arrastra desde el principio. Y encaja con el régimen **DEE (Destino Exclusivo Exportación)** que ya estaba en la investigación de contexto.

---

## Esquema propuesto (listo para copiar mañana)

Sirve para cualquiera de las 3 verticales — es el núcleo compartido.

```sql
-- La variedad como entidad, NO como string en una celda.
-- (ver papasud-company-research: Papasud importa 93,2% de la semilla del país
--  y el régimen de derechos de obtentor sobre Innovator/HZPC está en disputa)
create table variedad (
  id            text primary key,          -- 'innovator', 'spunta', 'atlantic'
  nombre        text not null,
  obtentor      text,                      -- 'HZPC'
  licencia      text,                      -- régimen / titular de derechos
  uso           text                       -- 'industria' | 'fresco'
);

create table ubicacion (
  id            text primary key,
  nombre        text not null,             -- 'Planta Mar del Plata', 'Dospanca', 'Cayetano Chávez'
  tipo          text not null,             -- 'planta' | 'frigorifico' | 'campo' | 'laboratorio' | 'cliente'
  localidad     text,
  provincia     text,
  partido       text,
  subcontratado boolean default false,     -- los frigoríficos NO son de Papasud
  tiene_bascula boolean default false,     -- sólo la planta
  geom          jsonb
);

-- Estaciones de proceso DENTRO de la planta. No son depósitos: el stock
-- vive en planta_mdp. Charla 22/08: recepción/báscula → reclasificación → playa.
create table zona_planta (
  id          text primary key,            -- 'recepcion' | 'reclasificacion' | 'playa'
  planta_id   text not null references ubicacion(id),
  nombre      text not null,
  rol         text not null                -- 'primer_ingreso' | 'calibre_empaque' | 'despacho'
);


-- LO IMPORTANTE: lote_padre_id. El linaje es el modelo.
create table lote (
  id                text primary key,
  nro_lote          text not null,
  variedad_id       text not null references variedad(id),
  subcategoria      text not null,         -- ver enum de 10 pasos abajo
  zona_produccion   text not null,
  anio_cosecha      int  not null,
  lote_padre_id     text references lote(id),   -- ← la genealogía
  semillero         text,
  nro_inscripcion   text,
  tratado_quimico   boolean default false,
  destino_presuntivo text,                 -- 'exportacion:VN' | 'mercado interno' | 'DEE'
  unique (semillero, variedad_id, subcategoria, zona_produccion, anio_cosecha, nro_lote)
);

-- Stock = saldo derivado de movimientos, nunca un número editable a mano.
-- Esto es lo que elimina el "conflicto de versiones" de la planilla.
create table movimiento (
  id              bigserial primary key,
  lote_id         text not null references lote(id),
  origen_id       text references ubicacion(id),      -- null = ingreso/cosecha
  destino_id      text references ubicacion(id),      -- null = egreso/despacho
  kg              numeric not null check (kg > 0),
  fecha           timestamptz not null default now(),
  usuario         text not null,
  fuente          text not null,           -- 'voz' | 'texto' | 'conteo' | 'importacion'
  transcripcion   text,                    -- el audio original, para auditoría
  confianza       text,                    -- 'alta' | 'dudosa'  (del extractor)
  confirmado_por  text,                    -- nadie escribe sin confirmar
  nota            text,
  tipo            text,                    -- 'ingreso_tolva' | 'envio_frio' | 'retiro_frio' | ...
  tipo_vehiculo   text,                    -- 'tolva' | 'camion_bolsas'
  zona_planta     text,                    -- 'recepcion' | 'playa' (estación, no depósito)
  orden_carga_id  text,
  peso_bascula_kg numeric
);

-- Papel en el campo. A veces no hay señal. A veces sale sin remito.
-- kg_estimado es ámbar (pendiente de pesaje), no un error. Ver cadena-planta-papasud.md.
create table orden_carga (
  id              text primary key,
  lote_id         text not null references lote(id),
  campo_id        text not null references ubicacion(id),
  kg_estimado     numeric not null,
  pendiente_pesaje boolean default true,
  tipo_vehiculo   text not null,           -- 'tolva' | 'camion_bolsas'
  camion          text,
  chofer          text,
  canal           text default 'papel',
  sin_remito      boolean default false,
  temperatura_cosecha_c numeric,
  observaciones   text
);

-- Planilla de recepción: el camión entra a planta, la báscula pesa.
create table recepcion_planta (
  id               text primary key,
  orden_carga_id   text references orden_carga(id),
  movimiento_id    bigint references movimiento(id),
  zona_id          text not null references zona_planta(id),  -- siempre 'recepcion'
  peso_bascula_kg  numeric not null,
  kg_estimado      numeric,
  chofer           text,
  camion           text,
  tipo_vehiculo    text default 'tolva'
);

-- Conteo físico, separado de los movimientos: así se detecta la discrepancia.
create table conteo (
  id            bigserial primary key,
  lote_id       text not null references lote(id),
  ubicacion_id  text not null references ubicacion(id),
  kg_contado    numeric not null,
  fecha         timestamptz not null default now(),
  usuario       text not null
);
```

### El enum de subcategorías, en orden

```ts
// Versión CORREGIDA (Res. 245/98). Sin 'prefundacion'; terminal Certificada A/B.
// Confirmar la escalera exacta con Papasud antes de mostrarla en pantalla.
export const SUBCATEGORIAS = [
  // --- Categoría Básica ---
  'preinicial_0',    // in vitro
  'preinicial_I',    // minitubérculos
  'preinicial_II',
  'inicial_I',       // ← a campo desde acá
  'inicial_II',
  'inicial_III',
  'fundacion',
  // --- Categoría Certificada ---
  'registrada',      // ← Papasud vende G3 acá
  'certificada_A',
  'certificada_B',
] as const;

// Regla de linaje INASE: un lote sólo puede provenir de una subcategoría
// igual o superior (= índice menor o igual) a la propia.
// Implementar la REGLA; no citar número de artículo sin verificar.
export function linajeValido(padre: Subcategoria, hijo: Subcategoria) {
  return SUBCATEGORIAS.indexOf(padre) <= SUBCATEGORIAS.indexOf(hijo);
}
```

### Stock como vista derivada (no como celda editable)

```sql
create view stock as
select
  m.lote_id,
  u.id   as ubicacion_id,
  u.nombre as ubicacion,
  sum(case when m.destino_id = u.id then m.kg
           when m.origen_id  = u.id then -m.kg
           else 0 end) as kg_declarado
from movimiento m
join ubicacion u on u.id in (m.origen_id, m.destino_id)
group by m.lote_id, u.id, u.nombre
having sum(case when m.destino_id = u.id then m.kg
                when m.origen_id  = u.id then -m.kg
                else 0 end) <> 0;
```

**Por qué esto gana puntos con el jurado:** el problema que Papasud describe ("varias personas editan la planilla al mismo tiempo, errores de versión") **no se resuelve con IA — se resuelve con este modelo de datos.** La IA resuelve la *captura* (voz → movimiento estructurado). Decir eso explícitamente en la demo demuestra criterio de ingeniería, no solo uso de un LLM.

---

## Los tres chequeos que se pueden demostrar en vivo

Cada uno es una validación imposible en una planilla, y visualmente contundente en 5 minutos:

1. **Saldo negativo / stock insuficiente** — intentar despachar 500 kg cuando el saldo derivado da 480 → bloqueo, con el detalle de los movimientos que componen ese saldo. (Vertical 03 / N02, tal cual el brief lo pide.)
2. **Linaje inválido** — intentar registrar un lote `inicial_I` cuyo padre es de categoría inferior → rechazo por **regla de linaje INASE**, mostrada en la UI. ⚠️ Mostrar la *regla*, no un número de artículo, hasta verificarlo (ver la corrección al inicio de este documento). Es el detalle que separa "hicimos un CRUD con voz" de "entendimos el negocio fiscalizado".
3. **Discrepancia declarado vs. contado** — comparar `stock.kg_declarado` con el último `conteo.kg_contado`; si difieren, listar los movimientos candidatos (los que tienen `origen` registrado pero ningún movimiento espejo en `destino`, o los de `confianza = 'dudosa'`) y **dejar que el LLM redacte la hipótesis** sobre esa lista acotada — nunca sobre la base entera. Igual que el brief lo pide: *"un movimiento del 12/08 posiblemente no se registró en destino"*.

El patrón de los tres es el mismo, y es el de [[polpilot-reusable-assets]]: **el núcleo determinístico detecta y calcula; el LLM sólo narra.**

---

## Merma: lo que vuelve creíble el motor de discrepancias

Una papa **pierde peso en el frigorífico** por respiración y deshidratación. Eso es **merma legítima**, no un error de registro. Un sistema que marque toda diferencia como faltante **inventa robos donde hay biología**.

Y la merma **no es lineal**: entre el **55 % y el 70 % de la pérdida de toda la temporada ocurre en los primeros 30 días**. Un modelo de "tanto por ciento por mes" genera faltantes fantasma exactamente en los lotes recién ingresados — el peor lugar para equivocarse, porque son los que más se mueven.

```sql
-- Curva de merma por días de almacenamiento, no lineal.
-- Se calibra con los datos reales de Papasud; estos valores son placeholder.
create table merma_curva (
  dias_desde    int primary key,   -- 0, 30, 60, 90, 120...
  pct_acumulado numeric not null    -- 0, 4.5, 5.8, 6.6, 7.1...
);

-- La discrepancia real: declarado − merma esperada vs. contado.
create view discrepancia as
select
  s.lote_id,
  s.ubicacion_id,
  s.kg_declarado,
  c.kg_contado,
  m.pct_acumulado,
  s.kg_declarado * (1 - m.pct_acumulado/100)         as kg_esperado,
  c.kg_contado - s.kg_declarado * (1 - m.pct_acumulado/100) as delta,
  case
    when abs(c.kg_contado - s.kg_declarado * (1 - m.pct_acumulado/100))
         <= s.kg_declarado * 0.01 then 'dentro_de_merma'
    else 'excede_merma'
  end as clasificacion
from stock s
join conteo c on c.lote_id = s.lote_id and c.ubicacion_id = s.ubicacion_id
join merma_curva m on m.dias_desde = /* bucket de días de almacenamiento */ 0;
```

**El LLM sólo redacta la hipótesis cuando `clasificacion = 'excede_merma'`.** Esa condición es la que convierte una resta en un sistema que entiende el negocio.

Frase para la demo: **«no te aviso cuando la papa pierde peso; te aviso cuando pierde más peso del que debería».**

**Corolario que encaja con el color epistémico:** la normativa **admite cantidad indeterminable** para productos primarios (Anexo V), así que `kg estimado, pendiente de pesaje` es un **estado legítimo en ámbar**, no un error en rojo. Agregar `kg_estimado boolean` a `movimiento`.

## Unidades y documentos de tránsito — dos datos que delatan

- **Un bolsón son ~700 kg**, no 1.000 ni 1.250: la densidad de la papa lo topea bastante abajo de la capacidad nominal del envase. Sembrar los datos con 700 para que la aritmética cierre («20 bolsones» = 14 t).
- **La papa NO viaja con Carta de Porte / CTG** — eso es instrumento de granos. Se mueve con el **DTV-e** (Documento de Tránsito Vegetal electrónico, SENASA) más el **COT de ARBA a partir de 4.500 kg**, umbral que alcanza a prácticamente todo camión de Papasud. Nombrar Carta de Porte en la demo delata igual que decir DJVE.

## Vocabulario para sesgar el reconocimiento de voz

Cargar esta lista como *prompt/hint* del STT y como diccionario del fuzzy-matcher mejora mucho la transcripción en castellano rioplatense con jerga agronómica:

**Subcategorías:** preinicial, inicial, prefundación, fundación, registrada, certificada
**Variedades:** Spunta, Innovator, Atlantic, Daisy, Markies, Kennebec, Bintje
**Ubicaciones:** frigorífico, galpón, cámara, El Calafate, Tres Arroyos, Gonzales Chaves, San Cayetano, Balcarce, Otamendi, General Pueyrredón
**Operación:** lote, bolsón, envase, kilos, toneladas, remito, orden de carga, despacho, conteo, acondicionamiento, empaque, rótulo, semillero
**Agronómico:** tubérculo, minitubérculo, brote, dormición, curado, fungicida, aporque, riego, aspersión, helada, virosis, sarna, rizoctonia
**Organismos:** INASE, SENASA, INTA, APPASBA, FENAPP, ONPF, CONASE

> Nota práctica: el brief dice que Papasud entrega el "diccionario de insumos y dosis recomendadas" el día del evento. Esta lista es el andamio para arrancar **antes** de tenerlo, y se reemplaza/completa cuando llegue el asset real.
