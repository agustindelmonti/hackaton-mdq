---
tags: [reference, compliance, papasud, hackathon, argentina]
---

# Documentación argentina de stock, traslado y facturación — referencia para el prototipo Papasud

> Alcance: **movimiento interno de stock, remitos, documentación de traslado doméstica, facturación e inventario**.
> Fuera de alcance (cubierto por otra investigación): certificado fitosanitario, factura proforma, certificado de origen, categorías de certificación de semilla INASE/SENASA.

## Cómo leer este documento

Cada afirmación fuerte está etiquetada:

- ✅ **VERIFICADO** — leído en la fuente citada.
- ⚠️ **PARCIAL** — respaldado por fuentes secundarias (blogs contables / docs de ERP), no por el texto normativo original.
- ❌ **NO VERIFICADO** — no lo pude confirmar en esta sesión. **No afirmar esto delante del sponsor.**

---

## 0. Resumen ejecutivo (lo que importa para el demo)

1. **El remito es obligatorio para TODO traslado de mercadería, incluso cuando no hay venta** — explícitamente incluye traslados entre establecimientos del mismo contribuyente. Esto es exactamente el caso Papasud (4 ubicaciones). ✅
2. **La letra del remito la determina la condición fiscal del EMISOR** — Papasud, responsable inscripto, emite **remito R**, también para mover papa entre sus plantas. **La única excepción** es el traslado *dentro de un mismo predio, polo o parque industrial*, que va con **X**. Muchos blogs dicen "remito X = movimiento interno": **confunden "mismo predio" con "misma empresa"** y un contador lo va a notar. ✅
3. **La Carta de Porte / CTG NO aplica a la papa.** Es un régimen de granos (cereales, oleaginosas, legumbres secas). Afirmar lo contrario sería el error más visible posible frente a un productor. ✅
4. **El documento de traslado específico de la papa es el DTV-e** (Documento de Tránsito Sanitario Vegetal electrónico, SENASA), obligatorio para el tránsito de papa, batata, ajo, cebolla y tubérculos andinos. Este es el "carta de porte de la papa". ✅
5. **Mar del Plata está en la Provincia de Buenos Aires ⇒ aplica el COT de ARBA** (Código de Operación de Traslado) cuando el traslado supera los umbrales de peso/valor. Un camión de papa supera holgadamente los 4.500 kg. ✅
6. **Factura E** es la de exportación; **A/B/C** son domésticas. El **CAE** es el código de autorización electrónica que ARCA devuelve por comprobante. ✅
7. Desde 2025 **el remito puede ser digital** (RG 5678/2025), pero **sigue requiriendo CAI**. ✅
8. **La merma NO es lineal: más del 50 % de la pérdida de toda la temporada ocurre en los primeros 30 días.** ~1-3 % el primer mes, ~0,5-1 %/mes después, ~5 % a los 5 meses, y **&gt;10 % es el umbral de problema**. Un sistema con un %/mes plano inventa faltantes donde no hay. ✅
9. **El bolsón de papa es de ~700 kg, no de 1.000.** Y la bolsa de **semilla es de 50 kg** mientras la de consumo es de **~20 kg**. ✅
10. **En Argentina la papa se comercializa POR BOLSA, no por peso** — y el peso real de la bolsa derivó a la baja con los años. La industria, en cambio, compra **por kilo neto con deducciones** y descarta papa &lt;50 mm. **Papasud vive en los dos sistemas a la vez, y la planilla sólo puede guardar uno.** ✅

**Punchline para el pitch:** hoy Papasud emite un remito por cada traslado entre sus 4 plantas, y cada uno de esos remitos es un movimiento de stock que la planilla compartida no está registrando de forma confiable. El sistema no "agrega" un documento nuevo: **hace que el documento que ya emiten sea la fuente de verdad del stock.**

**Segunda punchline, para el feature de hipótesis:** *"La diferencia entre lo declarado y lo contado casi nunca es una sola cosa. Es merma esperada más un error de registro, mezclados. Nuestro sistema los separa: te dice cuánto explica la merma y cuánto no — y lo que no explica, lo rastrea hasta el remito que lo causó."*

---

## 1. El remito

### 1.1 Qué es legalmente

El marco es la **RG (AFIP) 1415/2003**, "Facturación y Registración". El artículo clave:

> **Art. 27** — "Todo traslado y entrega de productos primarios o manufacturados estará documentado mediante factura, remito, guía o documento equivalente, **aun cuando se trate de traslados o entregas que se realicen a un título distinto de la compraventa**."
> ✅ [RG 1415/2003, texto completo](https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-1415-2003-81316/texto)

Consecuencias directas para el modelo de datos:

- El remito **no es un documento de venta**. Es un documento de **traslado**. Un traslado sin venta (consignación, muestras, depósito, **movimiento entre sucursales/establecimientos propios**) igual lo requiere. ✅
- Debe emitirse **antes** de que la mercadería se mueva, y **acompañar** la mercadería hasta destino. ✅
- El duplicado se conserva **2 años**. ✅
- Lleva la leyenda **"DOCUMENTO NO VALIDO COMO FACTURA"** (Art. 28). ✅

### 1.2 ¿Es un documento controlado por AFIP/ARCA?

Sí, pero con un mecanismo distinto al de la factura electrónica:

| | Factura electrónica | Remito preimpreso |
|---|---|---|
| Autorización | **CAE** — Código de Autorización **Electrónica**, se pide por comprobante, online | **CAI** — Código de Autorización de **Impresión**, se pide por *talonario* a la imprenta habilitada |
| Momento | Al emitir | Antes de imprimir el talonario |
| Vencimiento | Vencimiento del CAE | Vencimiento del CAI del talonario |

- El remito es un **talonario preimpreso con CAI**, no un comprobante con CAE. **✅ VERIFICADO**: el Anexo V, ap. I.a, pto. 12 exige *"Código de autorización de impresión, precedido de la sigla 'CAI N° …'"*, y el pto. 13 su fecha de vencimiento.
- **Sólo el remito "R" lleva CAI.** El remito "X" está exento de los puntos 7, 10, 11, 12 y 13 — es decir, **sin CAI, sin vencimiento y sin datos de imprenta**. ✅
- El CAI **sigue siendo obligatorio incluso en la modalidad digital**. Textual de la RG 5678/2025: *"La representación gráfica en formato digital de los remitos **no exime** la obligación de efectuar la solicitud del Código de Autorización de Impresión (CAI)."* ✅ [Boletín Oficial 22/04/2025](https://www.boletinoficial.gob.ar/detalleAviso/primera/324239/20250422)
- ⚠️ Varios blogs comerciales afirman que "el remito R lleva CAE". **Es falso.** El remito lleva **CAI**; la factura electrónica lleva **CAE**. Si el demo muestra un campo de autorización, etiquetalo correctamente — es un detalle chico que transmite mucha credibilidad, y el error inverso es muy visible para un contador.

### 1.3 La letra: R vs X — el punto que casi todos entienden mal

Texto literal del **Art. 28** ✅:

> "a) De tratarse de responsables inscritos en el impuesto al valor agregado: la letra **'R'**. **Cuando utilicen remitos para respaldar el traslado y/o entrega de productos dentro de un mismo predio, polo o parque industrial, dichos documentos estarán identificados con la letra 'X'.** […]
> b) De tratarse de responsables no inscritos, exentos o no alcanzados, en el impuesto al valor agregado o de pequeños contribuyentes inscritos en el Régimen Simplificado (Monotributo): la letra **'X'**. **Lo dispuesto en este inciso no será de aplicación para la documentación que respalda el traslado y/o entrega de productos dentro de un mismo predio, polo o parque industrial.**"
>
> ✅ [RG 1415/2003](https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-1415-2003-81316/texto)

**La regla real, en dos líneas:**

1. La letra la determina la **condición de IVA del emisor**: responsable inscripto → **R**; no inscripto / exento / monotributo → **X**.
2. **Única excepción:** el traslado **dentro de un mismo predio, polo o parque industrial** va con **X**, sea quien sea el emisor.

**Aplicado a Papasud** (responsable inscripto — exporta y factura a PepsiCo):

| Movimiento | Letra |
|---|---|
| Entre dos ubicaciones en **domicilios distintos** (Balcarce ↔ Mar del Plata ↔ Tandil) | **R** |
| Entre dos galpones **dentro del mismo predio** (ej. Cámara 1 → Cámara 2 de la misma planta) | **X** |
| Venta a cliente | **R** |

> 🎯 Esto es matizado y **es exactamente el matiz que hace la diferencia en la sala**. La afirmación cruda "la letra nunca depende de si el movimiento es interno" es **incorrecta**: sí depende, pero el criterio no es "interno vs externo" sino **"mismo predio vs domicilios distintos"**. Con 4 ubicaciones físicas separadas, el grueso de los traslados internos de Papasud es **remito R**; sólo los movimientos intra-planta son X.

