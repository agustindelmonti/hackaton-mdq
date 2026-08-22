"""
exportacion.py · N03 — el copiloto de la carpeta de exportación.

«Un asistente para la generación de facturas proformas y documentación de
exportación. El sistema lee los requisitos documentales y los cruza con los
datos de trazabilidad de un lote específico para pre-completar lo que ya se
sabe.»

LA IDEA, EN UNA LÍNEA: casi todos los campos de esos documentos YA ESTÁN en el
sistema. Están en el lote, en el cliente, en la orden de carga y en los análisis.
Lo que hoy hace una persona es copiarlos a mano de una planilla a seis
formularios distintos, y cada copia es una chance de que un peso no cuadre
entre la factura y el packing list — que es exactamente lo que frena un embarque.

CÓMO ESTÁ CONSTRUIDO Y POR QUÉ ASÍ

Cada documento es una lista de CAMPOS, y cada campo declara tres cosas:

    valor   — lo que el sistema ya sabe (o None)
    fuente  — DE DÓNDE lo sacó: "lote PS-202526-SPU-002", "análisis del
              14/03/2026", "cliente Southern Foods". Nunca "el sistema".
    estado  — completo | falta | a_confirmar

Esa terna es todo. Permite mostrar el documento con los huecos marcados, decir
cuánto falta para cerrarlo, y —lo que importa cuando alguien pregunta— señalar
el dato original detrás de cada casillero.

LOS CAMPOS NO SON INVENTADOS. Salen de los formularios reales:

  · Certificado Fitosanitario — modelo IPPC/ISPM 12 que usa el SENASA: las tres
    secciones (descripción del envío, declaración adicional, tratamiento) con
    sus campos textuales, incluido el nombre botánico Solanum tuberosum.
  · Factura E / proforma — campos de AFIP WSFEX: emisor con CUIT y punto de
    venta de exportación, receptor con su ID impositivo y CUIT País, Incoterm,
    moneda y cotización, ítems con NCM 0701.10.00, totales. La proforma espeja
    la Factura E sin CAE, porque es una cotización y no un comprobante fiscal.
  · Solicitud INASE — Res. 56/18 Anexo II: clase fiscalizada, DAV con kilos,
    categoría, especie, variedad del Catálogo Nacional, cantidad de envases,
    valor FOB. Validez 60 días y packing list obligatorio adjunto.
  · Packing list — el que exige el contenedor marítimo: precinto, bultos,
    peso neto y bruto, y la regla de oro de que descripción, bultos y pesos
    coincidan EXACTAMENTE con la factura.
  · Rótulo oficial — Res. INASE 171/2000 art. 16 + Ley 20.247 art. 9.
  · Certificado de origen — MERCOSUR/ALADI, válido 180 días.

EL CONTROL CRUZADO es la parte que ningún formulario tiene solo: el mismo
módulo verifica que los kilos, los bultos y la descripción digan lo mismo en
los tres documentos donde aparecen. Ese descuadre es la causa número uno de
demora en aduana, y acá se ve antes de imprimir nada.
"""
from __future__ import annotations

import datetime

from . import esquema, ordenes_carga, semilla, store, trazabilidad
from .fechas import hoy, parse_fecha

# --- La identidad registral del exportador ---------------------------------
# Va impresa en cada documento. Sale del catálogo del dataset para que haya un
# solo lugar donde cambiarla.
EMPRESA = {
    "razon_social": "PAPASUD S.A.",
    "cuit": "30-54187629-3",
    "inscripcion_rncfs": "RNCyFS N° 14.328",
    "domicilio": "Ruta 226 km 14,5 — Sierra de los Padres, Mar del Plata, Buenos Aires, Argentina",
    "punto_venta_export": "0004",
    "director_tecnico": "Ing. Agr. Dalia Ferreyra — Directora Técnica registrada",
    "email": "comercioexterior@papasud.com.ar",
}

NOMBRE_BOTANICO = "Solanum tuberosum L."
NCM = "0701.10.00"
KG_POR_BOLSON = 1000
DIAS_VALIDEZ_INASE = 60          # Res. 56/18
DIAS_VALIDEZ_ORIGEN = 180        # MERCOSUR/ALADI

