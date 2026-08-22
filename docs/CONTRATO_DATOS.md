# Contrato de datos · Papasud

> **Para Agustín.** Esto es lo que la capa de consulta (`feat/cerebro-info`) espera leer.
> Está escrito antes de construir nada para que el importador y el cerebro apunten al
> mismo lugar. Si algo de acá no te cierra, cambialo y avisá — pero que lo cambiemos
> una vez, no dos.

## La regla que ordena todo

```
CAMPO → PIVOTE (A, B) → CUADRANTE (1..8) → LOTE
```

Un **LOTE es una superficie de campo inscripta en INASE**, no una partida de stock.
**Un lote tiene UNA sola variedad.** Puede haber muchos lotes de la misma variedad;
nunca dos variedades en un lote.

La planta de Mar del Plata tiene **báscula**: es donde nace el peso confiable.
**La venta sale de la PLANTA**, no del frigorífico.

```
LOTE ──→ PLANTA ──→ CLIENTE
  │        │  ↑
  │        ↓  │
  │      FRIGORÍFICO ──→ CLIENTE
  ├──────→ FRIGORÍFICO
  └──────→ CLIENTE
```

El tramo `PLANTA → FRIGORÍFICO → PLANTA → CLIENTE` es el circuito más común y el
que hoy peor se sigue. Tiene que existir como dos movimientos, no como uno.

---

## 1 · Movimiento (la unidad del sistema)

**Un remito tiene VARIAS filas.** El camión es la unidad, el lote es el detalle.
El remito 1008 del 30/03 trajo lote 225 *y* lote 230; el remito 654 trajo 222 *y* 224.
Esto no es un caso raro: es cómo funciona. El modelo lo soporta de entrada.

```jsonc
{
  "id": "MOV-2026-000123",              // estable entre corridas del importador
  "tipo": "envio_a_frio",               // ver tabla de tipos
  "remito": "807",                      // string · puede ser "s/remito"
  "remito_id": "envio_a_frio:807",      // agrupa las filas del mismo camión
  "fecha": "2026-02-16",                // ISO. null si la planilla no la trae

  "lote": "223",                        // string SIEMPRE (hay lotes "55 b", "g1", "L37B")
  "variedad": "agata",                  // minúscula, sin acentos
  "categoria": "inicial 2",             // null si no está declarada
  "calibre": "exportacion",             // exportacion|granel|sin chicas|recibo|null

  "bolsas": 512,                        // null si vino a granel
  "granel": false,                      // true en tolva / chasis / acoplado
  "kg": 26434,                          // int, kilos netos
  "kg_prom": 51.63,                     // kg por bolsa DE ESTA FILA. null si granel

  "origen":  { "tipo": "planta",      "id": "planta_mdp" },
  "destino": { "tipo": "frigorifico", "id": "dospanca"  },

  "transporte": "cerone",               // empresa
  "chofer": "sotelo",                   // null si no viene
  "dtv": "13244679-2",                  // null si falta · SIN el prefijo "dtv "

  "observaciones": "bolsa blanca-hilo rojo",
  "bolsa_color": "blanca",              // null si no se puede leer
  "hilo_color": "rojo",

  "fuente": {                           // ← NO ES OPCIONAL
    "archivo": "Planilla de movimientos 2026.xls",
    "solapa": "Env a Frio",
    "fila_excel": 5
  },
  "anomalias": ["categoria_con_basura"] // ids de la sección 4
}
```

`fuente` es obligatorio. Todo número que el sistema muestre tiene que poder abrirse
hasta la fila del Excel de la que salió. Es literal lo que pidieron los dueños.

### Tipos de movimiento (uno por solapa de la planilla)

| `tipo` | Solapa | Origen → Destino |
|---|---|---|
| `ingreso_tolva` | Ingreso Tolvas Santa Ana | lote → planta (a granel, pesa la báscula) |
| `ingreso_multiplicacion` | Ingreso Trevelin | lote → planta (categorías inicial 1/2/3) |
| `campo_a_frio` | De campo a Frío | lote → frigorífico (sin pasar por planta) |
| `envio_a_frio` | Env a Frio | planta → frigorífico |
| `retiro_de_frio` | Ret Frio | frigorífico → planta *(el retorno)* |
| `entrega_cliente` | Entregas a clientes 2026 | planta \| frigorífico \| lote → cliente |
| `movimiento_interno` | P.Chica, SP | entre ubicaciones propias |

**Ojo con `retiro_de_frio`:** la solapa trae `Origen` (el frigorífico) pero el destino
vive en texto libre dentro de `Observaciones / Destino` — *"a planta para trabajar"*,
*"a cecive para trabajar"*, *"A SASULA PARA REPASAR"*, *"paraguay"*. Hay que parsearlo
y, cuando no se pueda, dejar `destino: null` con la anomalía `destino_no_declarado`.
No lo adivines.

---

## 2 · Ubicaciones

Los frigoríficos son **subcontratados** — hay que trackear los movimientos por lugar
porque hay que pagarles. Estos son los que aparecen en los datos reales, no los del brief:

```jsonc
{ "id": "planta_mdp", "nombre": "Planta Mar del Plata", "tipo": "planta", "bascula": true }
{ "id": "galpon_mdp", "nombre": "Galpón Mar del Plata",  "tipo": "galpon" }

// frigoríficos subcontratados
"dospanca" · "pancani" · "sasula" (Balcarce) · "belmonte" · "cecive" · "frigopap" · "teramal"
```