Confirmación en fuente secundaria, redactada justo para este caso: *"si la mercadería se traslada entre dos locales o depósitos ubicados en domicilios diferentes, corresponde utilizar **Remito R**, aunque ambos establecimientos pertenezcan al mismo contribuyente."* — [MyContador — Remito digital en ARCA](https://blog.mycontador.com.ar/remito-digital-en-arca) ⚠️

> ⚠️ **Cuidado con fuentes comerciales:** [Dux](https://duxsoftware.com.ar/blog/que-es-un-remito-argentina) y [YoFacturo](https://yo-facturo.com/blog/remito-electronico-afip/) afirman que "el remito X es el interno, sin valor fiscal". Es una **simplificación errónea**: confunden "mismo predio" con "misma empresa". No repitas esa versión.

**Implicación de modelado:** la letra es **derivable**, no un campo que el usuario elige:

```
letra = (ubicacion_origen.establecimiento = ubicacion_destino.establecimiento) ? 'X' : 'R'
```

…asumiendo emisor responsable inscripto. Que el sistema **calcule la letra sola** es un detalle chico y muy vendible: es precisamente el tipo de regla que en una planilla se equivoca.

### 1.4 Remito de venta vs remito de traslado entre establecimientos propios

Ambos son remitos R para Papasud. La diferencia está en el **contenido**, no en la clase:

| | Remito de venta / entrega a cliente | Remito de traslado interno (mismo CUIT) |
|---|---|---|
| Destinatario | Cliente (CUIT distinto) | **El mismo contribuyente**, otro establecimiento |
| Contraparte fiscal | Sí — se vincula a una factura | No hay venta, no hay factura asociada |
| Valor / precio | Suele consignarse o vincularse a la factura | **Sin valor** ✅ (ver 1.4.1) |
| Efecto en stock | **Baja** en origen | **Baja** en origen **+ alta** en destino |
| Riesgo operativo | Bajo (el cliente reclama si falta) | **Alto** — nadie reclama si el alta en destino nunca se registra |

Esa última fila es el corazón del problema de Papasud: **el traslado interno es el movimiento con menor control natural y mayor volumen diario.**

#### 1.4.1 Confirmación en fuente primaria del caso "mismo CUIT en las dos puntas" ✅

El **Instructivo COT de ARBA** confirma, en texto oficial, dos cosas que valen oro para el modelo de datos:

> **Sobre el traslado entre depósitos propios:**
> *"Aclaración: Para el transporte de bienes **entre depósitos de una misma empresa**, deberás ingresar al sistema bajo la opción **'Emisor de la documentación prevista en la RG 1415 AFIP'**."*

⇒ El traslado entre depósitos propios **es** un traslado documentado bajo la RG 1415. No es un "movimiento interno informal": es un remito. ✅

> **Sobre el importe:**
> *"**Importe**: campo obligatorio (mayor a cero) **siempre, excepto**: · Operaciones con **igual CUIT origen y CUIT destino** · Tratándose del transporte de productos no terminados/devoluciones."*

⇒ Cuando el CUIT de origen y el de destino son el **mismo**, el importe **no se informa**. Esto confirma normativamente el "remito sin valor" para traslados propios. ✅

Fuente: [ARBA — Instructivo COT (PDF)](https://www.arba.gov.ar/archivos/Publicaciones/Instructivo%20COT.pdf)

**Implicación de modelado:** `documento.es_traslado_propio = (cuit_origen = cuit_destino)`, y en ese caso `importe_total` queda **null** — no en cero, en null. Y la validación "importe obligatorio" debe desactivarse exactamente en ese caso. Es una regla de negocio real, tomada de un formulario del Estado.

### 1.5 Campos del remito

**Art. 29** remite al **Anexo V** de la RG 1415 para los datos mínimos. **Art. 30**: tamaño mínimo 15 cm × 20 cm (la modalidad digital queda exceptuada, RG 5678/2025 ✅).

Lista **✅ VERIFICADA** — texto completo del Anexo V, *"Datos que deben contener los remitos, las guías o documentos equivalentes"*, incluyendo la modificación de la RG 1697/04.
Fuente: [RG AFIP 1415/03 — Anexo V, Biblioteca electrónica CPCECABA](https://archivo.consejo.org.ar/Bib_elect/diciembre04_CT/documentos/rafip1415anexoV.htm)

#### I. Respecto del emisor y del comprobante

**a) Datos preimpresos:**

1. Apellido y nombres, denominación o razón social
2. Domicilio comercial
3. C.U.I.T.
4. Número de inscripción de **Ingresos Brutos** o condición de no contribuyente
5. Leyenda de condición IVA: `"I.V.A. responsable inscripto"` · `"I.V.A. exento"` · `"No responsable I.V.A."` · `"Responsable monotributo"` · `"Pequeño contribuyente eventual"` · `"Monotributista social"` · `"Pequeño contribuyente eventual social"`
6. **Numeración consecutiva y progresiva, de doce dígitos**
7. **Fecha de inicio de actividades** en el local o establecimiento / puntos de venta habilitados 🅁
8. Las letras **"R"** o **"X"**, según corresponda
9. Leyenda **`"Documento no válido como factura"`**
10. Apellido y nombres / razón social y **C.U.I.T. de la imprenta**, y fecha de impresión 🅁
11. **Primero y último número** de los documentos comprendidos en la impresión, y **número de habilitación del establecimiento impresor** 🅁
12. **Código de autorización de impresión**, precedido de la sigla **`"CAI N° …"`** 🅁
13. **Fecha de vencimiento**, precedida de **`"Fecha de vto. …"`** 🅁

> 🅁 = **sólo exigidos en remitos clase "R"**. Textual: *"Los datos indicados en el inc. a), ptos. 7, 10, 11, 12 y 13, sólo serán para los remitos clase 'R'."* ⇒ **el remito X no lleva CAI ni vencimiento ni datos de imprenta.**

**b)** Las palabras **`"Original"`** y **`"Duplicado"`** *(dispensables en modalidad digital — RG 5678/2025)*
**c)** **Fecha de emisión**

#### II. Respecto del destinatario de los bienes

Varía **según la condición de IVA del destinatario**:

| Condición del destinatario | Datos exigidos |
|---|---|
| Responsable inscripto | Nombre/razón social, domicilio comercial, CUIT + leyenda `"I.V.A. responsable inscripto"` |
| Exento / no alcanzado | Los mismos 3 datos + `"No responsable I.V.A."` o `"I.V.A. exento"` |
| Monotributo | Los 3 datos + `"Responsable monotributo"` / `"Pequeño contribuyente eventual"` / `"Monotributista social"` / `"Pequeño contribuyente eventual social"` |
| Consumidor final | Leyenda `"A consumidor final"`; **si el importe ≥ $1.000**, además nombre, domicilio y CUIT/CUIL/CDI o DNI/pasaporte |
| No categorizado | Los 3 datos + `"Sujeto no categorizado"` |

*(El inciso de "responsable no inscripto" fue **eliminado** por la RG 1697/04.)*

#### III. Con relación a la operación efectuada — 🔑 clave para papa a granel

> "**Descripción, contenido y cantidad** de los bienes transportados. **Cuando por la modalidad operativa no sea posible determinar la cantidad de los productos primarios** (por ejemplo: cereales, leche, etc.), dicho requisito se entenderá cumplido **con la descripción y contenido** de los bienes transportados."

> 🎯 **Esto es oro para el modelo de datos.** La propia norma reconoce que en productos primarios **la cantidad exacta puede no ser determinable al momento del traslado** — que es literalmente el caso de un camión de papa a granel que se pesa en destino. Justifica que el sistema tenga un estado **"cantidad estimada, pendiente de pesaje"** y que la discrepancia declarado-vs-contado sea **normal y esperada**, no una anomalía. Si en el pitch decís *"la propia RG 1415 contempla que en productos primarios la cantidad no siempre se puede determinar al cargar"*, ganás la sala.

#### IV. Con relación al transportista — ⚠️ menos de lo que uno supone

> "Apellido y nombres, denominación o razón social, domicilio comercial y C.U.I.T. de la empresa transportista. La información referida deberá cumplirse **sólo cuando el traslado de productos primarios o manufacturados se efectúe por terceros**."

**Correcciones importantes — esto NO está en el Anexo V:**

- ❌ **Dominio / patente del vehículo y del acoplado: NO lo exige la RG 1415.** *(Sí lo exige el **COT de ARBA** — ver §2.3.1, donde está verificado como obligatorio para transporte propio. Es un requisito **provincial**, no nacional.)*
- ❌ **Lugar de origen y lugar de destino: NO son un campo exigido en sí.** Los únicos "lugares" de la norma son el **domicilio comercial del emisor** y el del destinatario. *(El COT sí exige domicilio de origen y de destino explícitamente.)*
- ❌ **Precio / importe: NO se exige.** El apartado III pide sólo descripción, contenido y cantidad. La única mención de un monto es el umbral de $1.000 para consumidor final.
- ❌ **Espacio para firma / conformidad de recepción: NO es un requisito de la norma.** Es práctica comercial universal (y muy buena idea para el sistema), pero no es obligación legal.
- ❌ Leyendas tipo **"TRASLADO DE MERCADERÍA PROPIA"**, "MOVIMIENTO INTERNO" o "sin valor comercial": **no figuran en la RG 1415**. Son práctica opcional.

> **Si Papasud transporta con camiones propios, los datos del transportista no son obligatorios en el remito** — pero el COT sí le va a pedir el dominio. Buen ejemplo de por qué conviene un solo evento de movimiento que alimente los dos documentos con sus reglas distintas.

#### V. Aclaraciones del Anexo V que importan al diseño

- **Punto 3** — el **domicilio comercial** es *"el correspondiente al lugar habilitado para el almacenamiento y despacho de bienes (depósitos, almacenes, etcétera)"*. ⇒ el domicilio del remito **es el de la ubicación física**, no el de la sede administrativa. Esto valida modelar el domicilio en `ubicacion`, no sólo en la empresa.
- **Punto 6.b** — 🔑 *"Cuando desde un mismo lugar físico (depósito, almacén, etc.) se realice la expedición de bienes por cualquier título (venta, consignación, muestras, **remisión entre fábricas y sucursales**, etc.), y en él haya dos o más puntos de emisión de remitos con distintos códigos identificatorios, **cada uno de ellos deberá utilizarse en forma independiente y exclusiva en función de la causa —transferencia o no de dominio— que da origen al traslado y entrega de los bienes**."*
  ⇒ **La norma separa los remitos de traslado interno de los de venta por punto de emisión, no por letra.** Es la manera correcta de segregarlos. Ver §3.1.
- **Punto 7** — datos exclusivos de clase "R" (ver arriba).
- **Punto 8** — los autoimpresores (RG 100/98) no consignan datos de imprenta ni primero/último número.
- **Punto 10** — **el destinatario está obligado a informar al emisor su CUIT y condición de IVA.**
- **Punto 11** — cambio de CUIT ⇒ renumerar **desde 00000001**; cambio de domicilio ⇒ se pueden usar los comprobantes viejos hasta **120 días corridos** con la leyenda `"Nuevo domicilio"`.

### 1.6 Remito digital y remito electrónico

**Remito digital (RG 5678/2025 — ARCA).** ✅ VERIFICADO en el Boletín Oficial del 22/04/2025:

- Habilita la **representación gráfica en formato digital** de los remitos emitidos por los sistemas del Art. 12 inc. b) — **quedan excluidos los controladores fiscales**.
- **El CAI sigue siendo obligatorio**: *"no exime la obligación de efectuar la solicitud del Código de Autorización de Impresión (CAI)"*.
- El tamaño mínimo de 15 × 20 cm del Art. 30 **"no será de observancia"** cuando se opta por la representación digital.
- Se mantiene la conservación del duplicado por **≥ 2 años**.
- Vigencia desde su publicación.