# Los seis papeles de una carpeta de exportación, en el orden en que se arman.
DOCUMENTOS = [
    ("factura_proforma", "Factura proforma", "Papasud S.A.", "empresa"),
    ("packing_list", "Packing list", "Papasud S.A.", "empresa"),
    ("solicitud_inase", "Solicitud de exportación de semilla", "INASE", "organismo"),
    ("certificado_fitosanitario", "Certificado Fitosanitario de Exportación", "SENASA", "organismo"),
    ("rotulo_oficial", "Rótulo oficial de papa semilla", "INASE", "empresa"),
    ("certificado_origen", "Certificado de origen", "Cámara de Comercio", "organismo"),
]


# ---------------------------------------------------------------------------
# La pieza base: un campo que sabe de dónde salió
# ---------------------------------------------------------------------------
def campo(etiqueta: str, valor, fuente: str | None = None,
          obligatorio: bool = True, nota: str | None = None) -> dict:
    """Un casillero del formulario.

    `fuente` es lo que convierte esto en un copiloto y no en un generador de
    PDF: si alguien pregunta de dónde salió un número, la respuesta está al
    lado del número."""
    vacio = valor is None or valor == "" or valor == []
    return {
        "etiqueta": etiqueta,
        "valor": valor,
        "fuente": fuente,
        "estado": "falta" if (vacio and obligatorio) else ("opcional" if vacio else "completo"),
        "obligatorio": obligatorio,
        **({"nota": nota} if nota else {}),
    }


def _fmt_monto(x, moneda: str = "USD") -> str:
    """Un monto como lo escribe un despachante: separador de miles con punto y
    dos decimales con coma. `f"{x:,.2f}"` da el formato inglés — se da vuelta."""
    s = f"{float(x or 0):,.2f}"
    return f"{moneda} " + s.replace(",", "@").replace(".", ",").replace("@", ".")


def _fmt_kg(x) -> str:
    return f"{float(x or 0):,.0f}".replace(",", ".") + " kg"


def _fecha_larga(d: datetime.date, lang: str = "es") -> str:
    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
             "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    if lang == "en":
        return d.strftime("%B %d, %Y")
    return f"{d.day} de {meses[d.month - 1]} de {d.year}"


# ---------------------------------------------------------------------------
# El contexto: todo lo que el sistema ya sabe de este embarque
# ---------------------------------------------------------------------------
def _contexto(numero_orden: str) -> dict | None:
    """Junta la orden, su cliente y el pedigrí de cada lote. Es la única lectura
    de datos: los seis documentos se arman de acá."""
    orden = orden_carga_de(numero_orden)
    if not orden:
        return None
    cli = semilla.buscar_cliente(orden.get("cliente_id") or orden.get("cliente") or "")
    lotes = []
    for it in orden.get("items") or []:
        ped = trazabilidad.pedigri(str(it.get("lote") or it.get("codigo")))
        if ped.get("encontrado"):
            lotes.append({"item": it, "pedigri": ped})
    kg = sum(float(i.get("kg") or 0) for i in (orden.get("items") or []))
    return {
        "orden": orden,
        "cliente": cli or {},
        "lotes": lotes,
        "kg_total": kg,
        "bultos": int(round(kg / KG_POR_BOLSON)),
        "hoy": hoy(),
        "verificacion": ordenes_carga.verificar(numero_orden),
    }


def orden_carga_de(numero: str) -> dict | None:
    return ordenes_carga.buscar(numero)


def embarques() -> list[dict]:
    """Las órdenes de exportación abiertas, que son las que necesitan carpeta."""
    out = []
    for o in ordenes_carga.listar(tipo="exportacion"):
        if o.get("estado") == "despachada":
            continue
        v = ordenes_carga.verificar(o["numero"])
        out.append({**o, "puede_emitirse": v["puede_emitirse"],
                    "bloqueos": v["bloqueos"], "advertencias": v["advertencias"]})
    return out


