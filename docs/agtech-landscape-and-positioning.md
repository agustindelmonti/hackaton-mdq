---
tags: [research, agtech, papasud, hackathon, positioning]
date: 2026-08-21
event: [[cursor-hackathon-mar-del-plata-2026]]
status: reference
---

# Landscape agtech y posicionamiento — Papasud / Cursor Hackathon MdP

> **Cómo leer este doc.** Todo lo que tiene link es verificado. Lo que dice `[INFERENCIA]` es mi lectura del conjunto, no una cita. Cuando no encontré algo lo digo (`no verificado`) en vez de rellenar. Ver [[papasud]] para las 3 verticales del desafío y [[papasud-company-research]] para la empresa.

**Tesis en una línea:** el problema de Papasud cae exactamente en el hueco entre tres industrias de software que existen y funcionan — *monitoreo satelital* (argentino, barato, irrelevante), *ERP agropecuario* (argentino, transaccional, ciego a la semilla) y *ERP semillero / trazabilidad de papa* (europeo, correcto, no comprable acá) — y ningún producto cruza el hueco.

---

## 0. El mapa mental: tres capas que el marketing confunde

El campo agtech argentino se divide en tres capas que conviene no mezclar, porque **el 90% de lo que suena a competencia vive en la capa 1 y el dolor de Papasud vive en la capa 3**:

| Capa | Qué es | Qué NO tiene | Ejemplos AR |
|---|---|---|---|
| **1. Sensado remoto / decision support** | NDVI satelital, prescripciones, estimación de rinde, riego | Registros transaccionales, stock, órdenes de trabajo | Frontec, S4, Kilimo, Climate FieldView, Granular |
| **2. Cuaderno de campo / monitoreo** | Monitoreos georreferenciados, logs de aplicación, EIQ, certificación de sustentabilidad | Movimientos de inventario, lotes físicos, documentación | SIMA, Ucrop.it, Auravant (nivel medio) |
| **3. Gestión operativa/administrativa (FMIS/ERP real)** | Órdenes de compra, stock por depósito, costeo de labores, maquinaria, contabilidad | *Semántica de semilla*: categoría, generación, decomiso de clase | Agri, GestorMax, SYNAgro, Physis |

`[INFERENCIA — es la conclusión central del research]` **Ningún producto que pude verificar implementa semántica de certificación de semilla**: linaje categoría/generación (Prebásica → Básica → Registrada → Certificada; G0…Gn), estampillas y DAV/DAM de INASE, ni saldos de stock por lote en múltiples cámaras de frío. Esa capacidad hoy vive en el portal regulatorio de INASE — que es un organismo, no un vendor.

---

## 1. Software de gestión agrícola en Argentina

### 1.1 Los agtech argentinos "de marca"