Fuente primaria: [Boletín Oficial — RG 5678/2025 (22/04/2025)](https://www.boletinoficial.gob.ar/detalleAviso/primera/324239/20250422)

⚠️ Detalles que aparecen en fuentes secundarias pero **no** confirmé en el texto oficial: que se pueda prescindir de las leyendas "ORIGINAL"/"DUPLICADO", y las vigencias de **15 días corridos** (remito digital) y **45 días** ("resumen de datos"). Tratalos como plausibles, no los afirmes con seguridad.
Fuentes secundarias: [Estudio Noya](https://noya.com.ar/categoria-consultoria-de-empresas/revision-de-la-resolucion-general-5678-2025-de-a-r-c-a-modificacion-a-la-rg-1415-2003-sobre-documentacion-de-traslado/) · [BAE Negocios](https://www.baenegocios.com/economia/ARCA-como-hacer-un-remito-digital-para-el-traslado-de-mercaderia-20250422-0025.html)

**¿Hay un régimen de remito electrónico obligatorio que alcance a la papa?**

- **No encontré ninguno.** Los regímenes de "Remito Electrónico" en Argentina son **sectoriales**, no generales. El más conocido es el **Remito Electrónico Cárnico** (carne bovina). ⚠️
- ❌ **NO VERIFICADO:** la existencia/vigencia de regímenes de remito electrónico para **harina de trigo** y **azúcar**, y sus números de resolución. Los tengo en memoria pero no los pude confirmar en esta sesión — **no los menciones con número de RG.**
- ✅ **Conclusión utilizable:** *"No existe, al día de hoy, un régimen de remito electrónico obligatorio que alcance a papa, hortalizas o semilla. El remito de papa sigue siendo talonario con CAI, ahora opcionalmente digital."* Esta es la afirmación segura y es la que te conviene decir.

### 1.7 Regla especial útil: Art. 33

> **Art. 33** — el **comprador** de productos agropecuarios puede emitir él mismo el remito.
> ✅ [RG 1415/2003](https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-1415-2003-81316/texto)

Relevante si Papasud recibe papa de terceros (productores asociados, arrendatarios): el remito de ingreso puede ser emitido por Papasud. Justifica un flujo de **"remito de recepción"** en el sistema.

---

## 2. Documentación de transporte agrícola: qué aplica y qué NO

Esta es la sección donde un error se paga caro. Resultado: **tres documentos, uno no aplica y dos sí.**

### 2.1 Carta de Porte / CTG — ❌ NO aplica a la papa

La **Carta de Porte Electrónica (CPE)** con su **CTG (Código de Trazabilidad de Granos)** es un régimen **específico de granos**:

> "el único documento válido para respaldar el traslado de **granos no destinados a la siembra —cereales y oleaginosos— y de legumbres secas**"

Alcance: cereales y oleaginosas no destinados a siembra, legumbres secas (porotos, arvejas, lentejas) y semillas de esas especies. **La papa y las hortalizas no están comprendidas.** ✅

- Régimen actual: RG Conjunta AFIP/ARCA + Secretaría de Agricultura + Ministerio de Transporte, **RG 5017/2021** y modificatorias. ⚠️ (el número lo vi en fuentes secundarias, no en el B.O.)
- **La papa es un tubérculo hortícola, no un grano.** No hay CTG para la papa, ni para la papa semilla.

> 🗣️ **Cómo decirlo en la sala:** *"La carta de porte y el CTG no los tocamos porque son de granos; para papa el documento sanitario de tránsito es el DTV."* Esto demuestra que investigaste el dominio real y no copiaste un template de agtech de soja.

### 2.2 DTV-e — ✅ SÍ aplica, y es el documento clave de la papa

El **DTV-e** (Documento de Tránsito Sanitario Vegetal electrónico), de **SENASA**, es el documento que autoriza el tránsito de productos de origen vegetal.

- **Obligatorio para el traslado en fresco de raíces, bulbos y tubérculos** con destino a consumo e industrialización. Productos alcanzados incluyen **papa**, batata, ajo, cebolla y tubérculos andinos (papa andina, oca, olluco, mashua). ✅
- Obligatoriedad establecida por SENASA, con entrada en vigencia a fines de **2018** (120 días desde el anuncio de junio de 2018). ✅
- Debe **generarse antes del tránsito**, **acompañar** la mercadería durante todo el trayecto y tener **todos los campos completos**. ⚠️
- Se emite por el sistema **SIGDTV** (Sistema Integrado de Gestión del DTV). ⚠️
- Lleva un código de validación electrónica, **CUVE**, verificable (incluso por QR). ⚠️
- Función declarada: **trazabilidad** — identificación del producto, **origen** y **destino final**. ✅

Fuentes: [Mercado Central — obligatoriedad del DTV para hortalizas pesadas](https://mercadocentral.gob.ar/news/ser%C3%A1-obligatorio-el-uso-del-dtv-para-el-traslado-de-hortalizas-pesadas)

> 🎯 **Oportunidad de producto enorme:** el DTV-e exige **origen y destino** por envío. Es literalmente un registro de movimiento de stock que Papasud ya está obligado a generar. Un sistema que emita el DTV-e y el remito **del mismo evento de movimiento** elimina la doble carga y hace que el stock se actualice solo. Si tu demo muestra "un movimiento → remito + DTV + actualización de stock", eso es el pitch.

> ⚠️ Ojo con el límite de alcance: la **certificación de semilla** (categorías, INASE, rótulos) la cubre la otra investigación. El DTV es **tránsito sanitario**, distinto de la certificación de semilla. No los mezcles.

### 2.3 COT (ARBA) — ✅ SÍ aplica, y Mar del Plata está en su jurisdicción

El **COT — Código de Operación de Traslado** es un régimen de la **Provincia de Buenos Aires (ARBA)**, no nacional. Debe obtenerse **antes** del traslado.

- **Umbrales**: se exige cuando los bienes tienen **peso ≥ 4.500 kg** **o** valor ≥ un monto que se actualiza (≈ **$7.220.557** en valores 2025). ✅ / ⚠️ (el monto se actualiza; tratalo como parámetro configurable)
- Se declaran, entre otros datos, el **importe total sin impuestos** y el **total de kilos** transportados. ✅
- Los bienes alcanzados se definen por **anexos** de la normativa de ARBA.
- ❌ **NO VERIFICADO:** si la **papa** figura nominalmente en el Anexo I o II del COT, y si hay exenciones para productos primarios. **No afirmes que la papa está o no está listada.** Lo seguro es el umbral de 4.500 kg.

Fuentes: [ARBA — Instructivo COT (PDF)](https://www.arba.gov.ar/archivos/Publicaciones/Instructivo%20COT.pdf) · [ARBA — Guía de trámites COT](https://www.arba.gov.ar/GuiaTramites/TramiteSeleccionado.asp)

#### 2.3.1 Campos del COT — verificados en el instructivo oficial ✅

Esta es la estructura real del formulario. Sirve como **plantilla de campos** para el modelo de datos, porque el Estado ya resolvió qué hace falta para describir un traslado:

**1. Carácter en virtud del cual se obtiene el COT**
- `Emisor de la documentación prevista en la RG 1415 AFIP` — el que emite factura/remito/guía. **Ésta es la opción para traslados entre depósitos propios.**
- `Destinatario / propietario de los bienes`

**2. Datos del emisor**
- CUIT
- **Domicilio de origen** del traslado: calle, número (o S/N°), localidad *(obligatorios)*; barrio, piso, depto *(opcionales)*
- **Tenedor (SÍ/NO)** — "SÍ" implica que el emisor **no** es el propietario de la mercadería (operador logístico, intermediario, faconier)
- **Entrega en domicilio de origen** (flag)

**3. Datos del transportista**
- Tipo de transporte: **propio** (CUIT lo pone el sistema) o **terceros** (CUIT distinto)
- Modalidad: vehículo automotor o tren
- **Dominio** del vehículo — *obligatorio* si el transporte es propio; **dominio del acoplado/jaula** opcional
- Si es tren, los dominios no aplican

**4. Tipo de recorrido**
- `Urbano` → localidad + principal avenida/calle
- `Rural` → principal ruta/autovía/autopista
- `Mixto` → ambos

**5. Fecha y distancia**
- Fecha de origen del viaje *(obligatoria)*, horario de salida *(opcional)*
- Distancia: `< 500 km` · `500–1000 km` · `> 1000 km`
- **Fecha estimada de entrega**, calculada automáticamente: transporte propio → día siguiente (<500 km), segundo día (500–1000 km), manual (>1000 km); transporte de terceros → **7 días**

**6. Datos del destinatario**
- CUIT *(obligatorio si no es consumidor final)*
- **Domicilio de destino** *(siempre obligatorio)*: calle, número, localidad
- **Tenedor (SÍ/NO)** del destinatario

**7. Datos de los productos — 🔑 el hallazgo más útil**
- **Código de Producto**: **6 posiciones**, las **2 primeras identifican el capítulo** (nomenclador descargable de ARBA)
- **Unidad de Medida de Nomenclador** + **Cantidad** *(entero mayor a cero)*
- **Descripción propia del producto**
- **Unidad de medida propia** — *"aquella unidad de medida utilizada por la empresa en sus registros"*
- **Cantidad propia**

> 🎯 **ARBA modela unidad doble: la del nomenclador y la propia de la empresa.** Es decir: un organismo del Estado ya reconoce que la empresa cuenta en *bolsones* mientras el nomenclador exige *kilos*, y pide **las dos**. Esto es la mejor justificación posible de la decisión de guardar `cantidad_kg` **y** `cantidad_bultos` en cada movimiento — y es una línea excelente para el pitch: *"no lo inventamos nosotros, el formulario de ARBA ya pide las dos unidades porque la confusión de unidades es un problema conocido."*

> ⚠️ **NO VERIFICADO:** el código de 6 dígitos concreto de la papa. Por la estructura del nomenclador (capítulo en las 2 primeras posiciones) y su correspondencia con la nomenclatura arancelaria, **es esperable** que la papa caiga en el **capítulo 07** (hortalizas), pero no lo confirmé. Para el demo, mostrá el campo con formato `07xxxx` y no afirmes el código exacto.

**8. Documentación respaldatoria asociada** (un comprobante por registro; hasta 8 en carga parcial)
- Tipo de comprobante *(si es "Documento Equivalente", se agrega campo "Especifique el tipo")*
- Número de comprobante
- Fecha de emisión
- Flag **"Producto no terminado / devolución"**
- **Importe** — obligatorio > 0, **excepto** igual CUIT origen y destino, o productos no terminados/devoluciones

**Carga parcial:** si al iniciar el viaje no se puede individualizar al destinatario, se informan productos y documentación, y los destinatarios se completan dentro de los **4 días corridos** posteriores al fin de la validez del código. ✅

> 🎯 Otra joya: **el COT admite "mercadería en tránsito con destinatario indeterminado"**. El propio régimen fiscal reconoce el estado "en tránsito sin destino confirmado" — exactamente el estado `en_transito` del modelo de datos, y exactamente el agujero del Escenario 1.

> 🎯 Un camión de papa pesa mucho más de 4.500 kg (un solo bolsón de 1.000 kg × 5 ya lo supera). En la práctica **casi todo traslado de Papasud requiere COT**. Modelalo como un campo `cot_numero` en el movimiento, y ahí tenés un tercer documento que sale del mismo evento.

### 2.4 Tabla resumen — qué documento por tipo de movimiento

| Movimiento | Remito | DTV-e | COT (ARBA) | Factura |
|---|---|---|---|---|
| Traslado entre 2 plantas propias, misma provincia | ✅ R, sin valor | ✅ | ✅ si ≥4.500 kg | ❌ |
| Venta a PepsiCo Argentina | ✅ R | ✅ | ✅ si ≥4.500 kg | ✅ A |
| Venta a productor (responsable inscripto) | ✅ R | ✅ | ✅ si ≥4.500 kg | ✅ A |
| Venta a consumidor final / monotributista | ✅ R | ✅ | ✅ si ≥4.500 kg | ✅ B |
| Exportación | ✅ R | ✅ + fitosanitario* | según ruta | ✅ **E** |
| Ingreso a cámara de frío desde campo propio | ✅ R (traslado interno) | ⚠️ según destino | ✅ si ≥4.500 kg | ❌ |

\* certificado fitosanitario = otra investigación.

---

## 3. Numeración y formatos

### 3.1 Numeración de comprobantes

Texto literal del **Anexo V, ap. V, pto. 4** ✅:

> "**Numeración consecutiva y progresiva:** tendrá **doce dígitos**, de los cuales:
> a) Los **cuatro primeros dígitos** —de izquierda a derecha— conforman el código que **identifica el lugar de emisión** del comprobante. Esta numeración será asignada en forma consecutiva y progresiva a cada uno de los lugares de emisión —centralizada o descentralizada— **desde el 0001 hasta el 9998**. Cuando en el lugar en que se realice la emisión de facturas o documentos equivalentes, también, se encuentre físicamente ubicado el depósito o almacén, **los códigos a asignarse podrán ser diferentes para ambos casos**.
> b) Los **ocho restantes** se asignarán al número del comprobante y **deberá comenzar desde el 00000001**. Esta obligación será observada en forma independiente por cada medio o punto de emisión habilitado."

Puntos firmes:

- **4 + 8 = 12 dígitos.** ✅
- Rango del punto de venta: **0001 a 9998** — el **9999 no es utilizable**. ✅
- Cada punto de emisión arranca en **00000001** y lleva su propia secuencia independiente. ✅
- ⚠️ El formato de presentación **`0001-00001234`** (con guion) es **convención de mercado**, no está en la norma: la norma sólo manda los 12 dígitos. Usalo tranquilo, pero no lo cites como requisito legal.

**¿Punto de venta por establecimiento o por medio de emisión? Las dos opciones son válidas — es opción del contribuyente** (Anexo V, ap. V, pto. 6) ✅:

- **(a)** asignar el código **exclusivamente a cada establecimiento o lugar físico (inmueble)**, repartiendo la numeración por lotes/cupos a cada vendedor o sección *(exige registros que identifiquen los lotes)*; o
- **(b)** asignar un código **a cada lugar o medio de emisión** (vendedor, sección, línea de productos, corredor), independientemente del inmueble.

La opción elegida se declara en el **F. 446/C**, con al menos **3 días hábiles de anticipación** antes de habilitar una sucursal, local o punto de venta (Art. 47). ✅

⇒ **Un punto de venta propio por establecimiento no es obligatorio, pero es una de las dos opciones expresamente previstas.** Presentalo como decisión de diseño respaldada por la norma, no como obligación.

**🔑 Y hay una regla que sí obliga a segregar** (Anexo V, ap. V, pto. 6.b):

> "…y en él haya dos o más puntos de emisión de remitos con distintos códigos identificatorios, **cada uno de ellos deberá utilizarse en forma independiente y exclusiva en función de la causa —transferencia o no de dominio— que da origen al traslado**."

⇒ Si en una misma planta se emiten remitos de **venta** (transferencia de dominio) y de **traslado interno** (sin transferencia de dominio), **deben ir por puntos de emisión distintos**.

**Decisión de diseño recomendada para el demo — punto de venta por ubicación × causa:**

```
Ventas / salidas con transferencia de dominio
  0001  Planta Balcarce
  0002  Cámara de frío Mar del Plata
  0003  Galpón campo Norte
  0004  Depósito Tandil

Traslados internos (sin transferencia de dominio)
  0101  Planta Balcarce
  0102  Cámara de frío Mar del Plata
  0103  Galpón campo Norte
  0104  Depósito Tandil
```

> 🎯 Esto es mejor que "un punto de venta por planta" y **está respaldado por el texto de la norma**. Y da un beneficio de demo enorme: **el número del remito dice, de un vistazo, de dónde salió y si fue venta o movimiento interno.** Un remito `0102-00000418` se lee como "traslado interno saliendo de Mar del Plata". Eso hace que la trazabilidad se vea, no se explique.

**Nota de ERP:** en Odoo, el "**libro unificado**" hace que los tipos de comprobante con la **misma letra compartan la secuencia** (Factura FA-A `0001-00000002`, Nota de Crédito NC-A `0001-00000003`). ✅ [Odoo — localización Argentina](https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/argentina.html)

**Punto de venta electrónico ≠ manual.** Para factura electrónica se exige un punto de venta **específico y distinto** de los usados en controladores fiscales, y los documentos de cada punto de venta deben mantener correlatividad. ✅ [ARCA — solicitud de autorización de factura electrónica](https://www.arca.gob.ar/fe/emision-autorizacion/solicitud-autorizacion.asp)
⚠️ **No existe** un rango numérico reservado del tipo "0001–0099 = manual": el requisito es sólo que los códigos sean distintos.

### 3.2 Numeración de lotes

❌ **NO VERIFICADO.** No encontré una convención normada ni un estándar de mercado para numerar lotes/partidas en el agro argentino. **No inventes una y la presentes como "el estándar argentino".**

Lo que sí es defendible: proponer una convención **legible por el operario**, que es lo que hacen estas empresas en la práctica. Sugerencia para el demo, presentada como *nuestra* convención:

```
LOTE = <CAMPAÑA>-<VARIEDAD>-<CATEGORÍA>-<SECUENCIA>
Ej.:   2526-SPU-G2-014
       │    │   │  └─ secuencial dentro de campaña
       │    │   └──── categoría de semilla
       │    └──────── variedad (Spunta)
       └───────────── campaña 2025/26
```

- La **campaña** en Argentina se escribe **`2025/26`** — barra simple, segundo año en dos dígitos. Es el uso consistente de la Bolsa de Comercio de Rosario, la Bolsa de Cereales y la prensa sectorial ("campaña 2025/26"). `2025-26` aparece ocasionalmente; **`2025/2026` no se usa**. ⚠️ PARCIAL (verificado en títulos y snippets de esas instituciones, sin lectura de página institucional completa). Un lote de papa semilla pertenece a una **campaña**, no a un año calendario — modelalo como campo propio, **no lo derives de la fecha**.
- ✅ Confirmado que **no existe** una convención de formato de número de lote normada en Argentina: las normas de semilla y alimentos exigen *un* identificador de lote pero **no prescriben formato** ("*número de lote*: combinación de números y/o letras distintivas que identifica unívocamente un lote"). Cualquier esquema es diseño propio.
- Variedades reales de papa en Argentina para datos de demo: **Spunta**, **Innovator**, **Atlantic**, **Kennebec**, **Daisy**, **Markies**. (Atlantic e Innovator son las típicas de industria/papa prefritas — coherente con PepsiCo.) ⚠️

---

## 4. Facturación electrónica — lo mínimo necesario

### 4.1 Letras de comprobante

| Letra | Emisor → Receptor | IVA | Uso |
|---|---|---|---|
| **A** | Responsable inscripto → Responsable inscripto | **Discriminado**; el receptor toma **crédito fiscal** | B2B doméstico — PepsiCo, productores inscriptos |
| **B** | Responsable inscripto → consumidor final / exento / monotributista | Incluido, **no discriminado** | B2C doméstico |
| **C** | Monotributista o exento → cualquiera | No aplica IVA | Emisor no inscripto |
| **M** | Caso especial de emisor nuevo / observado | Discriminado, con retenciones | Poco frecuente |
| **E** | **Exportación** | **Sin IVA** (exportación exenta / no gravada) | Ventas al exterior |

✅ La letra la determinan (a) el diario/punto de venta configurado y (b) **la condición fiscal del emisor y del receptor**. [Odoo — localización Argentina](https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/argentina.html)

Fuentes adicionales: [Factura A/B/C/E — YoFacturo](https://yo-facturo.com/docs/sales/invoices/) · [Diferencias factura A/B/C — declar.ar](https://declar.ar/blog/factura-a-b-c-diferencias/)

**Para Papasud:** ~70-75% del volumen va con **factura A** (PepsiCo, productores inscriptos) y el 25-30% exportado con **factura E**.

### 4.2 CAE

- **CAE = Código de Autorización Electrónica.** Lo otorga AFIP/ARCA **por comprobante**, al momento de emitir, vía web service. La emisión es **instantánea**. ✅
- Tiene **fecha de vencimiento**. ✅
- Sin CAE, el comprobante **no es válido**. Modelalo como `cae` + `cae_vencimiento`, ambos nullable hasta que se autoriza.
- Web services relevantes (útil si el demo simula la autorización): **`wsfev1`** para comprobantes A/B/C/M domésticos, **`wsfexv1`** para **exportación (factura E)**, `wsbfev1` para bonos fiscales. ✅ [Odoo](https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/argentina.html)

> Detalle de credibilidad barato y efectivo: en el demo, la factura tiene **CAE**; el remito tiene **CAI**. Dos códigos distintos, dos mecanismos distintos. Casi nadie lo hace bien.

### 4.3 Factura E — solo lo esencial

- Es el comprobante de **exportación**, y cubre **tanto bienes como servicios**. ✅ El web service WSFEX tiene un campo `tipoExpo` donde **`1` = "exportación definitiva de bienes"** y otros valores cubren servicios. Para Papasud (exporta papa) el valor es **`1`**.
- La emiten tanto responsables inscriptos como monotributistas que venden al exterior. ✅ [ARCA — comprobantes alcanzados](https://www.arca.gob.ar/derechos-de-exportacion-de-servicios/comprobantes-y-facturacion/comprobantes.asp)
- Se autoriza por **`wsfexv1`** (WSFEX), un web service **distinto** del doméstico `wsfev1`. ✅
- **Sin IVA** (exportación exenta / no gravada). ✅
- El **punto de venta de exportación se registra por separado** del doméstico. ✅

**Campos propios de la factura E** ✅ (verificados en la documentación del web service WSFEX; semántica de campos verificada ahí, no en el texto de la RG):

| Campo | Contenido |
|---|---|
| `tipoExpo` | `1` = exportación definitiva de **bienes** |
| `incoterms` | Código Incoterms (FOB, CIF, …) |
| `moneda` | Ej. `DOL` |
| `monedaCtz` | Cotización en ARS, **> 0** |
| `dstPais` | País de destino |
| `permisos` | **Permisos de embarque** — admitidos **sólo** cuando `tipoExpo = 1` (exportación de bienes) |
| `cae` / `caeFchVto` | CAE y su vencimiento (`AAAAMMDD`) |

Fuente: [Documentación WSFEX — emitir factura E](https://arca.api.com.ar/docs/wsfex/facturas)

> ⚠️ Es documentación de API de un tercero que refleja la especificación de ARCA; **no** abrí las RG de fondo (RG 2758/2010 para bienes, RG 3689/2014). La **otra investigación cubre documentación de exportación** — para la lista definitiva de campos de exportación, tomala de ahí. Lo que sí está firme acá es: **factura E = exportación, `tipoExpo = 1` para bienes, y el permiso de embarque va sólo en exportación de bienes.**

---

## 5. Por qué el stock físico se separa del stock registrado

Esta sección es la materia prima del feature de "hipótesis de discrepancia". La clave conceptual:

> Un buen sistema **no** dice "hay una diferencia de 3.200 kg". Dice: **"de esos 3.200 kg, ~2.400 son merma esperada para 5 meses de cámara; los otros ~800 no tienen explicación y coinciden con el remito 0002-00000418, que registró la baja en Mar del Plata pero nunca el alta en Balcarce."**

Separar **merma esperada** de **error** es la diferencia entre una planilla con colores y un sistema.

### 5.1 Causas de tipo "error de registro" (el sistema puede detectarlas)

| Causa | Firma detectable en los datos |
|---|---|
| **Movimiento registrado en origen pero no en destino** | Existe baja sin alta correlativa; el remito tiene destino pero no recepción confirmada |
| **Remito contado dos veces** | Dos movimientos con el mismo `numero_documento`, o dos altas para un mismo remito |
| **Traslado en tránsito al momento del corte** | El camión salió el 30 y llegó el 1; el stock existe pero no está en ninguna ubicación física |
| **Confusión de unidad de medida** | Cantidad que, dividida o multiplicada por el peso nominal del envase, cierra exactamente |
| **Peso nominal vs peso real del envase** | Diferencia proporcional al número de bultos, siempre del mismo signo |
| **Devolución no registrada** | Cliente devuelve mercadería; entra físicamente sin documento |
| **Movimiento cargado en la ubicación equivocada** | Faltante en una ubicación y sobrante del mismo lote/cantidad en otra — se cancelan al sumar |
| **Reclasificación de categoría/calibre no registrada** | El lote "desaparece" de una categoría y "aparece" en otra |
| **Error de tipeo / transposición de dígitos** | Diferencia igual a la de dos dígitos permutados (ej. 1.800 vs 8.100) |

### 5.2 Causas de tipo "merma real" (el sistema debe esperarlas, no alarmarse)

- **Deshidratación / transpiración**: el tubérculo pierde agua durante todo el almacenamiento. Es la componente más grande y la más predecible.
- **Respiración**: pérdida de materia seca; el tubérculo sigue vivo.
- **Brotación**: en papa **semilla** la brotación es deseable al final del ciclo, pero consume reservas y hace perder peso. En papa de consumo/industria se combate.
- **Pudriciones / podredumbres**: pérdida localizada, no lineal; suele aparecer concentrada en bultos o sectores.
- **Descarte / culling durante la clasificación**: al acondicionar y calibrar se descarta tubérculo fuera de calibre, verdeado, dañado o enfermo. **Esto no es merma de almacenamiento, es rendimiento de proceso**, y conviene modelarlo aparte.

> **Distinción de modelado importante:** la merma de almacenamiento es **función del tiempo y la temperatura**; el descarte de clasificación es **función del evento de acondicionamiento**. Si los mezclás en un solo "ajuste", perdés la capacidad de explicar nada.

### 5.3 Cifras de merma

Esta sección **sí quedó verificada en fuentes argentinas citables**. Es material de primera calidad para el feature de hipótesis.

#### La curva de merma: NO es lineal — el primer mes es mucho peor

Este es el hallazgo más importante y el que más diferencia un buen sistema de una regla de tres.

**Respiración** (pérdida de materia seca), UNLP ✅:
> *"pérdidas de peso durante el almacenamiento del orden del **1-2 % del peso fresco durante el primer mes**, y varían luego a razón del **1,5 % por mes cuando los tubérculos comienzan a brotar**."*

**Evaporación + respiración** en tubérculos inmaduros, UNLP ✅:
> *"pierden del **3 al 5 % de su peso original** (evaporación y respiración) durante el primer mes… y luego estos valores descienden a **0,5 – 3 % por cada mes subsiguiente** siempre que los tubérculos no broten."*

Corroboración internacional (CIP) ✅ — el origen de las cifras anteriores:
> *"approximately **1 % to 2 % of fresh weight during the first month** and about **0.8 percent per month thereafter**, but rising to about **1.5 percent per month when sprouting is well advanced**."*

Y la confirmación más contundente de la no-linealidad (fuente no argentina) ✅:
> *"about **3 percent weight loss was seen in the first month**… **Total weight loss after five months was about 5 percent**… **55 to 70 percent of the total weight loss occurred in the first 30 days**."*

> 🎯 **Más de la mitad de la merma de toda la temporada ocurre en los primeros 30 días.** Un sistema que use un % mensual plano va a **sobrestimar** la merma de los lotes viejos y **subestimar** la de los recién ingresados — es decir, va a inventar faltantes donde no hay y a esconder faltantes reales. Modelar la curva (tramo inicial alto + tramo posterior bajo) es una decisión técnica con impacto operativo directo, y es un punto excelente para el pitch.

#### Cifras de referencia verificadas

| Concepto | Cifra | Fuente |
|---|---|---|
| Primer mes (maduro, buen manejo) | **1 – 3 %** | UNLP / CIP / Potato Grower ✅ |
| Primer mes (inmaduro o dañado) | **3 – 5 %** | UNLP ✅ |
| Meses subsiguientes, sin brotación | **0,5 – 1 % / mes** | CIP (0,8 %) / UNLP ✅ |
| Meses subsiguientes, **con brotación avanzada** | **~1,5 % / mes** | UNLP / CIP ✅ |
| **Total a 5 meses**, cámara bien manejada | **~5 %** | Potato Grower ✅ |
| **Total temporada larga**, buen almacén refrigerado | **~8 %** | CIP ✅ |
| Almacén ambiente / tiro forzado | **~15 %** | CIP ✅ |
| **Pila tradicional a campo** (Spunta/Kennebec, Argentina) | **&gt; 30 %** | UCA ✅ |
| Kennebec, ~161 días (5,3 meses), depósito **no refrigerado** argentino | **7,76 % – 7,91 %** | Ordóñez et al., FAUBA ✅ |
| **Umbral de problema** (aspecto/comerciabilidad) | **&gt; 10 %** | CIP ✅ |
| Pérdida de calidad / descarte, incluso con buen manejo | **5 – 15 %** | CIP ✅ |

**Temperaturas de almacenamiento — verificadas, y confirman el contraste semilla vs industria:**

| Destino | Temperatura | Fuente |
|---|---|---|
| **Papa semilla** | **4 – 5 °C** (UNLP) · **4 °C y 90 % HR** (UCA) · **2 – 4 °C** largo plazo (CIP) | ✅ |
| **Industria** | **8 – 9 °C** (UNLP) · **&gt; 10 °C** (FAUBA) · **7 – 8 °C** largo plazo (CIP) | ✅ |
| **Consumo** | **10 °C** (UCA) · **4 – 7 °C** largo plazo (CIP) | ✅ |
| Mínimo absoluto | **no bajar de 3 °C** (sensibilidad al daño) | UNLP ✅ |
| Curado previo | **15 – 18 °C, 90 – 95 % HR, 2 – 3 semanas** (UNLP) · **18 °C, 95 % HR, 10 – 15 días** (UCA) | ✅ |
| HR de conservación | **&gt; 90 %** (típico 95 %) | ✅ |

> ⚠️ **Importante:** todas las cifras de %/mes provienen de papa de **consumo/industria**. **No encontré ninguna cifra de merma específica de papa semilla.** La semilla se guarda más fría (4 °C vs 8-10 °C), lo que por lógica de déficit de presión de vapor implica **menos** transpiración — pero eso es **inferencia, no dato**. Si en el demo mostrás un parámetro para semilla, marcalo como calibrable.

#### Mecanismos: qué domina y cuándo ✅

- **Transpiración / evaporación es el mecanismo dominante**, y sobre todo al principio: *"La evapotranspiración provoca las mayores pérdidas sobre todo en las primeras semanas posteriores a la cosecha"* (Ordóñez et al., FAUBA).
- Del agua perdida, **97,6 % transpira por la piel** y **2,4 % sale por las lenticelas** junto con el CO₂ de la respiración (U. Idaho, citando Burton 1989).
- **La brotación es la principal causa de pérdida** en papa de consumo e industria (UNLP) — doblemente: descarta tubérculos comerciables y los brotes evaporan agua. Cada **1 % en peso de brotes agrega 0,07 – 0,1 %/semana/mbar** de pérdida evaporativa (CIP).
- **Tubérculos inmaduros o dañados pierden hasta el doble** de lo estimado (U. Idaho).
- El **envase influye**: pérdida en **bolsa de red (arpillera) &gt; bolsa de papel &gt; bandeja** (Ordóñez et al.).
- Composición: el tubérculo es **78 – 88 % agua** (U. Idaho).

#### Fórmula utilizable en el sistema — ASAE EP475.3 ✅

```
L = (A + 0,1 × S) × D
```
- `L` = % del peso original perdido **por semana**
- `A` = **0,7 las primeras dos semanas**, **0,2 el resto** ← acá está la no-linealidad, con respaldo normativo
- `S` = % de brotes en peso
- `D` = déficit de presión de vapor (mmHg)

Ejemplo trabajado (U. Idaho): sin brotación, 15 °C, 95 % HR → **0,45 %/semana** en las primeras dos semanas.
*Inferencia aritmética:* el resto de la temporada da 0,2 × 0,639 ≈ **0,13 %/semana ≈ 0,55 %/mes** — consistente con el rango de 5-10 % de temporada. Y "la pérdida puede ser **el doble** si la papa está inmadura o dañada".

> 🎯 **Esta fórmula es un regalo para el demo.** Es una norma de ingeniería (ASAE), tiene el quiebre de las dos semanas incorporado, y toma como entradas cosas que Papasud ya conoce o puede medir: temperatura, humedad y estado de brotación. Un sistema que calcula la merma esperada con EP475.3 en lugar de un porcentaje inventado es defendible ante cualquiera.

**Manejo (contexto útil para sonar competente):** mantener el **ΔT a través de la pila en 0,5 – 2,0 °F**; la HR de equilibrio (transpiración cero) sería **97,8 %** pero los almacenes operan a ~95 %; si la ventilación no extrae el CO₂ y el calor de respiración, la pila sube **~0,25 °C/día** (UNLP); el enfriamiento inicial va a **~1 °C/día** (UCA).

#### Lo que NO se encontró ❌

- **Ningún desglose porcentual argentino** entre transpiración / respiración / brotación / pudriciones / descarte. Los mecanismos están nombrados y **ordenados cualitativamente**, pero no cuantificados por separado.
- **Ninguna publicación de INTA Balcarce** con cifras de merma (el sitio y el repositorio de INTA no respondieron).
- **Ninguna cifra de merma específica de papa semilla.**
- El dato de **descarte del 40 %** que aparece en una tesis de FAUBA corresponde a **papa andina de autoconsumo en el NOA** — **no es una cifra comercial**, no la uses para Papasud.

#### Conceptos que siguen siendo la clave del diseño ✅

- El **descarte de clasificación** es un fenómeno de **evento** (el acondicionamiento), no de tiempo. Mezclarlo con la merma de almacenamiento destruye la capacidad explicativa del sistema.
- Las **pudriciones** son **no lineales y localizadas** — se concentran en bultos o sectores. Se detectan como *outlier por bulto*, no como desvío porcentual del lote. Y "la transpiración es el factor dominante **salvo que haya altos niveles de enfermedad**" (Potato Grower) ⇒ **si el desvío no sigue la curva de transpiración, sospechá enfermedad.** Esa es una hipótesis muy buena y muy específica.

**Aun así, no hardcodees porcentajes.** Usá la tabla `parametro_merma` con `pct_mensual_min`, `pct_mensual_max`, `temperatura_c` y un campo **`fuente`**. Así:

1. La merma esperada es **auditable**: el sistema puede mostrar *"esperado 3,8 % – 6,4 % según parámetro vigente desde 01/03/2026"*.
2. La conversación con el sponsor cambia de *"¿de dónde sacaste 0,8 %?"* a *"¿cuál es tu número?"* — y ese es exactamente el momento en que el sponsor se convierte en usuario.
3. **Frase para el pitch:** *"El sistema no adivina la merma: la calcula con un parámetro que ustedes calibran. Y separa lo que la merma explica de lo que no explica, que es lo único que hace falta investigar."*

> 🎯 Este es, honestamente, un mejor diseño que tener un número duro — y podés defenderlo con orgullo en lugar de disimular que no verificaste la cifra.

---

## 6. Unidades y envases de papa semilla

> 🚩 **Corrección importante respecto de lo que yo asumía.** Mi hipótesis inicial era "bolsón = 1.000–1.250 kg". **Es casi seguro incorrecto para papa.** Esos números son la **capacidad de carga nominal del envase** (dimensionada para materiales densos: grano, fertilizante, arena), no lo que entra de papa. La literatura agronómica argentina habla de **bolsones de 700 kg** para papa. Detalle abajo.

### 6.1 Envases — cifras verificadas

| Envase | Peso | Fuente |
|---|---|---|
| **Bolsón / big bag** para papa | **700 kg** | UCA ✅ |
| **Bolsa** papa **consumo / mercado fresco** | **~18 – 22 kg** (nominal "20 kg") | UCA · Argenpapa · prensa 2025 ✅ |
| **Bolsa** papa **SEMILLA** | **50 kg** | UCA ✅ |
| **Bin** agrícola estándar | **570 L → ~350 kg** de papa | bins.com.ar ✅ |
| **Bin** ventilado bajo (papa, cebolla, zanahoria) | **440 L → ~250-260 kg** *(inferencia por densidad)* | bins.com.ar ✅ / ⚠️ |
| **Cajón** de madera | **~20 kg** | bins.com.ar ✅ |
| **Canasto** de cosecha manual | **~20 kg** | UCA ✅ |
| Envases de góndola / retail | **2 – 4 kg** | UCA ✅ |
| Camión | **~30 toneladas** | UCA ✅ |

**Sobre el bolsón — por qué 700 y no 1.000** ✅/⚠️:
> *"el uso de **bolsones de 700 kg** favoreció la combinación de cosecha semimecánica y descarga en fábrica, evitando el costo de la bolsa. Un guinche o pluma es necesario para la carga y descarga de los bolsones."* — UCA

Los fabricantes argentinos ofrecen big bags "para contener cargas de **500, 800, 1000, 1250, 1500 kg** y más", pero eso es **resistencia estructural**, no contenido de papa. La densidad aparente de la papa es **~590 kg/m³** ⚠️ (fuente débil), así que un bolsón de 90×90×90 cm (0,73 m³) contiene **~430-480 kg** y uno de 1 m³ **~590-650 kg** — *inferencia mía*, y explica exactamente por qué la literatura dice 700 kg. **Para 1.000-1.250 kg de papa harían falta 1,7-2,1 m³.**

> 🗣️ **En la sala:** modelá el bolsón en **700 kg** y preguntá *"¿ustedes manejan bolsones de 700 u otro formato?"*. Preguntar con un número plausible de referencia es mucho mejor que afirmar 1.000.

**Semilla ≠ consumo en el envase:** la bolsa de semilla es de **50 kg**, la de consumo de **~20 kg**. Verificado con dos usos independientes en la tesis de UCA: *"un operario puede cortar unas **25-30 bolsas de 50 kg/día**"* y *"las **40 bolsas de papa semilla (50 kg)** que se destinan por hectárea"* (= 2.000 kg/ha de densidad de plantación). Como Papasud **es semillera**, su bolsa de referencia es la de **50 kg**.

⚠️ **No verificado:** bolsas de 20/25/30 kg **para semilla** — no encontré ninguna fuente argentina que las use.

### 6.2 🔑 El hallazgo más valioso: en Argentina la papa se comercializa POR BOLSA, no por peso

Textual, UCA ✅:
> *"Vale remarcar, que la **comercialización se suele realizar por bolsa y no por peso**"* — y en el mismo párrafo: el peso de la bolsa *"fue disminuyendo con el paso del tiempo"*.

Corroboración: Argenpapa y el MCBA cotizan la papa argentina en **$ por bolsa** (mientras cotizan otros países en $/kg, $/tonelada o U$S/cwt), y los análisis de costo del productor razonan enteramente en **$/bolsa**. La prensa de 2025 habla de *"la bolsa de 18 kilos"*. ✅

Y el contraste, también verificado ✅: **la industria no compra por bolsa** — compra por **peso neto con deducciones**, *"no pagándose por bolsas, defectos, tierra, enfermedades o papas muy pequeñas, menores a 50 mm"*, con bonificación/penalidad por materia seca. Contraste internacional: CIP dice que *"potatoes are sold **by weight**"* ⇒ **la convención de bolsa es una particularidad argentina del mercado fresco.**

> 🎯 **Esto es el corazón del problema de Papasud, y ahora está documentado.**
> - La **unidad de cuenta** es la bolsa, pero **su contenido real en kg se movió con el tiempo** ("fue disminuyendo") — es decir, el peso nominal es una **ficción histórica** que nadie actualizó. Exactamente la discrepancia nominal-vs-real que sospechábamos, confirmada en fuente argentina.
> - Papasud vive **con los dos sistemas a la vez**: vende a PepsiCo **por kilo neto con deducciones** y al mercado de semilla **por bolsa**. Un mismo lote se mide de dos maneras según a quién se le venda.
> - **Frase para el pitch:** *"En Argentina la papa se comercializa por bolsa, pero la industria la compra por kilo neto. Ustedes viven en los dos sistemas al mismo tiempo, y la planilla sólo puede guardar uno. Ahí nace la mitad de las diferencias."*

### 6.3 Calibre y gramaje de semilla ✅

- La semilla se elige por **gramaje**, no por milímetros: se compran *"semillas de entre **100 a 300 g**"* para que los cortes queden en **~50 g**; el "semillón" de tubérculo entero va de **30 a 60 g**. ✅ (UCA)
- La industria descarta papa **menor a 50 mm**. ✅
- Densidad de plantación de referencia: **2.000 kg/ha** (40 bolsas de 50 kg). ✅
- ⚠️ Los rangos de calibre tipo `35/55` y `55/75` mm que usé en el schema **no los verifiqué**; el criterio verificado para semilla es el **gramaje**. Considerá guardar **ambos**: `calibre_mm` y `gramaje_g`.

⇒ **Un mismo peso de semilla no equivale a la misma capacidad de siembra** según el gramaje. Razón concreta para guardar el gramaje en `lote`, y una buena pregunta para el sponsor.

### 6.4 Lo que NO se encontró ❌

- Ninguna fuente argentina que indique un bolsón de papa de **1.000 o 1.250 kg**.
- Ningún uso de una **"unidad de semilla"** formal para papa (a diferencia de maíz o girasol).
- Ninguna resolución de **INASE** sobre tamaño de envase o rotulado de papa semilla (los sitios de INASE/INTA no respondieron). *Nota: rotulado y certificación son alcance de la otra investigación.*
- Precios de **minitubérculos** por unidad.

### 6.5 Reglas de diseño que salen de esta sección

1. ✅ **El stock se cuenta de dos maneras a la vez**: por **bultos** (lo que ve el operario) y por **kilos** (lo que va en el remito, el COT y la factura). **Nunca son la misma medición** — y ARBA ya modela esta dualidad (§2.3.1).
2. ✅ **El peso nominal del envase no es el peso real**, y en Argentina está *documentado* que derivó en el tiempo. La diferencia nominal-vs-balanza es **proporcional al número de bultos y siempre del mismo signo** — firma detectable.
3. ✅ **La conversión bultos → kg es donde nace el error de unidad.** Si un movimiento guarda sólo kg, la información para detectarlo se perdió al cargar. De ahí `envase_id` + `kg_estimados`.
4. ✅ **Guardá el peso pesado y el peso nominal por separado.** Con papa se cobra por neto con deducciones (tierra, defectos): `peso_bruto_kg`, `peso_neto_kg` y `tara_kg` no son lujo.

> 🎯 **Regla de oro:** en cada movimiento guardá **siempre** `cantidad_bultos`, `envase_id`, `cantidad_kg` y `kg_estimados`. Con eso, toda discrepancia de unidad es aritmética verificable en lugar de misterio. **Sin eso, no hay feature de hipótesis.**

---

## 7. Vocabulario de conciliación de inventario (para la UI)

Terminología que un encargado de depósito argentino efectivamente usa. Usar esto en los labels es lo que hace que el sponsor sienta que el sistema es suyo.

| Término | Significado | Uso en la UI |
|---|---|---|
| **Recuento físico** / **conteo físico** | Contar la mercadería realmente presente | Botón "Iniciar recuento físico" |
| **Inventario cíclico** / **conteo cíclico** | Recontar una porción del stock de forma rotativa, sin parar la operación | "Inventario cíclico — lotes a contar hoy" |
| **Toma de inventario** | El acto/evento de inventariar | Nombre del evento en el historial |
| **Stock declarado** / **stock teórico** / **existencia según sistema** | Lo que dice el sistema | Columna "Declarado" |
| **Stock contado** / **existencia física** / **stock real** | Lo que se contó | Columna "Contado" |
| **Diferencia de inventario** | Declarado − contado | Columna "Diferencia" |
| **Faltante** | Contado **menor** que declarado | Chip rojo |
| **Sobrante** | Contado **mayor** que declarado | Chip azul |
| **Merma** | Pérdida esperada/natural (deshidratación, respiración) | "Merma estimada" — se explica, no se alarma |
| **Descarte** / **desecho** | Producto retirado por calidad | Movimiento tipo `descarte` |
| **Ajuste de inventario** | El asiento que corrige el sistema para igualar al recuento | Botón "Registrar ajuste" |
| **Acondicionamiento** / **clasificación** / **calibrado** | Preparar, seleccionar y separar por calibre | Proceso que consume un lote y produce otros |
| **Bulto** | Unidad de manipulación genérica (bolsa, bolsón, bin) | Unidad de conteo |
| **Partida** / **lote** | Conjunto homogéneo trazable | Entidad central |
| **En tránsito** | Salió de origen, no llegó a destino | Estado del movimiento |
| **Cámara** / **cámara de frío** / **frigorífico** | Almacenamiento refrigerado | Tipo de ubicación |
| **Galpón** / **depósito** / **planta** | Almacenamiento no refrigerado | Tipo de ubicación |
| **Remito de salida** / **de entrada** | Documento según sentido | Filtro de documentos |
| **Conformar** / **conformidad** | Que el destinatario acepte y firme la recepción | Botón "Conformar recepción" |
| **Trazabilidad** | Poder reconstruir origen y destino de un lote | Vista "Trazabilidad del lote" |

> 🗣️ Frases exactas que conviene poner en la UI: **"Faltante sin explicar"**, **"Merma esperada"**, **"Recepción pendiente de conformar"**, **"Remito bloqueado: stock verificado insuficiente"**.

---

## Modelo de datos sugerido

Postgres / Supabase. Nomenclatura de dominio en español (es lo que hace que el sponsor lea el schema y lo entienda), tipos y claves en inglés donde es convención técnica.

### Diagrama conceptual

```
variedad ─┐
          ├─< lote >─── existencia (lote × ubicación)  ← stock actual, materializado
categoria ┘     │
                └─< movimiento >─── documento (remito / DTV / COT / factura)
                        │
                        └─── recuento / ajuste
```

### Tablas

```sql
-- ─────────────────────────────────────────────
-- MAESTROS
-- ─────────────────────────────────────────────

create type tipo_ubicacion as enum (
  'camara_frio',      -- almacenamiento refrigerado
  'galpon',           -- depósito seco
  'packing',          -- planta de acondicionamiento
  'campo',            -- lote a campo / a granel
  'transito'          -- ubicación virtual: mercadería en viaje
);

create table ubicacion (
  id                uuid primary key default gen_random_uuid(),
  codigo            text not null unique,          -- 'BAL-CAM-01'
  nombre            text not null,                 -- 'Cámara 1 — Planta Balcarce'
  tipo              tipo_ubicacion not null,
  -- 'establecimiento' = predio físico. CLAVE: dos ubicaciones con el MISMO
  -- establecimiento están en el mismo predio ⇒ el remito entre ellas es letra X.
  establecimiento   text not null,                 -- 'Balcarce', 'Mar del Plata', 'Tandil'
  -- Anexo V ap.V pto.6.b: los remitos deben segregarse por CAUSA
  -- (transferencia de dominio o no) en puntos de emisión distintos.
  punto_venta_venta     int,                        -- 0001..9998  p.ej. 1
  punto_venta_traslado  int,                        -- p.ej. 101
  -- Anexo V ap.V pto.3: el domicilio comercial del remito es
  -- "el lugar habilitado para el almacenamiento y despacho de bienes"
  domicilio         text not null,
  localidad         text not null,
  provincia         text default 'Buenos Aires',
  temperatura_objetivo_c numeric(4,1),             -- 4.0 semilla / 8.0 industria
  refrigerada       boolean generated always as (tipo = 'camara_frio') stored,
  activa            boolean not null default true
);

create table variedad (
  id            uuid primary key default gen_random_uuid(),
  nombre        text not null unique,   -- 'Spunta', 'Innovator', 'Atlantic', 'Kennebec'
  destino       text                    -- 'semilla' | 'industria' | 'consumo'
);

-- Categoría de semilla: la maneja la otra investigación (INASE).
-- Acá sólo se referencia por código para no duplicar ni contradecir.
create table categoria_semilla (
  codigo        text primary key,       -- p.ej. 'G2', 'FISCALIZADA', 'IDENTIFICADA'
  descripcion   text,
  orden         int                     -- para ordenar de mayor a menor pureza
);

create type unidad_medida as enum ('kg', 'bolson', 'bolsa', 'bin', 'tonelada');

create table envase (
  id                 uuid primary key default gen_random_uuid(),
  nombre             text not null,
  unidad             unidad_medida not null,
  -- Peso DECLARADO del envase lleno. OJO: es una convención comercial que
  -- derivó en el tiempo ("fue disminuyendo con el paso del tiempo", UCA),
  -- NO una medición. De ahí que kg_estimados exista.
  peso_nominal_kg    numeric(10,2) not null,
  tara_kg            numeric(6,2) default 0,
  capacidad_litros   numeric(8,1),                -- bins: 440 L, 570 L
  activo             boolean not null default true
);

-- Valores verificados para papa en Argentina (ver §6.1):
insert into envase (nombre, unidad, peso_nominal_kg, capacidad_litros) values
  ('Bolsón (big bag) papa',      'bolson', 700,  null),
  ('Bolsa papa semilla',         'bolsa',   50,  null),
  ('Bolsa papa consumo',         'bolsa',   20,  null),
  ('Bin agrícola 570 L',         'bin',    350,  570),
  ('Bin ventilado bajo 440 L',   'bin',    255,  440),
  ('Cajón de madera',            'bolsa',   20,  null);

create table socio (                              -- clientes y proveedores
  id                    uuid primary key default gen_random_uuid(),
  razon_social          text not null,
  cuit                  text unique,
  condicion_iva         text not null,            -- 'responsable_inscripto' | 'monotributo' | 'exento' | 'consumidor_final'
  letra_comprobante     text generated always as (
                          case condicion_iva
                            when 'responsable_inscripto' then 'A'
                            else 'B'
                          end
                        ) stored,
  es_exterior           boolean not null default false,  -- true ⇒ factura E
  domicilio             text,
  pais                  text default 'AR'
);

-- ─────────────────────────────────────────────
-- LOTES Y EXISTENCIAS
-- ─────────────────────────────────────────────

create table lote (
  id                    uuid primary key default gen_random_uuid(),
  codigo                text not null unique,     -- '2526-SPU-G2-014'
  campania              text not null,            -- '2025/26'  ← NO derivar de la fecha
  variedad_id           uuid not null references variedad(id),
  categoria_codigo      text references categoria_semilla(codigo),
  calibre_mm            text,                     -- '35/55', '55/75' — ⚠️ formato no verificado
  -- Para SEMILLA el criterio verificado es el GRAMAJE, no los mm:
  -- se compra tubérculo de 100-300 g para cortar a ~50 g; semillón entero 30-60 g
  gramaje_g             numeric(6,1),
  fecha_cosecha         date,
  origen_campo          text,                     -- potrero / establecimiento de origen
  envase_id             uuid references envase(id),
  kg_iniciales          numeric(12,2) not null,   -- peso al ingresar a almacenamiento
  bultos_iniciales      int,
  observaciones         text,
  created_at            timestamptz not null default now()
);

-- Stock por lote y ubicación. Se recalcula desde `movimiento` (o trigger).
-- Separar cantidad_kg de cantidad_bultos es OBLIGATORIO:
-- es la única forma de detectar la confusión de unidades.
create table existencia (
  lote_id           uuid not null references lote(id),
  ubicacion_id      uuid not null references ubicacion(id),
  cantidad_kg       numeric(12,2) not null default 0,
  cantidad_bultos   int not null default 0,
  -- stock "verificado" = confirmado por recuento o por recepción conformada.
  -- Es lo que se usa para BLOQUEAR la emisión de un remito.
  kg_verificados    numeric(12,2) not null default 0,
  ultima_verificacion timestamptz,
  updated_at        timestamptz not null default now(),
  primary key (lote_id, ubicacion_id),
  constraint no_negativo check (cantidad_kg >= 0 and cantidad_bultos >= 0)
);

-- ─────────────────────────────────────────────
-- MOVIMIENTOS
-- ─────────────────────────────────────────────

create type tipo_movimiento as enum (
  'ingreso_cosecha',    -- entra del campo
  'traslado_interno',   -- entre ubicaciones del MISMO CUIT  ← el caso de mayor volumen
  'salida_venta',       -- a cliente
  'salida_exportacion',
  'devolucion',         -- vuelve de un cliente
  'descarte',           -- retirado por calidad (clasificación)
  'ajuste_merma',       -- merma reconocida como esperada
  'ajuste_inventario',  -- corrección tras recuento (faltante/sobrante sin explicar)
  'reclasificacion'     -- cambia categoría/calibre: consume un lote, genera otro
);

create type estado_movimiento as enum (
  'borrador',
  'confirmado',         -- documento emitido, mercadería salió
  'en_transito',        -- baja en origen hecha, alta en destino pendiente ← el agujero real
  'recepcionado',       -- destino conformó
  'anulado'
);

create table movimiento (
  id                    uuid primary key default gen_random_uuid(),
  tipo                  tipo_movimiento not null,
  estado                estado_movimiento not null default 'borrador',
  lote_id               uuid not null references lote(id),
  ubicacion_origen_id   uuid references ubicacion(id),   -- null en ingreso_cosecha
  ubicacion_destino_id  uuid references ubicacion(id),   -- null en salida/descarte
  socio_id              uuid references socio(id),       -- cliente/proveedor si aplica

  -- SIEMPRE registrar ambas cantidades y qué envase se asumió.
  cantidad_kg           numeric(12,2) not null,
  cantidad_bultos       int,
  envase_id             uuid references envase(id),
  -- true si los kg se ESTIMARON desde bultos × peso nominal en lugar de pesarse.
  -- Anexo V III lo respalda: en productos primarios la cantidad puede no ser
  -- determinable al momento del traslado.
  kg_estimados          boolean not null default false,
  -- La industria compra por NETO con deducciones (tierra, defectos, <50 mm);
  -- el mercado fresco negocia por BOLSA. Hacen falta los tres.
  peso_bruto_kg         numeric(12,2),
  peso_neto_kg          numeric(12,2),
  descuento_kg          numeric(12,2),           -- tierra, defectos, descarte de recepción

  fecha_movimiento      timestamptz not null,
  fecha_recepcion       timestamptz,                     -- null mientras no se conforme
  recepcionado_por      text,

  -- captura por voz: guardar el original para poder auditar la interpretación
  origen_carga          text not null default 'manual',  -- 'manual' | 'voz' | 'texto' | 'import'
  transcripcion_cruda   text,
  confianza_parseo      numeric(3,2),

  usuario               text not null,
  observaciones         text,
  created_at            timestamptz not null default now(),

  constraint traslado_tiene_ambas_puntas check (
    tipo <> 'traslado_interno'
    or (ubicacion_origen_id is not null and ubicacion_destino_id is not null)
  ),
  constraint cantidad_positiva check (cantidad_kg > 0)
);

create index on movimiento (lote_id, fecha_movimiento);
create index on movimiento (estado) where estado = 'en_transito';

-- ─────────────────────────────────────────────
-- DOCUMENTOS
-- ─────────────────────────────────────────────

create type tipo_documento as enum (
  'remito',        -- RG 1415 — letra R para responsable inscripto
  'factura',       -- A | B | C | E
  'nota_credito',
  'dtv',           -- SENASA — tránsito sanitario vegetal (papa SÍ está alcanzada)
  'cot'            -- ARBA — Código de Operación de Traslado, ≥4.500 kg
);

create table documento (
  id                  uuid primary key default gen_random_uuid(),
  tipo                tipo_documento not null,
  -- Remito: 'R' si emisor responsable inscripto; 'X' SÓLO si origen y destino
  -- están en el mismo predio/polo/parque industrial (Art. 28 RG 1415).
  -- Factura: 'A'/'B'/'C'/'E'.  DTV/COT: null.
  letra               char(1),
  punto_venta         int check (punto_venta between 1 and 9998),  -- 9999 NO es válido
  numero              bigint check (numero >= 1),                  -- arranca en 00000001
  -- '0001-00001234'
  numero_formateado   text generated always as (
                        lpad(punto_venta::text, 4, '0') || '-' || lpad(numero::text, 8, '0')
                      ) stored,
  fecha_emision       date not null,

  -- Autorización: OJO, son mecanismos DISTINTOS. No los unifiques en un campo.
  -- CAI: remito letra 'R' únicamente (el remito 'X' NO lleva CAI). Anexo V I.a.12-13
  cai                 text,
  cai_vencimiento     date,
  -- CAE: factura electrónica. Devuelto por el web service junto con caeFchVto
  cae                 text,
  cae_vencimiento     date,
  cuve                text,        -- DTV-e: código de validación electrónica (SENASA)
  cot_numero          text,        -- COT de ARBA

  -- Datos de imprenta: exigidos SÓLO en remito 'R' (Anexo V I.a.10-11)
  imprenta_cuit       text,
  imprenta_desde      bigint,      -- primer número del talonario impreso
  imprenta_hasta      bigint,      -- último número

  socio_id            uuid references socio(id),
  -- Traslado de bienes propios: mismo CUIT en ambas puntas.
  -- Instructivo COT: el importe NO se informa cuando CUIT origen = CUIT destino.
  -- Anexo V III: el importe tampoco es un dato exigido en el remito.
  es_traslado_propio  boolean not null default false,
  importe_total       numeric(14,2),   -- NULL (no cero) en traslado propio
  constraint importe_solo_si_hay_venta check (
    not es_traslado_propio or importe_total is null
  ),
  moneda              char(3) default 'ARS',
  tipo_cambio         numeric(12,4),   -- factura E: monedaCtz, debe ser > 0
  incoterm            text,            -- factura E
  pais_destino        char(2),         -- factura E: dstPais
  permiso_embarque    text,            -- factura E: sólo si exportación de BIENES

  -- TRANSPORTE — atención a quién exige qué:
  -- Anexo V IV: nombre, domicilio y CUIT del transportista SÓLO si el traslado
  --   lo hace un TERCERO. Con camión propio, el remito no lo exige.
  -- COT (ARBA): dominio del vehículo OBLIGATORIO si el transporte es propio;
  --   dominio del acoplado/jaula opcional. NO es requisito de la RG 1415.
  transporte_terceros  boolean not null default false,
  transportista_nombre text,
  transportista_cuit   text,
  transportista_domicilio text,
  dominio_vehiculo     text,        -- patente — requisito del COT
  dominio_acoplado     text,
  -- COT: domicilio de origen y destino son obligatorios (calle, número, localidad).
  -- La RG 1415 no los pide como campo propio: usa el domicilio comercial de cada punta.
  lugar_origen         text,
  lugar_destino        text,
  -- COT: recorrido y distancia
  tipo_recorrido       text,        -- 'urbano' | 'rural' | 'mixto'
  distancia_rango      text,        -- '<500' | '500-1000' | '>1000'
  fecha_estimada_entrega date,      -- derivable del rango y del tipo de transporte

  pdf_url             text,
  created_at          timestamptz not null default now(),

  unique (tipo, letra, punto_venta, numero)
);

-- Un movimiento puede tener varios documentos (remito + DTV + COT),
-- y un remito puede cubrir varios movimientos (varios lotes en un camión).
create table documento_movimiento (
  documento_id   uuid not null references documento(id),
  movimiento_id  uuid not null references movimiento(id),
  primary key (documento_id, movimiento_id)
);

-- ─────────────────────────────────────────────
-- RECUENTOS, MERMA Y DISCREPANCIAS
-- ─────────────────────────────────────────────

create table recuento (
  id              uuid primary key default gen_random_uuid(),
  ubicacion_id    uuid not null references ubicacion(id),
  tipo            text not null default 'ciclico',   -- 'ciclico' | 'total'
  fecha           timestamptz not null default now(),
  usuario         text not null,
  cerrado         boolean not null default false
);

create table recuento_linea (
  id                  uuid primary key default gen_random_uuid(),
  recuento_id         uuid not null references recuento(id),
  lote_id             uuid not null references lote(id),
  kg_declarados       numeric(12,2) not null,   -- lo que decía el sistema
  bultos_declarados   int,
  kg_contados         numeric(12,2) not null,   -- lo que se contó/pesó
  bultos_contados     int,
  diferencia_kg       numeric(12,2) generated always as (kg_contados - kg_declarados) stored,
  -- negativo ⇒ faltante, positivo ⇒ sobrante
  merma_esperada_kg   numeric(12,2),            -- calculada por días × tasa × temperatura
  -- lo que la merma NO explica: esto es lo que el sistema debe investigar
  desvio_sin_explicar_kg numeric(12,2) generated always as (
                          (kg_contados - kg_declarados) + coalesce(merma_esperada_kg, 0)
                        ) stored,
  hipotesis           text,                     -- explicación en lenguaje llano
  hipotesis_confianza numeric(3,2),
  evidencia           jsonb,                    -- ids de movimientos/documentos que la sustentan
  resuelto            boolean not null default false,
  ajuste_movimiento_id uuid references movimiento(id)
);

-- Parámetros de merma: hacen que la "merma esperada" sea calculable y auditable,
-- no un número mágico. Ajustables por variedad/destino/temperatura.
-- La merma NO es lineal: >50% de la pérdida de temporada ocurre en los
-- primeros 30 días. Un %/mes plano inventa faltantes en lotes viejos y
-- esconde faltantes reales en lotes nuevos. De ahí los dos tramos.
create table parametro_merma (
  id                  uuid primary key default gen_random_uuid(),
  destino             text not null,            -- 'semilla' | 'industria' | 'consumo'
  tipo_ubicacion      tipo_ubicacion not null,
  temperatura_c       numeric(4,1),
  -- TRAMO 1: primer mes (dominado por transpiración post-cosecha)
  pct_primer_mes_min  numeric(5,3) not null,    -- 1.0 maduro / 3.0 inmaduro
  pct_primer_mes_max  numeric(5,3) not null,    -- 3.0 maduro / 5.0 inmaduro
  -- TRAMO 2: meses subsiguientes
  pct_mensual_min     numeric(5,3) not null,    -- 0.5
  pct_mensual_max     numeric(5,3) not null,    -- 1.0  (→1.5 con brotación avanzada)
  pct_mensual_brotado numeric(5,3),             -- 1.5
  -- Multiplicador si el lote entró inmaduro o dañado: hasta 2x (U. Idaho)
  factor_inmaduro     numeric(4,2) default 2.0,
  -- Umbral de alarma: >10% afecta comerciabilidad (CIP)
  pct_umbral_alarma   numeric(5,3) default 10.0,
  fuente              text not null,            -- trazabilidad del parámetro
  vigente_desde       date not null default current_date
);

-- Parámetros verificados de arranque (ver §5.3):
insert into parametro_merma
  (destino, tipo_ubicacion, temperatura_c, pct_primer_mes_min, pct_primer_mes_max,
   pct_mensual_min, pct_mensual_max, pct_mensual_brotado, fuente) values
  ('semilla',  'camara_frio', 4.0, 1.0, 3.0, 0.5, 1.0, 1.5,
   'UNLP/CIP - ⚠️ cifras de papa consumo, no hay dato específico de semilla'),
  ('industria', 'camara_frio', 8.5, 1.0, 3.0, 0.5, 1.0, 1.5, 'UNLP 8-9 °C / CIP'),
  ('consumo',   'camara_frio', 7.0, 1.0, 3.0, 0.5, 1.0, 1.5, 'UCA 10 °C / CIP 4-7 °C'),
  ('industria', 'galpon',     15.0, 3.0, 5.0, 1.0, 2.0, 3.0,
   'Ordóñez et al. FAUBA: 7,8% a 161 días sin refrigeración');
```

### Notas de diseño que conviene poder defender

1. **`existencia.kg_verificados` separado de `cantidad_kg`.** El requerimiento del sponsor es bloquear el remito cuando el **stock verificado** es insuficiente. Si sólo tenés un número de stock, no podés distinguir "hay 10 toneladas según el sistema" de "hay 10 toneladas que alguien contó". Esta columna es la que habilita el feature (b) y es el detalle que hace que el modelo se vea pensado.
2. **`estado = 'en_transito'` + la ubicación virtual `transito`.** El agujero real de una operación de 4 plantas es la mercadería que salió y no llegó. Si el tránsito no tiene dónde vivir, el stock total de la empresa no cierra y nadie sabe por qué.
3. **`cantidad_kg` y `cantidad_bultos` siempre juntos, más `kg_estimados`.** Sin esto, la confusión de unidades es indetectable. Con esto, es un chequeo aritmético trivial y una hipótesis muy convincente. **Y no es una idea nuestra:** el formulario del COT de ARBA pide *"Unidad de Medida de Nomenclador + Cantidad"* **y** *"Unidad de medida propia + Cantidad propia"*, definiendo la segunda como *"aquella unidad de medida utilizada por la empresa en sus registros"*. El Estado ya modeló la unidad doble porque el problema es real.
4. **La letra del remito es derivada, no elegida.** `letra = (origen.establecimiento = destino.establecimiento) ? 'X' : 'R'` para un emisor responsable inscripto (Art. 28). Y el `punto_venta` se elige según la **causa** del traslado (transferencia de dominio o no), por Anexo V ap. V pto. 6.b. Dos reglas que una planilla equivoca sistemáticamente y que el sistema puede acertar siempre.
5. **Campos de autorización separados (`cai` / `cae`).** No unificar en un `codigo_autorizacion` genérico: son mecanismos distintos, se obtienen en momentos distintos, y el remito X no lleva ninguno. Es el detalle que un contador mira primero.
6. **`campania` como campo, no derivado de la fecha.** Un lote de campaña 2025/26 se puede mover en agosto de 2026. Derivarlo de la fecha rompe la trazabilidad.
7. **`transcripcion_cruda` + `confianza_parseo`.** Si el input es por voz, guardar el texto original es lo que te permite auditar cuando el sistema entendió "ochenta bolsones" en lugar de "ocho bolsones". Y esa es, además, una causa realista de discrepancia que tu propio sistema introduce — mostrarla es señal de madurez, no de debilidad.
8. **`documento_movimiento` como N:N.** Un camión lleva 3 lotes bajo 1 remito; y 1 movimiento genera remito + DTV + COT. Cualquier relación 1:1 se rompe en la primera demo real.
9. **`kg_estimados` tiene respaldo normativo.** El Anexo V III admite que en productos primarios *"por la modalidad operativa no sea posible determinar la cantidad"*. Es decir: un remito de papa a granel emitido con cantidad estimada **es legal**, y la diferencia con el pesaje en destino **no es un error**. Modelalo como un estado legítimo, no como una excepción.

---

## Reglas de validación para el bloqueo del remito

El requerimiento (b) del sponsor es *"bloquear la emisión de un remito cuando el stock verificado es insuficiente"*. Estas son las reglas que conviene implementar, ordenadas por valor demostrativo. Las marcadas 🏛️ tienen respaldo normativo verificado — decirlo en voz alta es lo que separa un prototipo de una demo creíble.

| # | Regla | Mensaje al usuario |
|---|---|---|
| 1 | `cantidad_kg > existencia.kg_verificados` en la ubicación de origen | **"Stock verificado insuficiente."** Muestra declarado, verificado y la hipótesis de la brecha |
| 2 | 🏛️ Si `origen.establecimiento = destino.establecimiento` ⇒ letra **X**; si no ⇒ **R** | Se calcula solo; no se pregunta |
| 3 | 🏛️ Si letra **R** ⇒ exigir `cai` vigente (no vencido). Si letra **X** ⇒ **no** pedir CAI | "El talonario R del punto de venta 0102 vence el …" |
| 4 | 🏛️ Si `cuit_origen = cuit_destino` ⇒ `importe_total` debe ser **null** | Se oculta el campo importe |
| 5 | 🏛️ Punto de venta según la **causa**: venta vs traslado sin transferencia de dominio | Se asigna solo según el tipo de movimiento |
| 6 | 🏛️ Si `transporte_terceros = true` ⇒ exigir nombre, domicilio y CUIT del transportista | "Falta el CUIT del transportista (obligatorio en traslado por terceros)" |
| 7 | Si `cantidad_kg ≥ 4.500` ⇒ requerir **COT** antes de despachar | **"Este traslado requiere COT: 12.400 kg supera el umbral de 4.500 kg."** |
| 8 | Si el producto es papa ⇒ requerir **DTV-e** | "Falta el DTV-e. Sin DTV el camión no puede circular." |
| 9 | 🏛️ `punto_venta` entre 0001 y 9998; `numero` correlativo sin saltos por punto de venta | "El remito 0102-00000419 rompe la correlatividad" |
| 10 | Si el destino es exterior ⇒ factura **E**, con `incoterm`, `moneda`, `tipo_cambio` y `permiso_embarque` | (deriva al flujo de exportación) |

> 🎯 **La regla 7 es la más fácil de demostrar y la más impactante.** Es un número duro, verificado, provincial, y aplica a casi todos los traslados de Papasud. Que el sistema diga *"esto requiere COT"* sin que nadie se lo haya pedido es la clase de detalle que hace que el sponsor piense "esta gente entendió mi negocio".

---

## Escenarios de discrepancia para el demo

Seis escenarios. Cada uno tiene una **firma detectable en los datos** — no son adivinanzas, son inferencias que el sistema puede hacer con las tablas de arriba. Eso es lo que hay que mostrar.

> **Nota sobre los números.** Las cantidades son **inventadas pero verosímiles** para una operación de ~7.500 t/ciclo y ~150 lotes. Los porcentajes de merma **sí están verificados** (§5.3): ~2 % el primer mes, ~0,8 %/mes después, ~5 % a los 5 meses, &gt;10 % como umbral de problema. Los envases usan los pesos verificados de §6: **bolsón 700 kg**, **bolsa de semilla 50 kg**, **bolsa de consumo ~20 kg**. Todos los escenarios son aritméticamente consistentes entre sí — revisá que sigan siéndolo si cambiás algún número.

---

### Escenario 1 — Baja en origen sin alta en destino *(el clásico, y el más frecuente)*

**Situación.** Recuento cíclico en Cámara Balcarce, lote `2526-SPU-G2-014` (papa semilla, 4 °C).
- Declarado: **41.000 kg** (820 bolsas de 50 kg) · Contado: **35.000 kg** · **Faltante: 6.000 kg**
- Merma esperada — el lote lleva **42 días** en cámara: primer mes ~2 % (820 kg) + 12 días a ~0,8 %/mes (130 kg) = **~950 kg**
- **Desvío sin explicar: ~5.050 kg**

**Firma en los datos.** Existe el movimiento `traslado_interno` del remito **`0102-00000418`** (Mar del Plata → Balcarce), **5.000 kg**, `estado = 'en_transito'`, `fecha_movimiento` hace 9 días, `fecha_recepcion = null`. La baja en Mar del Plata se registró; el alta en Balcarce, no.

> 🗣️ **Hipótesis:** *"El faltante es de 6.000 kg, pero 950 son merma esperada para 42 días de cámara. Los 5.050 kg restantes coinciden con los 5.000 kg del remito 0102-00000418, que salió de Mar del Plata hace 9 días y todavía figura en tránsito: nadie confirmó la recepción en Balcarce. Lo más probable es que la papa esté físicamente acá pero el ingreso nunca se cargó. Sugerencia: conformar la recepción del remito 0102-00000418; el faltante queda en 950 kg, que es la merma esperada."*

**Por qué convence:** es exactamente lo que pasa todos los días, y la planilla compartida no lo puede detectar porque no tiene el concepto de "en tránsito".

---

### Escenario 2 — Confusión de unidad: bolsones contados como bolsas

**Situación.** Recuento en Galpón Norte, lote `2526-INN-G3-007`.
- Declarado: **2.000 kg** · Contado: **28.000 kg** · **Sobrante: 26.000 kg**
- Un sobrante enorme y "redondo" es siempre sospechoso de unidad, no de robo.

**Firma en los datos.** El movimiento de ingreso tiene `cantidad_bultos = 40`, `kg_estimados = true`, `envase_id` → *Bolsa semilla 50 kg* ⇒ 40 × 50 = 2.000 kg. Pero el conteo físico encuentra **40 bolsones**. Con *Bolsón 700 kg*: 40 × 700 = 28.000 kg.
**La aritmética delata el error:** 26.000 / 40 = **650 kg por bulto** = exactamente **700 − 50**, la diferencia entre los dos envases. El sobrante es un múltiplo exacto de la cantidad de bultos.

> 🗣️ **Hipótesis:** *"No falta ni sobra papa: está mal la unidad. El ingreso se cargó como 40 bolsas de 50 kg (2.000 kg) pero en el galpón hay 40 bolsones. El sobrante dividido por la cantidad de bultos da 650 kg, que es exactamente la diferencia entre un bolsón de 700 y una bolsa de 50. La carga original eligió el envase equivocado. Sugerencia: corregir el envase del movimiento de ingreso — no hacer un ajuste de inventario."*

**Por qué convence:** el sistema distingue "corregir el dato" de "ajustar el stock". Un ajuste de inventario acá **escondería** el error en lugar de arreglarlo. Esa distinción es de alguien que entiende inventarios.

---

### Escenario 3 — Merma de almacenamiento pura: **no hay error**

**Situación.** Recuento en Cámara Mar del Plata, lote `2526-SPU-G2-003`, **5 meses** en cámara a 4 °C.
- Declarado: **120.000 kg** · Contado: **114.000 kg** · **Faltante: 6.000 kg (5,0 %)**
- Merma esperada a 5 meses: **~5 %** (≈ 2 % el primer mes + ~0,8 %/mes los 4 siguientes)
- **Desvío sin explicar: ≈ 0**

> 🗣️ **Hipótesis:** *"Este faltante de 6.000 kg es 5,0 % sobre 5 meses de cámara. La merma esperada para este lote es del orden del 5 %: alrededor de 2 % el primer mes y 0,8 % por mes después. Está en el rango normal, y muy por debajo del 10 % que se considera problema. No hay indicio de error: ningún remito en tránsito, ningún movimiento duplicado, ninguna inconsistencia de envase en este lote. Sugerencia: registrar un ajuste de merma. No hay nada que investigar."*

**Refuerzo opcional muy efectivo:** mostrar que el sistema entiende la **forma de la curva**, no sólo el total — *"y de esos 6.000 kg, unos 3.500 se perdieron en el primer mes: más de la mitad de la merma de toda la temporada ocurre en los primeros 30 días."* Esa frase, que está respaldada (55-70 % de la pérdida ocurre en los primeros 30 días), es la que convence a alguien que conoce la cámara de que el sistema no está tirando un promedio.

**Por qué convence — y por qué este es el escenario más importante del demo.** Cualquier sistema puede gritar "¡diferencia!". El valor está en decir **"esto está bien, seguí trabajando"**. Es lo que hace que el encargado confíe en las alertas de los otros cinco escenarios en lugar de ignorarlas todas. **Mostralo segundo o tercero, no último.**

---

### Escenario 4 — Remito duplicado

**Situación.** Cámara Balcarce, lote `2526-ATL-G2-021`.
- Declarado: **62.000 kg** · Contado: **80.000 kg** · **Sobrante: 18.000 kg**

**Firma en los datos.** Dos movimientos `salida_venta` de 18.000 kg cada uno, mismo lote, mismo `socio_id`, fechas separadas por 20 minutos, **ambos vinculados al mismo `documento` `0001-00003142`**. Se descontó dos veces la misma salida.

> 🗣️ **Hipótesis:** *"El sobrante de 18.000 kg es igual, al kilo, a la salida del remito 0001-00003142. Ese remito se descontó dos veces del stock: hay dos movimientos idénticos cargados con 20 minutos de diferencia, probablemente porque la primera carga pareció no guardarse. La papa nunca salió dos veces. Sugerencia: anular el movimiento duplicado."*

**Por qué convence:** los sobrantes suelen despertar más desconfianza que los faltantes ("¿de dónde salió esta papa?"), y la explicación es casi siempre un doble descuento. Que el sistema lo diga solo es muy vendible.

---

### Escenario 5 — Descarte de clasificación registrado como faltante

**Situación.** Packing Balcarce, lote `2526-KEN-G3-045`. Se acondicionaron 50.000 kg para despacho a PepsiCo.
- Declarado: **50.000 kg** · Contado: **44.000 kg** · **Faltante: 6.000 kg (12%)**
- Merma de almacenamiento esperada: **~30 kg** (el lote se movió ayer; ~0,45 %/semana ≈ 0,06 %/día por EP475.3)

**Firma en los datos.** Hay un evento de acondicionamiento sobre este lote hace 1 día, pero **ningún movimiento de tipo `descarte`** asociado. El faltante es del 12% del volumen procesado — orden de magnitud de descarte de calibrado, no de merma de cámara. Y coincide temporalmente con el procesamiento.

> 🗣️ **Hipótesis:** *"Este faltante no es merma: 6.000 kg en un día es imposible por deshidratación — lo esperado son unos 30 kg. El lote se clasificó ayer y no se registró ningún descarte. El 12 % está dentro del rango de pérdida de calidad de 5 a 15 % que se da incluso con buen manejo, y es consistente con el descarte por calibre: la industria no paga papa menor a 50 mm. Sugerencia: registrar 6.000 kg como descarte del acondicionamiento del 20/08, así el rendimiento de proceso queda medido y el faltante desaparece."*

**Por qué convence:** demuestra que el sistema entiende que **la papa no se pierde, se reclasifica**, y convierte un "faltante" molesto en un **KPI de rendimiento de packing** que al dueño le interesa medir. El detalle de los **50 mm** es verificado y muy específico: es el tipo de dato que sólo tiene alguien que miró el negocio de verdad. Esto abre conversación de negocio, no de software.

---

### Escenario 6 — Movimiento cargado en la ubicación equivocada *(faltante y sobrante que se cancelan)*

**Situación.** Recuento simultáneo en dos ubicaciones, lote `2526-SPU-G1-002`:
- Cámara Mar del Plata → **faltante de 24.000 kg**
- Depósito Tandil → **sobrante de 24.000 kg**
- Neto a nivel empresa: **0 kg**

**Firma en los datos.** Mismo lote, mismas cantidades exactas, signo opuesto, misma fecha de recuento. El último `traslado_interno` del lote tiene `ubicacion_destino_id` = Tandil, pero el remito `0102-00000501` dice `lugar_destino = 'Mar del Plata'`. El documento y el movimiento no coinciden.

> 🗣️ **Hipótesis:** *"No falta papa: está en otra ubicación. El faltante de 24.000 kg en Mar del Plata y el sobrante de 24.000 kg en Tandil son el mismo lote y la misma cantidad exacta. El remito 0002-00000501 declara destino Mar del Plata, pero el movimiento se cargó con destino Tandil. A nivel empresa el stock cierra perfecto. Sugerencia: corregir el destino del movimiento; no hace falta ningún ajuste."*

**Por qué convence:** es el argumento más fuerte a favor de la **vista unificada de las 4 ubicaciones**. Con planillas separadas por planta, este error es **invisible**: cada planilla parece tener un problema propio y grave, y nadie ve que se cancelan. Es la prueba de que el problema no era la planilla, era la **fragmentación**.

---

### Cómo ordenar los escenarios en el pitch

1. **Escenario 1** — el dolor que ya conocen. Engancha.
2. **Escenario 3** — "esto está bien". Genera confianza en el sistema.
3. **Escenario 6** — justifica la vista unificada. Es el argumento arquitectónico.
4. **Escenario 5** — convierte un problema en un KPI. Abre conversación de negocio.
5. Escenarios 2 y 4 quedan de reserva para preguntas.

Y el bloqueo del remito por stock verificado insuficiente conviene mostrarlo **en vivo**, intentando emitir un remito de 50.000 kg sobre un lote con 35.000 kg verificados: el sistema lo rechaza y **ofrece la hipótesis del Escenario 1** como explicación de por qué el stock verificado es menor al declarado. Ahí los tres features del sponsor se cierran en una sola pantalla.

---

## Fuentes

**Normativa y organismos**
- [RG (AFIP) 1415/2003 — Facturación y Registración (texto completo)](https://www.argentina.gob.ar/normativa/nacional/resoluci%C3%B3n-1415-2003-81316/texto) — Art. 27, 28, 29, 30, 33, 47
- **[RG 1415 — ANEXO V, texto completo en HTML (Biblioteca electrónica CPCECABA)](https://archivo.consejo.org.ar/Bib_elect/diciembre04_CT/documentos/rafip1415anexoV.htm)** ← la fuente clave de los campos del remito, con la modificación de la RG 1697/04
- [Boletín Oficial — RG 5678/2025, remito digital (22/04/2025)](https://www.boletinoficial.gob.ar/detalleAviso/primera/324239/20250422)
- [ARCA — factura electrónica, solicitud de autorización (puntos de venta)](https://www.arca.gob.ar/fe/emision-autorizacion/solicitud-autorizacion.asp)
- [ARCA — comprobantes de exportación de servicios (clase E)](https://www.arca.gob.ar/derechos-de-exportacion-de-servicios/comprobantes-y-facturacion/comprobantes.asp)
- [Anexo V RG 1415 (PDF oficial de ARCA — escaneado, no extraíble)](https://biblioteca.afip.gob.ar/pdfp/ANEXO_V_RG1415_V4290.pdf)
- [ARBA — Instructivo COT (PDF)](https://www.arba.gov.ar/archivos/Publicaciones/Instructivo%20COT.pdf)
- [ARBA — Guía de trámites (COT)](https://www.arba.gov.ar/GuiaTramites/TramiteSeleccionado.asp)
- [Mercado Central — obligatoriedad del DTV para hortalizas pesadas](https://mercadocentral.gob.ar/news/ser%C3%A1-obligatorio-el-uso-del-dtv-para-el-traslado-de-hortalizas-pesadas)

**Análisis y documentación técnica**
- [Estudio Noya — revisión de la RG 5678/2025 (modifica RG 1415 sobre documentación de traslado)](https://noya.com.ar/categoria-consultoria-de-empresas/revision-de-la-resolucion-general-5678-2025-de-a-r-c-a-modificacion-a-la-rg-1415-2003-sobre-documentacion-de-traslado/)
- [BAE Negocios — remito digital ARCA](https://www.baenegocios.com/economia/ARCA-como-hacer-un-remito-digital-para-el-traslado-de-mercaderia-20250422-0025.html)
- [Odoo — localización fiscal Argentina](https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/argentina.html) — tipos de comprobante, punto de venta, libro unificado, web services
- [Documentación WSFEX — emitir factura E](https://arca.api.com.ar/docs/wsfex/facturas) — campos `tipoExpo`, `incoterms`, `moneda`, `monedaCtz`, `dstPais`, `permisos`, `cae`, `caeFchVto`
- [MyContador — remito digital en ARCA](https://blog.mycontador.com.ar/remito-digital-en-arca) — remito R entre depósitos propios en domicilios distintos
- [YoFacturo — Factura A, B, C y E](https://yo-facturo.com/docs/sales/invoices/)
- [declar.ar — diferencias factura A/B/C](https://declar.ar/blog/factura-a-b-c-diferencias/)
- [Dux Software — qué es un remito](https://duxsoftware.com.ar/blog/que-es-un-remito-argentina) — ⚠️ contiene la afirmación errónea "X = interno"
- [YoFacturo — remito electrónico](https://yo-facturo.com/blog/remito-electronico-afip/) — ⚠️ ídem, y atribuye CAE al remito

**Almacenamiento, merma y envases de papa**
- **[UNLP, Fac. de Ciencias Agrarias — "El almacenamiento de la papa" (PDF)](https://aulavirtual.agro.unlp.edu.ar/pluginfile.php/60746/mod_folder/content/0/El%20almacenamiento%20de%20la%20papa.pdf)** — la fuente argentina central: %/mes de merma, temperaturas, curado, brotación
- **[UCA — Amand de Mendieta, "Cultivo de Papa: generalidades, ensayos comparativos de rendimiento y estudio de mercado" (PDF)](https://repositorio.uca.edu.ar/bitstream/123456789/19559/1/cultivo-papa-generalidades.pdf)** — envases (bolsón 700 kg, bolsa 20 kg / semilla 50 kg), comercialización por bolsa, temperaturas, gramaje, pilas a campo &gt;30 %
- [Ordóñez et al. 1985, Rev. Fac. de Agronomía UBA — "Acción del CIPC y otros factores en la pérdida de peso durante el almacenamiento de papa para la industria" (PDF)](https://ri.agro.uba.ar/files/download/revista/facultadagronomia/1985ordonezcr.pdf) — 7,76-7,91 % a 161 días sin refrigeración; ranking de envases
- [Del Pino 2014, FAUBA — papa andina, NOA (PDF)](https://ri.agro.uba.ar/files/download/tesis/especializacion/2014delpinomariajulia.pdf) — ⚠️ descarte 40 % en contexto de autoconsumo, **no comercial**
- [bins.com.ar — guía de bins agrícolas en Argentina](https://bins.com.ar/noticia?slug=bins-agricolas-argentina-guia-productores) — bins 440 L y 570 L, ~350 kg, cajones ~20 kg
- [Coirón — almacenamiento de papa en bins/granel](https://coiron.com.ar/almacenamiento-de-papa-en-bins-granel/) — +2 a +10 °C según requerimiento
- [Argenpapa](https://www.argenpapa.com.ar/) y [nota de costos por bolsa](https://www.argenpapa.com.ar/noticia/16501-argentina-el-costo-de-produccion-de-la-bolsa-de-papa-supera-ampliamente-a-lo-recibido-por-productor-en-el-mercado) — cotización en $/bolsa
- [Agrolatam — crisis de precio 2025](https://www.agrolatam.com/actualidad/crisis-precio-papa-argentina-2025/) — "la bolsa de 18 kilos"

**Fuentes internacionales (etiquetadas como no argentinas)**
- [CIP — "Principles of Potato Storage" (PDF)](https://cipotato.org/wp-content/uploads/2014/09/004729.pdf) — %/mes, umbral del 10 %, tabla de temperaturas por destino
- [University of Idaho Extension BUL 1081 (2024) — "Understanding Weight Loss of Potato Tuber in Storage"](https://www.uidaho.edu/extension/publications/bul-1081) — fórmula **ASAE EP475.3**, split 97,6 %/2,4 %
- [Potato Grower — "Weighing In: Managing Weight Loss in Storage" (2017)](https://www.potatogrower.com/2017/11/weighing-in) — 55-70 % de la pérdida en los primeros 30 días

---

## Lista de lo NO verificado (no afirmar como cierto)

**Resuelto durante la investigación (ya NO es incierto):**
- ✅ Lista textual completa del **Anexo V** — obtenida de la biblioteca del CPCECABA (§1.5).
- ✅ El remito lleva **CAI**, no CAE. Y el remito **X no lleva CAI**.
- ✅ El **importe no se informa** cuando el CUIT de origen y destino son el mismo (Instructivo COT) y **no es un dato exigido** por el Anexo V.
- ✅ El traslado **entre depósitos de una misma empresa** es un traslado documentado bajo RG 1415 (Instructivo COT).
- ✅ **RG 5678/2025** verificada en el Boletín Oficial (el CAI sigue siendo obligatorio; se exceptúa el tamaño de 15×20).
- ✅ Punto de venta: rango **0001–9998**, 4+8 dígitos, y **las dos opciones** de asignación (por inmueble o por medio de emisión) son válidas a opción del contribuyente.
- ✅ **Cifras de merma**, con fuentes argentinas (UNLP, UCA, FAUBA/Ordóñez) más CIP y U. Idaho: curva no lineal, 1-3 % el primer mes, 0,5-1 %/mes después, ~5 % a 5 meses, &gt;10 % umbral de problema, fórmula ASAE EP475.3.
- ✅ **Temperaturas**: semilla 4-5 °C, industria 8-9 °C, consumo ~10 °C, no bajar de 3 °C, HR &gt;90 %.
- ✅ **Pesos de envase**: bolsón de papa **700 kg** (¡no 1.000!), bolsa de **semilla 50 kg**, bolsa de **consumo ~20 kg**, bin de 570 L ≈ 350 kg.
- ✅ **En Argentina la papa se comercializa por BOLSA, no por peso** — y el peso de la bolsa derivó en el tiempo. La industria, en cambio, compra por **neto con deducciones** y descarta &lt;50 mm.
- ✅ **No existe** una convención normada de numeración de lotes en Argentina.

**Todavía NO verificado — no afirmar como cierto:**
- ❌ **Ninguna cifra de merma específica de papa SEMILLA.** Todas las cifras de %/mes son de papa consumo/industria. La semilla se guarda más fría (4 °C), lo que implica *menos* transpiración — pero eso es **inferencia**. Marcá el parámetro de semilla como calibrable.
- ❌ **Ningún desglose porcentual** entre transpiración / respiración / brotación / pudrición / descarte en fuente argentina. Sólo el orden cualitativo.
- ❌ **Ninguna publicación de INTA Balcarce** con cifras de merma (el sitio no respondió).
- ❌ El dato de **descarte del 40 %** de una tesis de FAUBA es de **papa andina de autoconsumo en el NOA** — **no es cifra comercial**, no la uses.
- ❌ La **densidad aparente de la papa (~590 kg/m³)** viene de una fuente débil. El bolsón de **700 kg** sí está en fuente argentina; el cálculo de litros→kg de los bins es **inferencia mía**.
- ❌ **Formatos de calibre en mm** (`35/55`, `55/75`). Para semilla el criterio verificado es el **gramaje** (100-300 g para cortar a ~50 g; semillón 30-60 g).
- ❌ Bolsas de **20/25/30 kg para semilla** — no hay fuente argentina; la de semilla verificada es de **50 kg**.
- ❌ Cualquier **"unidad de semilla"** formal para papa (a diferencia de maíz/girasol) — no existe uso documentado.
- ❌ Números de resolución de los regímenes de **remito electrónico** para harina de trigo y azúcar. (Sí existe el **Remito Electrónico Cárnico**; el número no lo confirmé.)
- ❌ El **código de producto de 6 dígitos** de la papa en el nomenclador del COT. La estructura (2 primeras posiciones = capítulo) sí está verificada; que la papa caiga en el **capítulo 07** es inferencia.
- ❌ Si la **papa figura nominalmente** en los Anexos I/II del COT y si hay exenciones para productos primarios. El **umbral de 4.500 kg** sí está verificado.
- ❌ Cualquier **convención estándar de numeración de lotes** en el agro argentino — **confirmado que no existe** una normada. La propuesta de §3.2 es diseño propio.
- ❌ Las **RG de fondo de la factura E** (2758/2010, 3689/2014) no fueron abiertas; los campos vienen de documentación del web service.
- ❌ El formato **`0001-00001234`** con guion como requisito legal — es convención de mercado. Los 12 dígitos sí son norma.
- ❌ Rangos numéricos reservados para puntos de venta manuales vs electrónicos — **confirmado que no existen**; sólo se exige que sean distintos.
- ⚠️ Detalles secundarios de la **RG 5678/2025**: prescindir de "ORIGINAL"/"DUPLICADO" y los plazos de **15 / 45 días**. No están en el texto que leí.
- ⚠️ Número **RG 5017/2021** como norma vigente de la Carta de Porte Electrónica. Lo que **sí** está firme es que el régimen es **de granos y no alcanza a la papa**.
- ⚠️ Detalles operativos del **DTV-e** (SIGDTV, CUVE, Resolución 242/2025): provienen de fuentes secundarias. Lo **verificado** es que el DTV **es obligatorio para el tránsito de papa** desde 2018.