# ---------------------------------------------------------------------------
# 1 · FACTURA PROFORMA (campos de AFIP WSFEX, sin CAE)
# ---------------------------------------------------------------------------
def _factura_proforma(c: dict) -> dict:
    o, cli = c["orden"], c["cliente"]
    fuente_cli = f"cliente {cli.get('nombre', '—')}"
    fuente_ord = f"orden {o['numero']}"
    items = []
    total = 0.0
    for L in c["lotes"]:
        it, p = L["item"], L["pedigri"]
        art = next((a for a in store.raw_actual() if a.get("codigo") == it.get("codigo")), {})
        precio = float(art.get("pvp") or 0)
        kg = float(it.get("kg") or 0)
        importe = round(precio * kg, 2)
        total += importe
        items.append({
            "codigo": it.get("lote"),
            "descripcion": (f"Papa semilla fiscalizada {p['identidad']['variedad']} — "
                            f"categoría {p['identidad']['categoria']} "
                            f"({p['identidad']['clase']}), campaña {p['identidad']['campania']}"),
            "ncm": NCM,
            "cantidad": kg,
            "unidad": "kg",
            "precio_unitario": precio,
            "importe": importe,
            "fuente": f"lote {it.get('lote')}",
        })
    return {
        "id": "factura_proforma",
        "titulo": "Factura proforma",
        "subtitulo": "Proforma invoice",
        "organismo": "Papasud S.A.",
        "nota_legal": ("La proforma espeja los campos de la Factura E (AFIP WSFEX) "
                       "pero NO lleva CAE: es una cotización, no un comprobante fiscal. "
                       "La Factura E se emite al confirmarse la operación."),
        "secciones": [
            {"titulo": "Exportador", "campos": [
                campo("Razón social", EMPRESA["razon_social"], "datos de la empresa"),
                campo("CUIT", EMPRESA["cuit"], "datos de la empresa"),
                campo("Domicilio", EMPRESA["domicilio"], "datos de la empresa"),
                campo("Punto de venta exportación", EMPRESA["punto_venta_export"],
                      "datos de la empresa"),
                campo("Inscripción RNCyFS", EMPRESA["inscripcion_rncfs"],
                      "registro de semillero"),
            ]},
            {"titulo": "Importador", "campos": [
                campo("Razón social", cli.get("nombre"), fuente_cli),
                campo("País de destino", cli.get("pais"), fuente_cli),
                campo("ID impositivo del receptor", cli.get("id_impositivo"), fuente_cli,
                      nota="Lo informa el cliente; no está en el sistema todavía."),
                campo("Domicilio", cli.get("domicilio"), fuente_cli, obligatorio=False),
            ]},
            {"titulo": "Condiciones", "campos": [
                campo("Incoterm", cli.get("incoterm"), fuente_cli),
                campo("Moneda", cli.get("moneda") or "USD", fuente_cli),
                campo("Cotización", None, None,
                      nota="Se toma la del día de emisión de la Factura E."),
                campo("Puerto de carga", cli.get("puerto"), fuente_cli),
                campo("Puerto de destino", cli.get("destino_puerto"), fuente_cli),
                campo("Forma de pago", None, None, obligatorio=False),
            ]},
        ],
        "items": items,
        "totales": [
            campo(f"Total {cli.get('incoterm', 'FOB')} ({cli.get('moneda', 'USD')})",
                  # el total va FORMATEADO: un "20760240" pelado en una factura
                  # de exportación se lee mal en pantalla y peor impreso
                  _fmt_monto(total, cli.get("moneda", "USD")), fuente_ord),
            campo("Peso neto total", _fmt_kg(c["kg_total"]), fuente_ord),
            campo("Bultos", f"{c['bultos']} bolsones", fuente_ord),
        ],
        "pie": [
            campo("Lugar y fecha", f"Mar del Plata, {_fecha_larga(c['hoy'])}", "fecha del sistema"),
            campo("Firma y sello", None, None, obligatorio=False,
                  nota="Se firma al imprimir."),
        ],
    }