| Producto | Capa | Qué hace realmente | Para quién | Precio público | ¿Sirve para papa semilla? |
|---|---|---|---|---|---|
| **[Auravant](https://www.auravant.com/en/pricing-en/)** | 2 (+3 vía extensiones) | Monitoreo satelital, prescripciones, registros agronómicos, **órdenes de trabajo**, cuaderno de campo digital, stock/silos vía marketplace de extensiones | Productores, agrónomos, LatAm + Europa | **Sí, parcial**: gratis hasta 1.000 ha; pagos ~USD 15–40/mes; premium ~USD 50–150 ([review de planes](https://agentaya.com/es/ai-review/auravant/)) | Genérico. Nada modela generaciones de semilla |
| **[SIMA](https://blog.sima.ag/2026/expoagro-2026-sima-agtech/)** | 2 | Monitoreo georreferenciado (malezas/plagas/enfermedades), órdenes de aplicación, avance de siembra/cosecha, EIQ + huella de carbono, GIS, tableros | Productores, equipos agronómicos, cultivos extensivos | No público | No. Derivó hacia certificación y reporte ambiental; sin stock ni horticultura |
| **[S4](https://www.syngentagroupventures.com/s4)** (ex-Solapa4) | 1 | Índices satelitales de rinde → **productos financieros de riesgo** (Cobertura Index®, seguros climáticos, derivados índice) | Bancos, aseguradoras, proveedores de insumos | No público | No |
| **[Frontec](https://www.infoespacial.com/texto-diario/mostrar/3568958/empresa-argentina-frontec-utiliza-satelites-mejorar-gestion-agricola)** | 1 | Servicios de sensado remoto (origen Invap + Los Grobo): agricultura de precisión, monitoreo, prescripciones, BI agro | Productores grandes / empresas | No público | No |
| **[Kilimo](https://kilimo.com/)** | 1 + servicios | Recomendación de riego por satélite/clima sin sensores; mide m³ ahorrados (VWBA) para venderlos como créditos de agua a corporaciones | Productores bajo riego **y** corporativos | No público | No |
| **[DeepAgro](https://www.deepagro.com/es/tech.html)** (SprAI) | Hardware/edge AI | Pulverización selectiva retrofit: cámaras RGB + deep learning en el botalón, actuación por pico. ~73% de ahorro de químico, >90 equipos instalados | Dueños de pulverizadoras, contratistas | No; ahorro citado ~USD 50/ha | No |
| **[ZoomAgri](https://bichosdecampo.com/el-caso-zoomagri-crearon-un-sistema-para-determinar-en-4-minutos-la-calidad-del-grano-de-cebada-que-luego-sera-cerveza/)** | Lab/calidad | Imagen RGB + IA para pureza varietal y calidad física de grano en ~2–4 min. Método reconocido por MEBAK e **INASE** | Malterías, traders, laboratorios de certificación | No público | **Adyacente e interesante**: el único con método reconocido por INASE — pero para cereales, no papa |
| **[Agree](https://agrolink.com.ar/exclusivo-como-funciona-agree-market-la-plataforma-que-busca-mayor-eficiencia-en-el-comercio-agricola/)** | Comercial/fintech | Marketplace de comercialización de granos + financiamiento digital; maneja cupos, canjes, documentación, posición comercial | Productores, traders, corredores | No público | No |
| **[Ucrop.it](https://ucrop.it/en/why-blockchain-is-key-in-agricultural-traceability/)** | 2 | "Crop story" en blockchain: registro colaborativo, offline-capable, firmado digitalmente, de siembra a cosecha, para certificar sustentabilidad y desbloquear premios | Productores + compradores downstream, 9 países | No público | Trazabilidad **de relato/claims**, no de stock físico por lote |
| **Agrofy / Agrofy Pay** | Marketplace/fintech | Marketplace agro + pagos/crédito `[INFERENCIA — sitio devolvió 403, no verificado]` | Productores, dealers | No verificado | No |
| **Bemyfarm, Kuali, Agrology, Ruuts** | — | **No pude sustanciar nada.** Tratar como no verificado, no como inexistente | — | — | — |
| **[Terragene](https://www.terragene.com/)** | — | Rosarina, pero biotech de esterilización/bioindicadores — **no es software agro** `[INFERENCIA]` | — | — | No |

### 1.2 Los ERP agro argentinos (los "aburridos", y los que más se parecen al problema)

Los vendors que realmente hacen gestión operativa no son los agtech con VC: son locales, con 30 años, y **ninguno publica precio**.

- **[Agri](https://www.agri.com.ar/en/argentina/)** — presupuestación, órdenes de aplicación, control de faenas, control de cosecha, compras, **stock de bodega/depósito**, maquinaria, cuaderno digital, riego, ganadería. Dice 160+ operaciones y 34M+ ha. **Es el que estructuralmente más se acerca** (stock + órdenes de trabajo + lotes) pero no menciona objetos de certificación de semilla.
- **[GestorMax](https://gestormax.com/)** — "cada lote, insumo y labor en una plataforma"; costo por lote, control de stock; familia Gestor 4 / Piloto / Admin, con lectura de facturas por IA y APIs. 1.500+ empresas agro, 30+ años.
- **[SYNAgro](https://synagroweb.com/nuestro-software/)** — dos módulos: contable/comercial (compras, ventas, tesorería, contabilización automática) y productivo (labores mecanizadas, siembra, pulverización, cosecha, maquinaria, servicios de terceros, **artículos e inventario**). 32+ años. Licencias por 3/6/9 usuarios.
- **Physis** — gestión agro / costos y procesos `[INFERENCIA de listado de directorio; sitio 403]`.

`[INFERENCIA]` Sus modelos de datos tienen forma *centro-de-costo-y-lote-de-siembra*. Stock multi-ubicación en frío con linaje de lote y restricciones de categoría/generación sería una **customización, no una configuración**.

### 1.3 Los internacionales: presencia más superficial de lo que parece

- **[Climate FieldView (Bayer)](https://climate.com/es-ar/precios.html)** — el único que **publica precios en Argentina**: Prime USD 299/año, Plus USD 599/año, Premium USD 999/año (licencias de 365 días); FieldView Drive 2.0 USD 499; Combo Cabina 2.0 USD 2.229. Alcance: monitoreo + prescripciones + registro de tareas por campaña. **El sitio no menciona órdenes de trabajo, stock de insumos ni trazabilidad de lotes.**
- **John Deere Operations Center** — plataforma de datos de máquina/lote, mapas, planificación de trabajo `[INFERENCIA — páginas de deere.com devolvieron 404/vacío; no verificado]`. Generalmente gratis con el equipo `[INFERENCIA, no verificado]`.
- **[Granular (Corteva)](https://granular.ag/)** — granular.ag redirige a un login **solo-EEUU**. Granular Business parece discontinuado `[INFERENCIA por cadena de redirects]`. **No hay superficie de producto LatAm.**
- **[Trimble Ag](https://ptxag.com/us/en/products/digital-farming-solutions)** — absorbido en **PTx**: la línea digital ahora es FarmENGAGE, Panorama y NEXT Farming (**solo Alemania**). Farmer Core/Farmer Pro ya no aparecen `[INFERENCIA: retirados/rebrandeados]`.
- **[Agworld](https://www.agworld.com/au/pricing/)** — **el único cuyo feature-set genuinamente matchea** necesidad operativa (registros de compliance, harvest tracking, **inventario**, presupuestos, satélite, colaboración productor–agrónomo–contratista). Precios públicos: Grower Basic USD 1.795/año, Plus USD 3.195/año, Pro USD 3.995/año. **Pero Argentina / Sudamérica no está en su lista de regiones.**
- **Syngenta Cropwise** — syngenta.com.ar devolvió 403, no verificado.
- **[Agroptima](https://www.agroptima.com/es/precios/)** (España, aparece en directorios AR) — cuaderno de explotación oficial en todos los planes; **control de stock en Pro/Premium**; **órdenes de trabajo + planificación/localización de trabajadores en Premium**. Precio por *hectáreas × usuarios*, 3 tiers, 15 días de prueba. Disponibilidad en Argentina no declarada.

### 1.4 Un dato de mercado que vale como evidencia

El directorio de [farm management software de Capterra Argentina](https://www.capterra.com.ar/directory/20061/farm-management/software) lista **cero precios** en todos los vendors. Eso no es un detalle: es evidencia del motion de venta del mercado — demo, cotización, implementación asistida. `[INFERENCIA]` Un ciclo de venta así, para una empresa de ~200 ha, tiene un costo de adquisición que no cierra para el vendor ni para el cliente.

---

## 2. Por qué estas herramientas no le sirven a un productor como Papasud

Esta es la sección del argumento build-vs-buy. Ordenada de la evidencia más dura a la más inferencial.

### 2.1 Están construidas para grano extensivo, no para multiplicación de semilla — **evidencia dura**

El objeto central de Papasud es **`lote = variedad × categoría × generación × parcela × año`**, con reglas legales de avance y de *decomiso de clase*. Ese objeto no existe en ninguno de los productos de arriba. Compará:

Lo que la [Resolución INASE 171/2000](https://www.argentina.gob.ar/normativa/nacional/norma-64565/texto) (+ [Res. 245/1998](https://servicios.infoleg.gob.ar/infolegInternet/anexos/50000-54999/53715/norma.htm)) exige por lote de papa semilla en Argentina:

- **Dos clases** — *Básica* (Preinicial 0 / I / II in vitro o invernáculo; luego campo: **Inicial I–III, Prefundación, Fundación**) y *Certificada* (subcategorías **Registrada** y **Certificada**).
- **Avance generacional lineal estricto**: cada subcategoría deriva de su predecesora. No hay atajos.
- **Preinscripción de lote 30 días antes de la siembra**, con ubicación catastral y **tres años de historia del terreno**; inscripción definitiva antes de la primera inspección, declarando subcategoría, dimensiones y aranceles.
- **Mínimo dos inspecciones de campo** (4–6 semanas post-emergencia; antes de destrucción del follaje); el Art. 11 obliga al inspector a **verificar el origen de la semilla por sus rótulos**.
- **Rótulos oficiales** con clase, categoría, subcategoría, variedad, zona de producción, año de cosecha; **cartelería a campo** con variedad, número de lote y subcategoría desde la siembra.
- **Muestreo post-cosecha 15–30 días después de la destrucción del follaje: 500 tubérculos por lote** (400 patología + 100 pureza varietal), bajo supervisión de inspector.
- Productor inscripto en el **RNCyFS**; el **Técnico Director carga el registro de cultivo por lote en el Sistema de Gestión de INASE**.
- Papa tiene trámite propio: [solicitud de estampillas y DAV/DAM para fiscalización de papa](https://www.argentina.gob.ar/servicio/solicitar-estampillas-y-dav-yo-dam-para-fiscalizacion-de-papa) y [transporte de semilla en fiscalización](https://www.argentina.gob.ar/servicio/transportar-semilla-en-proceso-de-fiscalizacion).

Ahora buscá "generación", "categoría de semilla", "estampilla", "DAV" o "decomiso de clase" en Auravant, SIMA, FieldView o Agri. No están. `[INFERENCIA, pero verificada producto por producto]`

### 2.2 El regulador ya es digital — y el software comercial no habla con él

INASE puso en producción, el **6 de abril de 2026**, nuevos módulos de autogestión en su *Sistema de Gestión y Portal de Servicios*, explícitamente para "garantizar la transparencia y trazabilidad a lo largo de la cadena", incluyendo reutilización de datos de lote para solicitudes DAV repetidas ([INASE moderniza su gestión](https://www.argentina.gob.ar/noticias/inase-moderniza-su-gestion-nuevas-herramientas-digitales-para-el-sector-semillero)).

`[INFERENCIA — y es el hallazgo más filoso del research]` Esto significa que **un productor de papa semilla hoy mantiene categorías/generaciones, estampillas y DAV/DAM en el portal de INASE, y la agronomía en una herramienta no relacionada. Las dos nunca se unen sobre el lote.** El Excel es el pegamento. Ese es literalmente el problema del sponsor.

### 2.3 Cobertura geográfica: el producto correcto no se vende acá

- **Agworld** (el mejor fit funcional) no lista Sudamérica.
- **Granular** colapsó a login solo-EEUU.
- **NEXT Farming** (la pieza más FMIS de Trimble/PTx) es solo Alemania.
- Los **ERP semilleros** europeos (§3) se venden en euros, con partner de implementación, en holandés/inglés.

Esto no es especulación sobre "adopción": es disponibilidad. `[INFERENCIA]` Y donde no hay canal, no hay soporte en español, no hay factura local, no hay quien atienda un martes a las 7 AM en Balcarce.

### 2.4 Nada cubre documentación de exportación

Ver §6. Ni un solo producto de §1 genera un pack de exportación. VUCE tampoco. `[INFERENCIA]` Es el gap más limpio de los cuatro desafíos.

### 2.5 Los barriers "blandos" — flaggeados como inferencia

`[INFERENCIA — no encontré estudios argentinos citables sobre esto en el tiempo disponible; presentarlo como razonamiento, no como dato]`

- **Costo relativo:** FieldView Premium USD 999/año es barato; Agworld Pro USD 3.995/año ya no; un ERP semillero sobre Dynamics 365 con partner es otro orden de magnitud. Para 200 ha, el numerador chico hace que cualquier implementación asistida no cierre.
- **Migración del Excel:** 20+ años de historia en un archivo sin esquema. Ningún producto tiene un onboarding para eso; todos asumen que empezás a cargar desde cero en la campaña que viene. **Eso es un año de historia perdida** — inaceptable para una empresa cuyo activo es el pedigree de sus lotes.
- **Conectividad y entrenamiento:** el operario que reporta desde el lote y el que mueve stock entre 4 ubicaciones no van a abrir un dashboard. (Ver §5: la industria ya convergió a *voz + WhatsApp* justo por esto.)
- **Resistencia al cambio:** una empresa familiar de 140 años no reemplaza su Excel; le pone una capa arriba. **Esto es una guía de diseño, no un obstáculo.**

---

## 3. Software específico de papa semilla / hortícola (y la vara internacional)

Holanda es el benchmark. Lo que hay allá define qué es "serio".

### 3.1 El sistema holandés: NAK

**[NAK](https://www.nak.nl/)** (Nederlandse Algemene Keuringsdienst) inspecciona **~40.000 ha de papa semilla por año** ([nak.nl/aardappelen](https://www.nak.nl/aardappelen/)). Marco UE: [Directiva 2002/56/CE](https://eur-lex.europa.eu/legal-content/en/LSU/?uri=CELEX:32002L0056), con grados fijados por [2014/21/UE](https://eur-lex.europa.eu/eli/dir_impl/2014/20/oj/eng) (**PBTC, PB** pre-basic) y [2014/20/UE](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32014L0020) (**S / SE / E** basic, **A / B** certified).

Lo que se trackea por parcela/lote, del [manual de declaración 2026](https://www.nak.nl/kennisbank/aardappelen/handleiding-aangifte-pootaardappelen-2026/):

- variedad, superficie en ha, nombre identificatorio de parcela, **coordenadas X/Y** tomadas de la declaración de nematodos (AM-verklaring);
- **clase de salida**: PB4→A para producción normal; PBTC y PB1–PB3 para material de tallo/microplanta;
- **número de generación de campo (FG)**;
- tipo de material (tallos / semilla regular / material de mejorador);
- para material importado: **número de productor extranjero + número de certificado de 9 dígitos**;
- al cerrar, el productor recibe **etiquetas de parcela y de tallo** para identificación física en el campo.

Además: la declaración incluye un paso de **autorización** que permite a una empresa nombrada (ej. una casa comercializadora) ver todos los datos de cultivo y certificación ([NAK aangifte](https://www.nak.nl/aardappelen/aangifte/)). Inspección: mínimo dos por temporada desde principios de junio, resultados entregados como reporte en **MijnNAK**, con re-inspección solicitable en 48 h ([NAK Veldkeuring](https://www.nak.nl/aardappelen/veldkeuring-aardappelen/)). Downstream: testeo de laboratorio obligatorio de virus, **inspección de lote** cosechado, *rooimeldingen* (avisos de cosecha), pedido de certificados, **kistenlabels** (etiquetas de trazabilidad por caja/bin) y monitoreo post-cosecha.

**Nótese el paralelo casi 1:1 con la Res. 171/2000 argentina.** El dominio es el mismo; lo que falta acá es el software.

Fitosanitario: **[e-CertNL](https://e-cert.nl/en/)** (NVWA) emite documentos de exportación certificados y empuja ePhytos tanto a **TRACES** (buzón UE) como al **hub ePhyto de la CIPF**, con fallback automático a papel cuando ePhyto no está disponible.

### 3.2 Portales de mejoradores/comercializadores

HZPC opera **[HZPC Online](https://www.hzpc.com/hzpc-online)** para productores y clientes (pedidos, entrega de semilla); los productores registran todas las actividades de temporada — pulverización, fertilización, siembra, entrega — alimentando un sistema de trazabilidad que deja ver al cliente las condiciones de producción ([vía Agroline](http://www.agroline.gr/en/aboutHzpc.html)).

`[INFERENCIA importante]` **Estos portales son propietarios e internos de cooperativa, no productos licenciables.** Un productor independiente no los puede comprar. Igual con Agrico.

### 3.3 ERP semillero: la categoría *comprable* más cercana

- **[Mprise Agriware 365](https://www.mprise-agriware.com/start-material)** (Holanda, sobre Business Central) — ERP hortícola/de material de partida: tracking de líneas parentales y linaje macho/hembra, plantillas de inspección de rinde, monitoreo de plagas y enfermedades, análisis de semilla, **Mobile Inspect App con captura offline a campo**, documentación de tareas de cultivo ("un registro completo de qué se hace, dónde y por quién").
- **[ERP for Seed](https://erpforseed.com/)** (sobre Dynamics 365 F&SCM) — manejo de productores, procesamiento, testeo de calidad, empaque, distribución, finanzas, con **genealogía completa de batch desde lotes de productor hasta producto terminado**, y resultados de germinación/pureza/viabilidad ligados al inventario.
- **[Strinos ERP](https://www.strinos.com/industries/seed)** — inventario, lot tracking, procesamiento, tratamientos, bookings, ventas.
- **[exactllyERP Seed](https://www.exactlly.com/pages/industry/exactllyERP-seed.html)** — cada lote ligado a productor, parcela y registro de ingreso, trazable hacia adelante por procesamiento, testeo, grading y despacho.
- **[inecta Produce Grower](https://www.inecta.com/produce-grower)** — manejo de lote/invernáculo, costo de cultivo, trazabilidad de lote, compliance PTI.
- **[Famous Software](https://support.famoussoftware.com/article/fsma-204-general-summary)** (ERP de empaque) — Traceability Lot Codes, KDEs y CTEs, 2 años de registros, y planillas ordenables para la FDA en 24 h.
- **[Folio3 AgTech Seed Management](https://agtech.folio3.com/seed-management-software/)** — blending, retesteo de germinación, contratación de productores, reporting de compliance.

`[INFERENCIA — y es clave]` **Ninguno es específico de papa semilla.** Los ERP semilleros están construidos alrededor de *semilla verdadera* (% germinación, pureza, blending, tratamientos), no alrededor de **conteo de generaciones vegetativas, límites de generación de campo, decomiso de clase y desclasificación por título viral** — que es de lo que depende la certificación de papa. La lógica papa-específica vive dentro de los sistemas de las autoridades de inspección (MijnNAK, Sistema de Gestión INASE) y de los portales de mejoradores. No se vende.

### 3.4 Almacenamiento: lo único genuinamente papa-específico y comprable

**[Tolsma-Grisnich Vision Control](https://www.tolsmagrisnich.com/en/products/storage/control-technology/vision-control/)** — "computadora de almacenamiento inteligente" que regula temperatura, HR y CO₂ vía ventiladores, compuertas, calefactores y frío mecánico, con monitoreo remoto (temperaturas, horas de marcha, estado, alarmas) por app. Para almacenamiento en cajones construyeron un **sistema de track-and-trace con dos tags RFID por cajón y antenas montadas en el autoelevador** — lo más parecido a un sistema de lote-ubicación hecho a propósito para papa semilla que encontré ([PotatoPro](https://www.potatopro.com/companies/tolsma-grisnich)). Contexto de industria: [Potato News Today](https://www.potatonewstoday.com/2025/05/17/the-future-of-potato-storage-advances-in-ventilation-energy-efficiency-and-storage-automation/), [Potato Business](https://www.potatobusiness.com/pb-special-feature/climate-control-in-potato-storage-system-integration-forecast-logic-and-operational-risk/).

*No verificado:* Omnivent, Miedema/Dewulf, Ellips, Insort (se agotó el presupuesto de búsqueda).

### 3.5 La vara de "trazabilidad seria": FSMA 204

**[FSMA 204](https://www.fda.gov/food/food-safety-modernization-act-fsma/fsma-final-rule-requirements-additional-traceability-records-certain-foods)** es la especificación más filosa de trazabilidad de lote que existe. Define **CTEs** (Critical Tracking Events): cosecha, enfriado, empaque inicial, primera recepción terrestre, envío, recepción, transformación; y **KDEs** (Key Data Elements): traceability lot code, cantidad/UOM, fechas/horas, ubicaciones, descripción de producto, origen y destinatario ([mapa CTE/KDE](https://www.truecommerce.com/blog/fsma-204-kdes-ctes-guide/)). El **Traceability Lot Code se asigna en el empaque inicial o en la transformación**, y PTI lo define como GTIN de caja + número de lote ([guía inecta](https://www.inecta.com/blog/fsma-204-compliance-guide)). Compliance se corrió 30 meses, a **20 de julio de 2028** ([Federal Register, 7-ago-2025](https://www.federalregister.gov/documents/2025/08/07/2025-14967/requirements-for-additional-traceability-records-for-certain-foods-compliance-date-extension)).

`[INFERENCIA]` La papa cruda no está en la Food Traceability List, así que FSMA 204 es un **template de diseño, no una obligación** para Papasud. Pero es la mejor definición disponible de "qué significa trazabilidad en serio", y **el estándar de facto es: responder one-lot-back / one-lot-forward en menos de 24 horas.** Ése es un criterio de demo excelente.

### 3.6 Qué espera una operación seria de papa semilla — checklist

Sintetizado de todo lo anterior (`[INFERENCIA]`, pero anclada en las normas citadas):

1. **Registro de parcelas/lotes con geometría** — coordenadas, ha, ID catastral, historia multi-anual del terreno (3 años en AR; AM-verklaring en NL).
2. **Motor de generación/clase** — objeto central `lote = variedad × clase × generación de campo × parcela × año`, con reglas legales de avance (PB→S→SE→E→A; Preinicial→Inicial→Fundación→Registrada→Certificada) y **decomiso automático** ante hallazgos de inspección.
3. **Genealogía** — lote padre → lote hijo, indefinidamente hacia atrás hasta el origen in vitro/microtubérculo.
4. **Captura de inspección de campo** — móvil offline, 2+ visitas, pureza varietal, virus, daño, evaluación de tolerancias por clase, flujo de re-inspección.
5. **Integración de laboratorio** — resultados ELISA/PCR ligados al lote muestreado, con tamaño de muestra y cadena de custodia.
6. **Intercambio con el regulador** — declaraciones a MijnNAK / Sistema de Gestión INASE, reconciliación de rótulos oficiales y números de estampilla.
7. **Vínculo almacenamiento↔lote** — qué lote está en qué cajón/bin/cámara, con historia climática por depósito e identidad de cajón por RFID/código de barras.
8. **Transformación en grading/empaque** — split/merge con herencia de código de lote, asignación de TLC en el empaque, etiquetas GTIN+lote.
9. **Certificados y fitosanitario** — números de certificado, ePhyto de exportación vía hub/GeNS.
10. **Consulta de recall** — one-lot-back / one-lot-forward, rápido.

### 3.7 ¿Puede un productor argentino de papa semilla comprar algo hoy?

**No — no un producto.** `[INFERENCIA, del gap entre §3.3 y §3.6]` Lo comprable hoy es:

- un **ERP semillero** (Mprise Agriware 365, ERP for Seed, Strinos, exactllyERP) que da genealogía de lote, inspecciones, captura móvil y depósitos — pero **sin modelo de clase/generación de papa y sin integración INASE**, así que las clases se vuelven campos custom y la lógica legal vive en la configuración;
- un **ERP de empaque/produce** (Famous, inecta) para la punta de empaque/TLC/etiquetas;
- **control de clima de almacenamiento con datos** (Tolsma-Grisnich + RFID), que sí es papa-específico pero es hardware bundleado, en euros.

---

## 4. ERP y el "Excel gap"

### 4.1 Sobre qué corre la administración de una PyME agro argentina

Lo verificado:

- **[Tango (Axoft)](https://www.axoft.com/)** — 6 productos: Tango Gestión (ERP PyME/grande), Capital Humano, Punto de Venta, Estudios Contables, Restô, TFactura. Módulos listados: Ventas, Stock, Compras, Importaciones, Proveedores, Tesorería, Contabilidad, IVA, Activo Fijo, Sueldos. Énfasis en compliance ARCA: *"anticipamos a los cambios legales e impositivos, garantizando que tu empresa esté siempre en regla con la ARCA"*. **La página no menciona partidas/lotes, series, múltiples depósitos ni vertical agro.** Sin precios públicos.
- **[Finnegans](https://www.finneg.com/ar/)** — Finnegans GO (ERP cloud) + Quippos (HCM), con división **"Agronegocios"** para *Productores* y *Comercialización de granos*, y plataforma abierta No-Code/Low-Code/Guest-Code. **Los módulos específicos (lotes, campañas, stock multi-depósito, órdenes de trabajo, trazabilidad, documentación de exportación) no están documentados en el sitio.** Sin precios. *Dato relevante:* Finnegans es uno de los integradores listados por Auravant.
- **[Odoo — localización argentina](https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/argentina.html)** — soporta webservices AFIP: `wsfev1` (facturas A/B/C/M), **`wsfexv1` = "Electronic Exportation Invoice… el tipo de documento relacionado es tipo 'E'"**, `wsbfev1` (bono fiscal). Maneja certificados digitales, entornos de prueba/producción, puntos de venta AFIP, sincronización de secuencias, retenciones y percepciones. Módulo `l10n_ar_edi`.

**No verificado** (agotamiento de presupuesto de búsqueda): Bejerman, SAP Business One AR (costo/timeline de implementación), Holistor, Xubio, Colppy, Calipso, Dynamics 365 BC AR, y cualquier estadística de adopción de ERP en PyMEs argentinas (Bolsa de Cereales devolvió 403; Agrofy 403). **No inventar números acá.**

`[INFERENCIA]` El punto útil: **la pieza fiscal ya está resuelta** — Odoo/Tango emiten Factura E contra AFIP sin problema. Lo que no está resuelto es todo lo que va *antes* de la factura: qué lote, de qué generación, en qué cámara, con qué certificado. El ERP arranca donde el problema de Papasud termina.

### 4.2 El "Excel gap": evidencia citable para el pitch

Lo verificado, con números:

- **Tasa de error en fórmulas:** se estima que **"alrededor del 1% de todas las fórmulas en planillas operativas tienen error"** ([Wikipedia — Spreadsheet, sección de errores](https://en.wikipedia.org/wiki/Spreadsheet)).
- **Errores de una sola instancia han excedido los USD 1.000 millones** (misma fuente).
- **Gobernanza (estudio UK 2011):** **57%** de los usuarios de planillas **nunca recibió entrenamiento formal**; **72%** reportó que **ningún departamento interno chequea** sus planillas; solo **13%** tiene revisión de Auditoría Interna; apenas **1%** recibe chequeo del área de riesgo (misma fuente).
- **JPMorgan / London Whale (2012):** pérdida final de **USD 6.200 millones**. JPMorgan admitió ante la SEC *"spreadsheet miscalculations that caused large valuation errors"* ([2012 JPMorgan Chase trading loss](https://en.wikipedia.org/wiki/2012_JPMorgan_Chase_trading_loss)).
- **Reinhart–Rogoff (2013):** Thomas Herndon encontró fallas de codificación mayores en la planilla detrás de *Growth in a Time of Debt*, el paper usado para justificar programas de austeridad europeos 2010–2013 ([Spreadsheet](https://en.wikipedia.org/wiki/Spreadsheet)).
- **Excel corrompe datos silenciosamente:** al 2016, **19,6%** de los artículos publicados con listas de genes en archivos Excel estaban afectados por errores de nombre de gen (Excel convierte `MARCH1` → `1-Mar`, `SEPT2` → `2-Sep`). El comité HUGO tuvo que **renombrar 27 genes** para acomodarse a Excel ([Microsoft Excel](https://en.wikipedia.org/wiki/Microsoft_Excel)).

`[NO VERIFICADO — no usar como cita]` Panko (cifras específicas de cell error rate y % de planillas auditadas con error), EuSpRIG horror stories (sitio 403), Public Health England / 16.000 casos COVID perdidos por límite de filas de XLS (BBC y Guardian no fetcheables — la historia es real y conocida, pero **no la pude verificar en esta sesión**, así que si la usás decilo de memoria y sin número exacto), DeHoratius & Raman sobre inexactitud de registros de inventario (paywall 403).

**La línea de pitch más fuerte y 100% defendible:** *el 19,6% de los papers científicos con listas de genes tienen datos corrompidos por Excel, y JPMorgan perdió USD 6.200 millones con "errores de cálculo en planillas" admitidos ante la SEC. Si eso pasa con auditoría, compliance y equipos de riesgo, ¿qué pasa con una planilla compartida de stock sin control de versiones?*

---

## 5. Los entrantes AI-native (2024–2026): el estado del arte de la demo

Esta es la sección más accionable para mañana. **La industria ya convergió a un patrón, y hay competidores argentinos.**

### 5.1 Captura de datos a campo por voz — el patrón ganó

| Producto | Interfaz | UX notable |
|---|---|---|
| **[FieldData](https://news.agrofy.com.ar/noticia/211402/ia-ganaderia-dos-jovenes-vieron-problema-campo-y-crearon-plataforma-que-ordena)** 🇦🇷 | **WhatsApp** (audio o texto) | **El más relevante.** Fundado por Julian Saavedra (agrónomo) y Marcus Stromeyer, se conocieron por un asesoramiento CREA. Cualquiera del equipo — a caballo, en la camioneta, arriba del tractor — manda un audio o texto; la IA lo estructura. Mensajes reales: *"Movimos 20 vacas del Lote 1 al Lote 12"*, *"Llovió 22 mm"*. 100+ productores en la nota; [otra fuente](https://www.defrentealcampo.com.ar/fielddata-amplia-su-sistema-de-gestion-por-whatsapp-e-integra-la-agricultura/) reporta 1.500+ establecimientos en AR/EEUU/Australia, y que **acaban de extenderse de ganadería a agricultura**. Sin precio público. |
| **[Celio IA](https://celioia.com/)** 🇦🇷 | **Telegram** (sin instalar app) | **Solapamiento directo con la Vertical 02.** Registro de siembra, pulverización, fertilización y cosecha en segundos; **generación de órdenes de trabajo asignadas a contratistas y personal**; consultas agronómicas (productos, dosis, precios de insumos); reportes en **PDF y Excel** en minutos; 30 GB de storage por usuario. Testimonio: *"Es como tener un asistente personal. Registro desde el campo con Telegram"*. Dice 1.000+ ingenieros agrónomos. |
| **[Numanac](https://www.numanac.com/)** | App de voz | **El mejor UX de referencia.** *"Speak in any language, records auto-structure"* — **180+ idiomas**. Ejemplo de una sola locución: *"Light aphid pressure on the north block, about 15 per leaf, no natural enemies yet. Rescout next week"* → log de scouting estructurado con **ubicación (GPS 38.54, −121.75), timestamp, clima, tags de plaga y fecha de seguimiento auto-completados**. **Full functionality sin señal, auto-sync al reconectar.** Capa de consulta llamada **Alma**: *"ask anything, answered from the record"*. |
| **[PlantVoice Field Notes](https://plantvoice.farm/field-notes/)** | Chat estilo WhatsApp | *"a smart chat that lets agronomists and operators record every activity directly from the field"*. Texto, **notas de voz y fotos**. Flujo de 4 pasos: Captura → Interpretación IA (*"identifica tipo de actividad, cantidad, tiempo y contexto"*) → Transformación en reportes/datos consultables/historial → Compartir instantáneo. Trazabilidad: *"records ready for audits, inspections and supply-chain certifications"*. Español entre los 6 idiomas. |
| **[Fulcrum Audio FastFill](https://www.fulcrumapp.com/blog/audio-fastfill-field-data-capture-using-voice-dictation/)** | Botón único en formulario | *"Tap one button, then speak naturally… eliminating the need to tab, touch, or click through fields"*. Una locución llena **múltiples campos** — texto, números, checkboxes — y **navega sub-preguntas, opciones en cascada y lógica condicional**. Claim: equipos **≥20% más rápidos**. |
| **[Agro4Data](https://agro4data.com/casos-de-uso/introducir-datos-agricolas-por-whatsapp)** | WhatsApp (voz + foto) | Foto del estado del cultivo + audio, sin clicks; sincroniza a ERP y cuadernos de campo existentes. |
| **[Herd Advisor](https://www.drovers.com/news/beef-production/voice-record-app-reinvents-cattle-management)** | Voz | Voice-first para ganadería, construido por un ganadero; lanzado en CattleCon 2026. |
| **[Tellia](https://tellia.com/)** | Voz | *"turns real conversations into clean, structured records that sync to databases"*. |

**Lectura estratégica.** Que existan FieldData y Celio IA es **buena noticia para el pitch, no mala**: valida que el patrón voz/WhatsApp funciona y se adopta en Argentina, y ninguno de los dos toca lo que hace único a Papasud — **categoría/generación de semilla, stock en 4 cámaras y documentación de exportación**. Celio IA hace órdenes de trabajo pero para agricultura extensiva genérica; FieldData viene de ganadería. `[INFERENCIA]` Si un juez menciona "esto ya existe", la respuesta es: *sí, la captura por voz ya es commodity — el valor está en el modelo de dominio que hay debajo.*

### 5.2 "Chat con tus datos operativos" — patrones de confianza

**[Snowflake Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)** es la mejor referencia de diseño para no alucinar números:

- **Semantic views** en vez de schema crudo: *"Semantic Views provide a business-friendly layer over your data by defining logical tables, dimensions, facts, metrics, and relationships"* — metadata rica que el LLM sí entiende.
- **Devuelve siempre el SQL generado** junto a la respuesta en texto: *"analyst responses have both text and SQL responses"* — permite auditar la consulta.
- **Verified Query Repository**: ejemplos verificados que guían la generación.
- **Separación generación/ejecución**: el SQL generado se ejecuta contra el motor Snowflake, nunca SQL arbitrario del usuario.
- Limitación admitida honestamente: *"If a conversation includes too many turns or the user shifts intent frequently, Cortex Analyst might struggle to interpret the follow-up questions."*

`[NO VERIFICADO]` Databricks Genie (la doc que fetcheé era solo un hub de navegación); Julius, Hex Magic, Zenlytic, Fabric Copilot.

### 5.3 Generación de documentos con IA (logística/comercio)

- **[Expedock](https://www.expedock.com/blog/8-freight-forwarding-systems-use-cases-to-automate-repetitive-documentation-data-workflows-for-freight-organizations)** — IA propietaria que lee documentos no estructurados y extrae datos: crea shipments desde bills of lading y booking confirmations (timestamps, números de contenedor, ETA/ETD), y extrae **line-by-line de facturas comerciales y packing lists**. Integra con Cargowise. Posicionado para forwarders con 10.000+ documentos/mes, 90%+ de accuracy, deploy en <30 días.
- **[Vooma](https://procurementmag.com/technology-and-ai/vooma-ai-secures-series-a-funding)** — agentes IA sobre voz, email y texto para el ciclo de vida de la carga en trucking (USD 800+ mil millones).

`[INFERENCIA clave]` Notá la dirección: **toda la industria de IA documental en comercio va de documento → datos (extracción)**. Casi nadie va de **datos → documento (generación)**, que es exactamente lo que necesita Papasud. Eso es un gap real, no una carencia de investigación.

---

## 6. Documentación de exportación argentina: ¿existe software o es manual?

**Es manual.** Con evidencia.

### 6.1 El set de documentos

El despachante de aduana asesora en la confección de la **factura E de exportación, el Packing List, el certificado de origen, la factura proforma y la cobranza internacional** ([Despachante de Aduana](https://despachante-aduana.com/cuales-son-los-requisitos-para-importar-y-exportar-en-argentina/)). Exportadores, despachantes y ATA deben tener inscripción vigente en el **Registro de Operadores de Comercio Exterior** de AFIP/ARCA ([argentina.gob.ar](https://www.argentina.gob.ar/servicio/gestionar-la-certificacion-para-exportar-productos-de-origen-vegetal)).

### 6.2 Lo que el Estado sí digitalizó — y lo que dejó afuera

**[VUCE / VUCEA](https://www.argentina.gob.ar/vuce/preguntas-frecuentes)** — *"una herramienta de facilitación del comercio exterior que permite optimizar y unificar digitalmente la información y documentación"*. Conecta despachantes, entidades financieras, operadores logísticos y cámaras emisoras de certificados de origen. **Pero:**

- **Los certificados de origen siguen en papel**: *"Por el momento no… los certificados se mantendrán en soporte papel"*.
- **VUCE no genera documentos comerciales** — ni facturas ni packing lists. Solo permisos y trámites de organismos.
- **Su uso es voluntario**: se puede operar alternativamente por SIM y gestionar trámites por TAD.

**[Portal de Certificación Fitosanitaria de Exportación (SENASA)](https://www.argentina.gob.ar/senasa/portal-de-certificacion-fitosanitaria-de-exportacion)** — permite consultar requisitos por país de destino, iniciar trámites (**SIG-FITO**), acceder a protocolos y obtener certificados. **Es parcialmente self-service**: la emisión del certificado requiere autorización presencial de un funcionario — *"Solamente un funcionario público que esté técnicamente calificado y debidamente autorizado por una ONPF puede expedir un certificado fitosanitario."* También referencia **Cert-POV**. `[Manual de usuario externo del sistema de gestión de Certificación Fitosanitaria](https://biblioteca.senasa.gob.ar/items/show/4322)`.

**Certificados de origen digitales**: [CAME](https://www.redcame.org.ar/secretarias/44/certificados-de-origen) emite CODs digitales **solo para Brasil, Chile, Paraguay y Uruguay**, con carga vía plataforma web y firma digital por TOKEN. La [CAC](https://origen.cac.com.ar/) tiene su propio sistema. `[INFERENCIA]` O sea: portales separados, por cámara, por destino, cada uno con su login y su re-tipeo.

**ePhyto**: el [IPPC ePhyto Solution](https://www.ippc.int/en/ephyto/) es un hub que intercambia certificados XML entre ONPFs, con **GeNS** como sistema nacional gratuito y browser-based para países sin sistema propio. **La participación de Argentina no la pude verificar** (la página de estado no listó países). Holanda ya empuja ePhytos vía [e-CertNL](https://e-cert.nl/en/) al hub y a TRACES.

### 6.3 Veredicto

`[INFERENCIA, pero bien sostenida]` Para un exportador argentino de papa, el pack de exportación se arma así: **plantillas de Word/Excel para proforma, factura E y packing list; re-tipeo de los mismos datos en SIG-FITO (SENASA), en el portal de la cámara para el certificado de origen, y en el SIM/VUCE vía despachante.** El ERP resuelve la factura fiscal (Odoo `wsfexv1`, tipo E). Nadie resuelve **la orquestación**: un lote de stock → los 5 documentos con los mismos números, sin re-tipeo, con los datos de trazabilidad de lote y certificación que el destino exige.

**Los tools internacionales de comercio (Descartes, e2open, ONESOURCE) y los AI entrants (Expedock, Vooma) van en la dirección opuesta: extraen datos de documentos, no generan documentos desde datos.** No verificado: software de despachantes argentinos (Depot, TradeSoft, Zeus), Nuvocargo, Cargoflip, Shipsy — se agotó el presupuesto.

**Recomendación de priorización:** de los tres desafíos, **el copiloto de documentación de exportación (Vertical 03 / N03) es el gap más limpio y menos poblado del landscape entero.** Es el que menos riesgo tiene de que alguien diga "eso ya existe".

---

## "Por qué no compran un producto existente"

*Respuesta de 20 segundos, en orden de fuerza. Los tres primeros bullets son los que hay que decir; los últimos dos son munición si insisten.*

1. **El objeto que Papasud administra no existe en ningún software del mercado.** El lote de papa semilla es `variedad × categoría × generación × parcela × año`, con avance generacional lineal obligatorio y decomiso de clase por inspección (Res. INASE 171/2000). Buscá "generación" o "estampilla" en Auravant, SIMA, FieldView o Agri: no está. Los ERP semilleros que sí tienen genealogía de lote están construidos para *semilla verdadera* — germinación, pureza, blending — no para conteo de generaciones vegetativas.

2. **El software agtech argentino es monitoreo satelital, no gestión.** Frontec, S4, Kilimo, FieldView: NDVI, prescripciones, estimación de rinde. Cero stock, cero órdenes de trabajo, cero documentación. Y el único producto internacional cuyo feature-set realmente matchea — Agworld, con inventario y registros de compliance a USD 1.795–3.995/año — **no se vende en Sudamérica**. Granular colapsó a solo-EEUU; la pieza más FMIS de Trimble es solo Alemania.

3. **El regulador ya se digitalizó y el software comercial no le habla.** INASE puso módulos de autogestión en producción en abril de 2026, con papa teniendo su propio trámite de estampillas y DAV/DAM. Hoy las categorías y generaciones viven en el portal de INASE, la agronomía en otra herramienta, y **las dos nunca se unen sobre el lote. El Excel es el pegamento.** Eso no es un problema de compra: es un problema de integración de dominio.

4. **Comprar cuesta más que el problema.** Ni un vendor del directorio de Capterra Argentina publica precio: todo es demo, cotización e implementación asistida. Para 200 ha eso no cierra. Y ningún producto tiene onboarding para 20 años de historia sin esquema — todos asumen que empezás de cero la campaña que viene, o sea, tirar el pedigree de los lotes, que es el activo de la empresa.

5. **Documentación de exportación: no hay producto, punto.** VUCE dice explícitamente que los certificados de origen siguen en papel y que no genera documentos comerciales; el certificado fitosanitario de SENASA requiere firma presencial de funcionario; los CODs digitales de CAME solo cubren Brasil/Chile/Paraguay/Uruguay. Y toda la industria de IA documental en comercio va de documento→datos, no de datos→documento. **Nadie está construyendo esto.**

---

## Ideas de UX robadas

*Patrones concretos, con la fuente de la que vienen. Ordenados por retorno en una demo de 5 minutos.*

**Captura a campo**

- **Una locución = un registro completo, con campos auto-inferidos.** De **Numanac**: *"Presión leve de pulgón en el cuadro norte, unos 15 por hoja, sin enemigos naturales todavía. Re-monitorear la semana que viene"* → log estructurado con GPS, timestamp, clima, tags de plaga **y fecha de seguimiento** auto-completados. **Robar esto textual: la demo es la locución.** El wow no es la transcripción, es los campos que el usuario nunca dijo y aparecieron igual.
- **Un solo botón, hablá natural, y la IA navega la lógica condicional del formulario.** De **Fulcrum Audio FastFill**: *"Tap one button, then speak naturally… eliminating the need to tab, touch, or click through fields"* — llena texto, números y checkboxes, y **atraviesa sub-preguntas y opciones en cascada**. Claim de ≥20% más rápido: usable como benchmark.
- **La interfaz es WhatsApp, no una app.** De **FieldData** 🇦🇷 y **PlantVoice**: chat estilo WhatsApp con audio, texto y foto. Cero instalación, cero entrenamiento, cero resistencia. FieldData lo justifica explícitamente por el contexto: el operario está *a caballo, en la camioneta o arriba del tractor*. **Para Papasud, con operarios de campo y de depósito, esto es casi obligatorio.**
- **Offline total con auto-sync.** De **Numanac**: *"full functionality without signal, auto-syncs on reconnect"*. En la demo: mostrar el modo avión. Es 15 segundos y mata la objeción de conectividad.
- **Multi-idioma sin configurar.** De **Numanac** (180+ idiomas): relevante si hay personal estacional.
- **Confirmación editable antes de commitear.** `[INFERENCIA — es el patrón que falta explícito en las fuentes, y precisamente por eso diferencia]` Mostrar los campos extraídos como *chips* editables con un tap para corregir antes de guardar. En un dominio donde una generación mal asignada arruina la certificación de un lote, **el paso de confirmación es una feature, no una fricción.**

**Chat sobre los datos históricos**

- **Devolver siempre el SQL/consulta generada junto a la respuesta.** De **Cortex Analyst**: *"analyst responses have both text and SQL responses"*. Auditable = creíble. En una demo con un dueño de empresa familiar de 140 años, esto es lo que compra confianza.
- **Capa semántica en vez de schema crudo.** De **Cortex Analyst** (*semantic views*: tablas lógicas, dimensiones, hechos, métricas y relaciones "business-friendly"). Traducido a Papasud: **no le des el Excel al LLM — dale un modelo de dominio con `lote`, `categoría`, `generación`, `campaña`, `cámara`.** Es la diferencia entre una demo que funciona y una que alucina en vivo.
- **Repositorio de consultas verificadas.** De **Cortex Analyst** (*Verified Query Repository*): un set de preguntas frecuentes ya validadas, que además sirve como pantalla de arranque ("probá preguntar…") y garantiza que la demo no falle.
- **Citar la fila/campaña que sustenta el número.** Ya está en las features refinadas de [[papasud]] (F1.3) y coincide con la dirección de toda la categoría. Mantenerlo.
- **Admitir la limitación en voz alta.** De la propia doc de Cortex Analyst, que reconoce que se degrada con muchos turnos o cambios de intención. `[INFERENCIA]` Decir en la demo *"si la pregunta es ambigua, pregunta en vez de inventar"* — y **mostrarlo pidiendo una aclaración**. Es el momento más creíble que puede tener un demo de LLM sobre datos.

**Trazabilidad y stock**

- **Etiquetas físicas generadas por el sistema, atadas al lote.** De **NAK**: al cerrar la declaración el productor recibe **etiquetas de parcela y de tallo**, y downstream hay **kistenlabels** (etiquetas por cajón). De **Tolsma-Grisnich**: **dos tags RFID por cajón con antenas en el autoelevador**. El principio a robar: **el sistema imprime la identidad física; el mundo real no se tipea, se escanea.**
- **La pregunta de recall como criterio de éxito.** De **FSMA 204** / **Famous Software** (planillas ordenables para la FDA en 24 h). El estándar de facto es **one-lot-back / one-lot-forward en menos de 24 horas**. **Hacer eso el cierre de la demo: "¿de dónde salió este lote y a dónde fue todo lo que produjo?" → respuesta en 2 segundos.**
- **Split/merge con herencia de código de lote.** De **FSMA 204** (TLC asignado en empaque/transformación) y **ERP for Seed** (*"complete batch genealogy from grower lots to finished goods"*). Cuando un lote se divide entre cámaras o se junta para un pedido, el linaje tiene que sobrevivir.
- **Autorización granular para que un tercero vea el lote.** De **NAK**: la declaración de parcela incluye un paso que permite a una empresa nombrada (ej. la casa comercializadora) ver todos los datos de cultivo y certificación. `[INFERENCIA]` Traducido: un link de solo-lectura por lote para PepsiCo o para un cliente de exportación. Barato de construir, muy vendible.
- **Captura de inspección con plantillas y offline.** De **Mprise Agriware 365**: plantillas de inspección de rinde, monitoreo de plagas y **Mobile Inspect App offline**, con *"un registro completo de qué se hace, dónde y por quién"*.

**Documentación de exportación**

- **Invertir la dirección de la industria: datos → documento.** Todo el mercado de IA documental en comercio (**Expedock**, **Vooma**) extrae datos de documentos. Papasud necesita lo contrario. `[INFERENCIA]` El patrón a construir: **un lote de stock seleccionado genera los 5 documentos con los mismos números, y muestra en pantalla qué campo salió de dónde.**
- **Extracción line-by-line como formato de salida.** De **Expedock** (extrae ítem por ítem de facturas comerciales y packing lists): usar esa estructura *al revés* — el packing list se arma desde los movimientos de stock por lote, con la línea trazable al cajón.
- **Fallback automático a papel.** De **e-CertNL**, que empuja ePhyto a TRACES y al hub de la CIPF y **cae automáticamente a papel cuando ePhyto no está disponible**. Diseñar asumiendo que el canal digital falla — muy realista para Argentina, y demuestra madurez de producto ante un juez que conoce el rubro.

---

## Fuentes principales

Agtech AR: [Auravant](https://www.auravant.com/en/pricing-en/) · [SIMA](https://blog.sima.ag/2026/expoagro-2026-sima-agtech/) · [S4](https://www.syngentagroupventures.com/s4) · [Frontec](https://www.infoespacial.com/texto-diario/mostrar/3568958/empresa-argentina-frontec-utiliza-satelites-mejorar-gestion-agricola) · [Kilimo](https://kilimo.com/) · [DeepAgro](https://www.deepagro.com/es/tech.html) · [ZoomAgri](https://bichosdecampo.com/el-caso-zoomagri-crearon-un-sistema-para-determinar-en-4-minutos-la-calidad-del-grano-de-cebada-que-luego-sera-cerveza/) · [Agree](https://agrolink.com.ar/exclusivo-como-funciona-agree-market-la-plataforma-que-busca-mayor-eficiencia-en-el-comercio-agricola/) · [Ucrop.it](https://ucrop.it/en/why-blockchain-is-key-in-agricultural-traceability/) · [Agri](https://www.agri.com.ar/en/argentina/) · [GestorMax](https://gestormax.com/) · [SYNAgro](https://synagroweb.com/nuestro-software/) · [Capterra AR](https://www.capterra.com.ar/directory/20061/farm-management/software)

Internacionales: [FieldView precios AR](https://climate.com/es-ar/precios.html) · [Agworld pricing](https://www.agworld.com/au/pricing/) · [Granular](https://granular.ag/) · [PTx](https://ptxag.com/us/en/products/digital-farming-solutions) · [Agroptima](https://www.agroptima.com/es/precios/)

Certificación: [INASE certificación](https://www.argentina.gob.ar/inase/certificacionsemillas) · [INASE modernización 2026](https://www.argentina.gob.ar/noticias/inase-moderniza-su-gestion-nuevas-herramientas-digitales-para-el-sector-semillero) · [INASE estampillas/DAV papa](https://www.argentina.gob.ar/servicio/solicitar-estampillas-y-dav-yo-dam-para-fiscalizacion-de-papa) · [Res. 171/2000](https://www.argentina.gob.ar/normativa/nacional/norma-64565/texto) · [Res. 245/1998](https://servicios.infoleg.gob.ar/infolegInternet/anexos/50000-54999/53715/norma.htm) · [NAK](https://www.nak.nl/aardappelen/) · [NAK manual 2026](https://www.nak.nl/kennisbank/aardappelen/handleiding-aangifte-pootaardappelen-2026/) · [Dir. 2014/20/UE](https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32014L0020) · [INTA Balcarce lab papa](https://www.argentina.gob.ar/inta/tematicas/laboratorios/red/balcarce-papa) · [FSMA 204](https://www.fda.gov/food/food-safety-modernization-act-fsma/fsma-final-rule-requirements-additional-traceability-records-certain-foods)

Software semillero/almacenamiento: [Mprise Agriware](https://www.mprise-agriware.com/start-material) · [ERP for Seed](https://erpforseed.com/) · [Strinos](https://www.strinos.com/industries/seed) · [inecta](https://www.inecta.com/produce-grower) · [Famous FSMA 204](https://support.famoussoftware.com/article/fsma-204-general-summary) · [Tolsma-Grisnich Vision Control](https://www.tolsmagrisnich.com/en/products/storage/control-technology/vision-control/) · [HZPC Online](https://www.hzpc.com/hzpc-online)

ERP / Excel: [Axoft/Tango](https://www.axoft.com/) · [Finnegans](https://www.finneg.com/ar/) · [Odoo AR](https://www.odoo.com/documentation/18.0/applications/finance/fiscal_localizations/argentina.html) · [Spreadsheet errors](https://en.wikipedia.org/wiki/Spreadsheet) · [JPMorgan 2012](https://en.wikipedia.org/wiki/2012_JPMorgan_Chase_trading_loss) · [Excel gene names](https://en.wikipedia.org/wiki/Microsoft_Excel)

AI-native: [FieldData](https://news.agrofy.com.ar/noticia/211402/ia-ganaderia-dos-jovenes-vieron-problema-campo-y-crearon-plataforma-que-ordena) · [FieldData agricultura](https://www.defrentealcampo.com.ar/fielddata-amplia-su-sistema-de-gestion-por-whatsapp-e-integra-la-agricultura/) · [Celio IA](https://celioia.com/) · [Numanac](https://www.numanac.com/) · [PlantVoice](https://plantvoice.farm/field-notes/) · [Fulcrum Audio FastFill](https://www.fulcrumapp.com/blog/audio-fastfill-field-data-capture-using-voice-dictation/) · [Agro4Data](https://agro4data.com/casos-de-uso/introducir-datos-agricolas-por-whatsapp) · [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst) · [Expedock](https://www.expedock.com/blog/8-freight-forwarding-systems-use-cases-to-automate-repetitive-documentation-data-workflows-for-freight-organizations) · [Vooma](https://procurementmag.com/technology-and-ai/vooma-ai-secures-series-a-funding)

Exportación: [VUCE FAQ](https://www.argentina.gob.ar/vuce/preguntas-frecuentes) · [SENASA cert. fitosanitaria](https://www.argentina.gob.ar/senasa/portal-de-certificacion-fitosanitaria-de-exportacion) · [SENASA manual usuario](https://biblioteca.senasa.gob.ar/items/show/4322) · [CAME cert. origen](https://www.redcame.org.ar/secretarias/44/certificados-de-origen) · [Despachante de aduana — requisitos](https://despachante-aduana.com/cuales-son-los-requisitos-para-importar-y-exportar-en-argentina/) · [IPPC ePhyto](https://www.ippc.int/en/ephyto/) · [e-CertNL](https://e-cert.nl/en/)