`tipo` de un nodo: `lote` | `planta` | `galpon` | `frigorifico` | `cliente`.

## 3 · Entidades de campo

```jsonc
// campo
{ "id": "santa_ana", "nombre": "Santa Ana", "pivotes": ["A", "B"] }
// pivote → cuadrantes (del plano Santa Ana 2023)
{ "campo": "santa_ana", "pivote": "A", "cuadrantes": [1,2,3,4] }
{ "campo": "santa_ana", "pivote": "B", "cuadrantes": [5,6,7,8] }
// lote
{ "id": "223", "campo": "santa_ana", "pivote": "A", "cuadrante": 2,
  "variedad": "agata", "superficie_ha": 12.17, "campana": "2025/26" }
```

Campos: **Santa Ana, Marisol, Trevelin, Oriente** (+ *Pampa Chica*, que aparece en los
datos como origen de los lotes 50–53).

Del plano: Pivote A = L30, L35, L37, L38, L41–L45, L55 · Pivote B = L31–L34, L34B,
L36, L37B, L54, L71, L72B, L75, L77, L79.

**Si un lote no declara campo, `campo: null`.** Que se vea en "datos a corregir".
Inventar el campo de un lote es exactamente el error que vinimos a resolver.

---

## 4 · Anomalías — no las escondas, listalas

La planilla real está sucia y **eso es el argumento de venta**, no algo a tapar. Poder
abrir su Excel y decir *"esta columna dice Cliente y adentro hay un peso"* pega más
que cualquier explicación. Cada anomalía viaja con `fuente.fila_excel`.

| `id` | Qué es | Evidencia real |
|---|---|---|
| `lote_multivariedad` | El lote declara más de una variedad. **Rompe la regla dura.** | **8 de 106 lotes.** El lote 500 figura como *sagitta* (19 filas), *spunta* (1) y *atlantic* (4) |
| `columna_con_otro_dato` | La columna contiene algo que no es lo suyo | `Cliente` = `"49,87 kg"` (De campo a Frío) · `Categoría` = `"solo chasis"`, `"camara 2"`, `"vuelve al frio"`, `"56 BOLSONES"`, `"(lamb weston)"` |
| `dtv_en_columna_ajena` | Un DTV metido donde va otra cosa | `Categoría` = `"dtv 13796860-6"` (Env a Frio #51) |
| `sin_remito` | Movimiento sin número de remito | `"s/remito"` — **18 filas** en Ret Frio |
| `sin_dtv` | Movimiento sin DTV registrado | frecuente en Ingreso Tolvas |
| `dtv_repetido` | El mismo DTV en remitos distintos | `13587702-6` en remito 850 y 1025 |
| `kg_como_texto` | Kilos cargados como texto | `"29080 kg"` en la columna `Kg` de Ret Frio |
| `kg_prom_imposible` | kg/bolsa fuera de 45–56 **sin explicación en observaciones** | remito 734: **9 bolsas / 40.860 kg = 4.540 kg por bolsa** |
| `destino_no_declarado` | No se puede resolver el destino | `retiro_de_frio` sin destino parseable |
| `lote_sin_campo` | El lote no declara a qué campo pertenece | |

**Un detalle que importa:** `kg_prom_imposible` tiene que leer las observaciones antes
de disparar. El remito 829 lote 821 da 25 kg/bolsa, pero la observación dice
`"bolsa papasud x 25kg"` — es una bolsa distinta, no un error. Un detector que marca eso
como error pierde la confianza del que conoce la operación. **Marcar sólo lo que la
planilla no explica.**

---

## 5 · Muestras de pre-cosecha → qué calibre da cada lote

De `Muestras pre-cosecha`: la distribución de calibres por lote, medida en el campo
antes de cosechar. Sirve para decir si un lote **sirve** para un pedido, en vez de suponerlo.

```jsonc
{ "lote": "38", "campana": "2020",
  "distribucion_mm": { ">55": 0.127, "45-55": 0.714, "25-45": 0.140, "<25": 0.019 },
  "reparto": { "exportacion": 0.858, "sin_chicas": 0.130, "semillon": 0.012 },
  "rinde_kg_ha": 1148.98 }
```

## 6 · Bolsas ↔ kilos

**No hay constante.** El kg por bolsa va de **46,66 a 54,59** y es propio de cada fila.
Para convertir se usa el `kg_prom` real del lote (promedio ponderado por kilos de sus
movimientos), nunca un 50 fijo. Si preguntan en bolsas se responde en bolsas y se aclaran
los kilos.

## 7 · Lo que consume el cerebro

Alcanza con que el importador deje esto; el resto lo derivo yo:

```
data-papasud/real/movimientos.json   [ ...movimiento ]
data-papasud/real/lotes.json         [ ...lote ]
data-papasud/real/ubicaciones.json   [ ...ubicacion ]
data-papasud/real/anomalias.json     [ ...anomalia ]
data-papasud/real/muestras.json      [ ...muestra ]
```

**El stock nunca es un campo.** Se deriva del libro de movimientos. Lo calculo yo en
`core/disponibilidad.py`: por ubicación, por lote, por variedad y por calibre, separando
**comprometido** (pedidos abiertos) de **libre**. Tener no es lo mismo que poder vender.

---

*Escrito el 22/08/2026 desde la planilla real, el plano de Santa Ana y las muestras de
pre-cosecha. Rama `feat/cerebro-info`.*