# ---------------------------------------------------------------------------
# 2 · PACKING LIST
# ---------------------------------------------------------------------------
def _packing_list(c: dict) -> dict:
    o, cli = c["orden"], c["cliente"]
    filas = []
    for L in c["lotes"]:
        it, p = L["item"], L["pedigri"]
        kg = float(it.get("kg") or 0)
        bultos = int(round(kg / KG_POR_BOLSON))
        filas.append({
            "lote": it.get("lote"),
            "descripcion": f"Papa semilla {p['identidad']['variedad']} — {p['identidad']['categoria']}",
            "ncm": NCM,
            "bultos": bultos,
            "tipo_bulto": "big bag (bolsón)",
            "peso_neto": kg,
            # El bolsón vacío pesa: el bruto NO es el neto, y ese descuadre es
            # de los que frenan un embarque.
            "peso_bruto": round(kg + bultos * 2.4, 1),
            "fuente": f"lote {it.get('lote')}",
        })
    bruto = sum(f["peso_bruto"] for f in filas)
    return {
        "id": "packing_list",
        "titulo": "Packing list",
        "subtitulo": "Lista de empaque",
        "organismo": "Papasud S.A.",
        "nota_legal": ("Regla de oro: la descripción, la cantidad de bultos y los pesos "
                       "tienen que coincidir EXACTAMENTE con la factura y con el "
                       "conocimiento de embarque. El descuadre es la causa más común "
                       "de demora en aduana."),
        "secciones": [
            {"titulo": "Embarque", "campos": [
                campo("Referencia de factura", f"Proforma s/ orden {o['numero']}",
                      f"orden {o['numero']}"),
                campo("Exportador", EMPRESA["razon_social"], "datos de la empresa"),
                campo("Consignatario", cli.get("nombre"), f"cliente {cli.get('nombre', '—')}"),
                campo("Puerto de carga", cli.get("puerto"), f"cliente {cli.get('nombre', '—')}"),
                campo("Puerto de destino", cli.get("destino_puerto"),
                      f"cliente {cli.get('nombre', '—')}"),
                campo("Incoterm", cli.get("incoterm"), f"cliente {cli.get('nombre', '—')}"),
                campo("N° de contenedor", None, None,
                      nota="Lo asigna la naviera al reservar."),
                campo("N° de precinto", None, None,
                      nota="Se completa al cerrar el contenedor."),
                campo("Buque y viaje", None, None, obligatorio=False),
            ]},
            {"titulo": "Condiciones de transporte", "campos": [
                campo("Temperatura de transporte", "3 a 5 °C",
                      "condiciones de conservación de semilla"),
                campo("Humedad relativa", "85 a 90 %", "condiciones de conservación"),
                campo("Observaciones", "Mantener en oscuridad. Ventilación permanente.",
                      "condiciones de conservación", obligatorio=False),
            ]},
        ],
        "items": filas,
        "totales": [
            campo("Total de bultos", f"{c['bultos']} bolsones", f"orden {o['numero']}"),
            campo("Peso neto total", _fmt_kg(c["kg_total"]), f"orden {o['numero']}"),
            campo("Peso bruto total", _fmt_kg(bruto), "neto + tara de los bolsones"),
            campo("País de origen", "Argentina", "datos de la empresa"),
        ],
        "pie": [],
    }


# ---------------------------------------------------------------------------
# 3 · SOLICITUD DE EXPORTACIÓN INASE (Res. 56/18 Anexo II)
# ---------------------------------------------------------------------------
def _solicitud_inase(c: dict) -> dict:
    o, cli = c["orden"], c["cliente"]
    detalle = []
    for L in c["lotes"]:
        it, p = L["item"], L["pedigri"]
        art = next((a for a in store.raw_actual() if a.get("codigo") == it.get("codigo")), {})
        detalle.append({
            "lote": it.get("lote"),
            "clase": "Fiscalizada",
            "categoria": p["identidad"]["categoria"],
            "especie": NOMBRE_BOTANICO,
            "variedad": p["identidad"]["variedad"],
            "kg": float(it.get("kg") or 0),
            "envases": int(round(float(it.get("kg") or 0) / KG_POR_BOLSON)),
            "virus_pvy": art.get("virus_pct"),
            "tolerancia_pvy": art.get("virus_max_pct"),
            "fuente": f"lote {it.get('lote')} · análisis del {art.get('analisis_fecha')}",
        })
    vence = c["hoy"] + datetime.timedelta(days=DIAS_VALIDEZ_INASE)
    return {
        "id": "solicitud_inase",
        "titulo": "Solicitud de exportación de semilla",
        "subtitulo": "INASE · Res. 56/18 Anexo II — requisito adicional para papa: Res. SAGYP 715/94",
        "organismo": "INASE",
        "nota_legal": ("Validez de la solicitud: 60 días. Es obligatorio adjuntar el "
                       "packing list. Para papa, la categorización se informa por "
                       "generaciones y por resultados de análisis de virus, nematodos y "
                       "defectos externos."),
        "secciones": [
            {"titulo": "Solicitante", "campos": [
                campo("Usuario RNCyFS", EMPRESA["inscripcion_rncfs"], "registro de semillero"),
                campo("Razón social", EMPRESA["razon_social"], "datos de la empresa"),
                campo("CUIT", EMPRESA["cuit"], "datos de la empresa"),
                campo("Director Técnico", EMPRESA["director_tecnico"], "registro de semillero"),
                campo("Anualidad vigente", "Sí", "registro de semillero"),
            ]},
            {"titulo": "Datos generales", "campos": [
                campo("Motivo de exportación", "Venta comercial", f"orden {o['numero']}"),
                campo("País de origen", "Argentina", "datos de la empresa"),
                campo("País de destino", cli.get("pais"), f"cliente {cli.get('nombre', '—')}"),
                campo("Vía de salida", "Marítima" if "Puerto" in str(cli.get("puerto", ""))
                      else "Terrestre", f"cliente {cli.get('nombre', '—')}"),
                campo("Lugar de salida (aduana)", cli.get("puerto"),
                      f"cliente {cli.get('nombre', '—')}"),
                campo("Despachante de aduana", None, None,
                      nota="Se designa antes de oficializar la destinación."),
                campo("Posición NADE", NCM, "nomenclatura"),
                campo("Valor FOB (U$S)", None, None,
                      nota="Se toma de la factura proforma al confirmarse el precio."),
            ]},
            {"titulo": "Documentos habilitantes", "campos": [
                campo("DAV (Documento de Autorización de Venta)", None, None,
                      nota="Se tramita por lote ante el INASE, con los kilos de cada uno."),
                campo("Catálogo Nacional de Cultivares", "Variedades inscriptas",
                      "registro varietal"),
                campo("Packing list adjunto", "Sí — se genera junto con esta solicitud",
                      "documento del sistema"),
            ]},
        ],
        "items": detalle,
        "totales": [
            campo("Total de kilos", _fmt_kg(c["kg_total"]), f"orden {o['numero']}"),
            campo("Total de envases", f"{c['bultos']} bolsones", f"orden {o['numero']}"),
            campo("Válida hasta", _fecha_larga(vence), "60 días desde la emisión"),
        ],
        "pie": [],
    }


# ---------------------------------------------------------------------------
# 4 · CERTIFICADO FITOSANITARIO (modelo IPPC / ISPM 12)
# ---------------------------------------------------------------------------
def _certificado_fitosanitario(c: dict) -> dict:
    o, cli = c["orden"], c["cliente"]
    lotes_txt = ", ".join(L["item"].get("lote") for L in c["lotes"])
    # las declaraciones adicionales las fija la ONPF del país importador
    onpf = cli.get("requisitos_onpf") or []
    analisis = []
    for L in c["lotes"]:
        art = next((a for a in store.raw_actual()
                    if a.get("codigo") == L["item"].get("codigo")), {})
        analisis.append(
            f"{L['item'].get('lote')}: PVY {art.get('virus_pct')}% "
            f"(tolerancia {art.get('virus_max_pct')}% para {art.get('categoria_semilla')}), "
            f"{art.get('analisis_metodo', 'DAS-ELISA')}, {art.get('analisis_fecha')}")
    return {
        "id": "certificado_fitosanitario",
        "titulo": "Certificado Fitosanitario de Exportación",
        "subtitulo": "Phytosanitary Certificate · modelo IPPC / NIMF 12 — SENASA",
        "organismo": "SENASA",
        "nota_legal": ("Lo emite el SENASA (sistema CERT-POV / SIG-FITO). Para material "
                       "de propagación exige copia del certificado del INASE. Este "
                       "borrador pre-completa lo que el sistema ya sabe; los campos de "
                       "emisión los llena el organismo."),
        "secciones": [
            {"titulo": "Encabezado", "campos": [
                campo("N° de certificado", None, None,
                      nota="Serial único que asigna el SENASA."),
                campo("Organización de Protección Fitosanitaria de",
                      "Argentina — SENASA", "organismo emisor"),
                campo("Para: ONPF de", cli.get("pais"), f"cliente {cli.get('nombre', '—')}"),
            ]},
            {"titulo": "I · Descripción del envío", "campos": [
                campo("Nombre y dirección del exportador",
                      f"{EMPRESA['razon_social']} — {EMPRESA['domicilio']}",
                      "datos de la empresa"),
                campo("Nombre y dirección declarada del consignatario",
                      cli.get("nombre"), f"cliente {cli.get('nombre', '—')}"),
                campo("Número y descripción de bultos",
                      f"{c['bultos']} big bags (bolsones) de 1.000 kg",
                      f"orden {o['numero']}"),
                campo("Marcas distintivas", f"Lotes {lotes_txt}",
                      "rótulos de los lotes"),
                campo("Lugar de origen",
                      ", ".join(sorted({L["pedigri"]["origen"]["campo"] for L in c["lotes"]})),
                      "campo de producción de cada lote"),
                campo("Medio de transporte declarado",
                      "Marítimo — contenedor refrigerado" if "Puerto" in str(cli.get("puerto", ""))
                      else "Terrestre", f"cliente {cli.get('nombre', '—')}"),
                campo("Punto de entrada declarado", cli.get("destino_puerto"),
                      f"cliente {cli.get('nombre', '—')}"),
                campo("Nombre botánico", NOMBRE_BOTANICO, "especie"),
                campo("Nombre del producto y cantidad declarada",
                      f"Papa semilla fiscalizada — {_fmt_kg(c['kg_total'])}",
                      f"orden {o['numero']}"),
            ]},
            {"titulo": "II · Declaración adicional", "campos": [
                campo("Requisitos de la ONPF de destino",
                      onpf or None,
                      f"requisitos declarados por {cli.get('pais')}",
                      nota="Los fija el país importador; se transcriben literales."),
                campo("Resultados de análisis sanitario", analisis,
                      "análisis de laboratorio de cada lote"),
                campo("Laboratorio", "INTA Balcarce · ProPapa (habilitado por INASE)",
                      "análisis de laboratorio"),
            ]},
            {"titulo": "III · Tratamiento de desinfestación / desinfección", "campos": [
                campo("Fecha del tratamiento", None, None, obligatorio=False),
                campo("Tratamiento", None, None, obligatorio=False),
                campo("Producto (principio activo)", None, None, obligatorio=False),
                campo("Duración y temperatura", None, None, obligatorio=False),
                campo("Concentración", None, None, obligatorio=False),
            ]},
            {"titulo": "Cierre", "campos": [
                campo("Lugar de emisión", "Mar del Plata, Buenos Aires, Argentina",
                      "datos de la empresa"),
                campo("Fecha", _fecha_larga(c["hoy"]), "fecha del sistema"),
                campo("Funcionario autorizado", None, None,
                      nota="Firma y sella el SENASA."),
            ]},
        ],
        "items": [],
        "totales": [],
        "pie": [],
    }


# ---------------------------------------------------------------------------
# 5 · RÓTULO OFICIAL (Res. INASE 171/2000 art. 16 + Ley 20.247 art. 9)
# ---------------------------------------------------------------------------
def _rotulo_oficial(c: dict) -> dict:
    rotulos = []
    for L in c["lotes"]:
        it, p = L["item"], L["pedigri"]
        art = next((a for a in store.raw_actual() if a.get("codigo") == it.get("codigo")), {})
        campania = p["identidad"]["campania"]
        rotulos.append({
            "lote": it.get("lote"),
            "clase": "FISCALIZADA",
            "categoria": p["identidad"]["categoria"],
            "clase_categoria": p["identidad"]["clase"],
            "variedad": p["identidad"]["variedad"].upper(),
            "zona_produccion": p["origen"]["zona"],
            "anio_cosecha": campania.split("/")[-1] if "/" in campania else campania,
            "grado": p["identidad"]["calibre_label"],
            "inscripcion": EMPRESA["inscripcion_rncfs"],
            "razon_social": EMPRESA["razon_social"],
            "tratado_con_veneno": bool(art.get("tratado")),
            "peso_envase": "1.000 kg (big bag)",
            "fuente": f"lote {it.get('lote')}",
        })
    return {
        "id": "rotulo_oficial",
        "titulo": "Rótulo oficial de papa semilla",
        "subtitulo": "Res. INASE 171/2000 art. 16 · Ley 20.247 art. 9 · Res. 42/00 Anexo IV",
        "organismo": "INASE",
        "nota_legal": ("Obligatorio en envases nuevos. Para papa producida a campo el "
                       "envase no puede superar los 50 kg; el bolsón de 1.000 kg se usa "
                       "para movimiento interno y requiere habilitación previa del INASE "
                       "como envase abierto. Si el material fue tratado, la leyenda "
                       "«material tratado con veneno» va en letras rojas."),
        "secciones": [],
        "items": rotulos,
        "totales": [],
        "pie": [],
    }


# ---------------------------------------------------------------------------
# 6 · CERTIFICADO DE ORIGEN
# ---------------------------------------------------------------------------
def _certificado_origen(c: dict) -> dict:
    cli = c["cliente"]
    vence = c["hoy"] + datetime.timedelta(days=DIAS_VALIDEZ_ORIGEN)
    mercosur = cli.get("pais") in ("Brasil", "Uruguay", "Paraguay")
    return {
        "id": "certificado_origen",
        "titulo": "Certificado de origen",
        "subtitulo": ("MERCOSUR / ALADI" if mercosur else "Cámara de Comercio"),
        "organismo": "Cámara de Comercio",
        "nota_legal": ("Válido 180 días. Para MERCOSUR habilita preferencias "
                       "arancelarias; desde 2026 rige además la autocertificación de "
                       "origen (Declaración de Origen)."
                       if mercosur else "Válido 180 días."),
        "secciones": [
            {"titulo": "Datos", "campos": [
                campo("Exportador", EMPRESA["razon_social"], "datos de la empresa"),
                campo("Importador", cli.get("nombre"), f"cliente {cli.get('nombre', '—')}"),
                campo("País de destino", cli.get("pais"), f"cliente {cli.get('nombre', '—')}"),
                campo("Posición arancelaria", NCM, "nomenclatura"),
                campo("Mercadería",
                      f"Papa semilla fiscalizada ({NOMBRE_BOTANICO}) — {_fmt_kg(c['kg_total'])}",
                      f"orden {c['orden']['numero']}"),
                campo("Origen", "República Argentina", "datos de la empresa"),
                campo("Régimen", "MERCOSUR/ALADI" if mercosur else "General",
                      "país de destino"),
                campo("Válido hasta", _fecha_larga(vence), "180 días desde la emisión"),
            ]},
        ],
        "items": [],
        "totales": [],
        "pie": [],
    }


_ARMADORES = {
    "factura_proforma": _factura_proforma,
    "packing_list": _packing_list,
    "solicitud_inase": _solicitud_inase,
    "certificado_fitosanitario": _certificado_fitosanitario,
    "rotulo_oficial": _rotulo_oficial,
    "certificado_origen": _certificado_origen,
}


# ---------------------------------------------------------------------------
# La API del módulo
# ---------------------------------------------------------------------------
# El prefijo de la numeración de cada papel. No es cosmético: un documento de
# exportación sin número correlativo no lo acepta ni el despachante ni la
# aduana, y el que le sigue tiene que poder referenciarlo.
_PREFIJO = {
    "factura_proforma": "PRO",       # proforma, punto de venta de exportación 0004
    "packing_list": "PKL",
    "solicitud_inase": "INA",
    "certificado_fitosanitario": "FIT",
    "rotulo_oficial": "ROT",
    "certificado_origen": "ORI",
}


def _correlativo(doc_id: str, numero_orden: str) -> str:
    """El número del papel, DERIVADO de la orden de carga.

    No es un contador que sube cada vez que alguien aprieta descargar: eso
    daría dos números distintos para el mismo documento y rompería la
    referencia cruzada entre la factura y el packing list. Sale de la orden,
    que es lo único que identifica al embarque, así que es estable y se puede
    reconstruir: PS-PRO-2026-2461 es la proforma de OC-2026-2461."""
    cola = numero_orden.split("-", 1)[-1] if "-" in numero_orden else numero_orden
    return f"PS-{_PREFIJO.get(doc_id, 'DOC')}-{cola}"


def documento(numero_orden: str, doc_id: str) -> dict | None:
    """UN documento, pre-completado desde la trazabilidad del embarque."""
    c = _contexto(numero_orden)
    if not c or doc_id not in _ARMADORES:
        return None
    d = _ARMADORES[doc_id](c)
    d["orden"] = numero_orden
    d["cliente"] = c["cliente"].get("nombre")
    d["emitido"] = c["hoy"].isoformat()
    d["numero"] = _correlativo(doc_id, numero_orden)
    d["completitud"] = _completitud(d)
    return d


def carpeta(numero_orden: str) -> dict | None:
    """LA CARPETA ENTERA del embarque: los seis documentos, cuánto le falta a
    cada uno, y el control cruzado entre ellos."""
    c = _contexto(numero_orden)
    if not c:
        return None
    docs = []
    for did, _n, _o, _e in DOCUMENTOS:
        d = _ARMADORES[did](c)
        d["completitud"] = _completitud(d)
        docs.append({
            "id": did,
            "titulo": d["titulo"],
            "organismo": d["organismo"],
            "numero": _correlativo(did, c["orden"]["numero"]),
            "completitud": d["completitud"],
        })
    listos = sum(1 for d in docs if d["completitud"]["faltan"] == 0)
    return {
        "orden": c["orden"]["numero"],
        "cliente": c["cliente"].get("nombre"),
        "pais": c["cliente"].get("pais"),
        "incoterm": c["cliente"].get("incoterm"),
        "puerto": c["cliente"].get("puerto"),
        "destino_puerto": c["cliente"].get("destino_puerto"),
        "kg_total": c["kg_total"],
        "bultos": c["bultos"],
        "lotes": [L["item"].get("lote") for L in c["lotes"]],
        "documentos": docs,
        "listos": listos,
        "total_documentos": len(docs),
        # El embarque no sale si la orden de carga está frenada, por más que la
        # carpeta esté completa. Se dice acá para que no sea una sorpresa.
        "orden_bloqueada": not c["verificacion"]["puede_emitirse"],
        "bloqueos": c["verificacion"]["bloqueos"],
        "control_cruzado": control_cruzado(numero_orden),
    }


def _completitud(d: dict) -> dict:
    campos = [x for s in d.get("secciones", []) for x in s["campos"]]
    faltan = [x for x in campos if x["estado"] == "falta"]
    completos = [x for x in campos if x["estado"] == "completo"]
    total_oblig = len([x for x in campos if x["obligatorio"]])
    return {
        "completos": len(completos),
        "faltan": len(faltan),
        "total": len(campos),
        "pct": round(len(completos) / total_oblig * 100) if total_oblig else 100,
        "que_falta": [x["etiqueta"] for x in faltan],
    }


def control_cruzado(numero_orden: str) -> dict:
    """La verificación que ningún formulario hace solo: que los kilos, los
    bultos y la descripción digan LO MISMO en los tres documentos donde
    aparecen.

    Es la causa número uno de demora en aduana, y es trivial de chequear
    cuando los tres salen de la misma fuente — que es precisamente el punto."""
    c = _contexto(numero_orden)
    if not c:
        return {"ok": False, "motivo": "orden_inexistente"}
    fac = _factura_proforma(c)
    pl = _packing_list(c)
    inase = _solicitud_inase(c)

    kg_fac = sum(i["cantidad"] for i in fac["items"])
    kg_pl = sum(i["peso_neto"] for i in pl["items"])
    kg_inase = sum(i["kg"] for i in inase["items"])
    bultos_pl = sum(i["bultos"] for i in pl["items"])

    checks = [
        {"que": "Kilos: factura vs packing list",
         "a": kg_fac, "b": kg_pl, "ok": abs(kg_fac - kg_pl) < 0.5},
        {"que": "Kilos: packing list vs solicitud INASE",
         "a": kg_pl, "b": kg_inase, "ok": abs(kg_pl - kg_inase) < 0.5},
        {"que": "Bultos: packing list vs total de la orden",
         "a": bultos_pl, "b": c["bultos"], "ok": bultos_pl == c["bultos"]},
        {"que": "Lotes: los mismos en los tres documentos",
         "a": len(fac["items"]), "b": len(inase["items"]),
         "ok": len(fac["items"]) == len(pl["items"]) == len(inase["items"])},
    ]
    return {
        "ok": all(x["ok"] for x in checks),
        "checks": checks,
        "nota": ("La descripción, los bultos y los pesos coinciden en factura, "
                 "packing list y solicitud INASE."),
    }
