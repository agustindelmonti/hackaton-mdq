"""
dominio.py · Las constantes del negocio de la semilla de papa.

Todo lo de acá sale de la operación real de Papasud y de la normativa argentina
que la rige. Vive aparte del generador porque el BACKEND también las necesita
(categorías INASE, calibres, rangos de temperatura): son reglas del rubro, no
datos sembrados.

FUENTES (verificadas, no inventadas):

  · Resolución INASE 171/2000 — categorías y subcategorías de semilla de papa,
    calibres por grado en milímetros, tolerancias y rotulado de envases.
      - Clase BÁSICA:      Preinicial 0 / I / II (condiciones controladas),
                           Inicial I / II / III, Prefundación, Fundación (a campo)
      - Clase CERTIFICADA: Registrada, Certificada
      - Calibres (Art. 25):  grado 1 = >45 a 90 mm · grado 2 = >33 a 45 mm
                             grado 3 = >20 a 33 mm · grado 4 = libre
        Tolerancia: 5% en peso del grado inmediato inferior y 5% del superior.
      - Envases (Art. 23): máximo 50 kg a campo; 20 kg para Preiniciales.
      - Rótulo (Art. 16): clase fiscalizada, categoría y subcategoría, variedad,
        zona de producción, año de cosecha, y N° de inscripción en el Registro
        Nacional de Comercio y Fiscalización de Semillas.

  · Conservación de semilla (bibliografía de poscosecha): almacenamiento por
    más de tres meses a 3–5 °C. Por encima de 4 °C se rompe la dormancia y
    arranca la brotación. La dormancia dura entre 7 y 120 días según variedad,
    estado de cosecha y condiciones. La temperatura alta acelera el
    envejecimiento fisiológico del tubérculo y acorta la dormancia.

  · Exportación de semilla desde Argentina: certificado de exportación del
    INASE (Res. SAGYP 715/94 para papa), Certificado Fitosanitario de
    Exportación del SENASA (que exige copia del certificado INASE para material
    de propagación), permiso de embarque de Aduana, y los requisitos
    fitosanitarios que fije la ONPF del país importador.
"""
from __future__ import annotations

# --- Las cuatro ubicaciones ------------------------------------------------
# Tres frigoríficos y un galpón, como dice el brief. El galpón NO tiene frío:
# es acondicionamiento y armado de carga, y por eso es el que corre contra el
# reloj — lo que entra ahí ya empezó a envejecer.
UBICACIONES = [
    {"id": "sierra", "nombre": "Frigorífico Sierra de los Padres",
     "tipo": "frigorifico", "camaras": ["Cámara 1", "Cámara 2", "Cámara 3", "Cámara 4"],
     "capacidad_kg": 2_850_000, "temp_objetivo": 4.0, "temp_tolerancia": 1.0,
     "direccion": "Ruta 226 km 14,5 — Sierra de los Padres"},
    {"id": "ruta226", "nombre": "Frigorífico Ruta 226",
     "tipo": "frigorifico", "camaras": ["Cámara A", "Cámara B", "Cámara C"],
     "capacidad_kg": 2_100_000, "temp_objetivo": 4.0, "temp_tolerancia": 1.0,
     "direccion": "Ruta 226 km 31 — Partido de General Pueyrredón"},
    {"id": "batan", "nombre": "Frigorífico Batán",
     "tipo": "frigorifico", "camaras": ["Cámara 1", "Cámara 2"],
     "capacidad_kg": 1_450_000, "temp_objetivo": 3.5, "temp_tolerancia": 1.0,
     "direccion": "Parque Industrial Batán — Mar del Plata"},
    {"id": "chapadmalal", "nombre": "Galpón Chapadmalal",
     "tipo": "galpon", "camaras": ["Sector Norte", "Sector Sur"],
     "capacidad_kg": 900_000, "temp_objetivo": None, "temp_tolerancia": None,
     "direccion": "Camino Viejo a Chapadmalal km 8"},
]
UBIC_POR_ID = {u["id"]: u for u in UBICACIONES}


def ubicacion_nombre(uid: str) -> str:
    return UBIC_POR_ID[uid]["nombre"]


# --- Variedades ------------------------------------------------------------
# Las que se multiplican como semilla en el sudeste bonaerense. Innovator y
# Atlantic son las industriales (bastón y chip): son las que van al circuito de
# PepsiCo. Spunta manda en consumo fresco.
VARIEDADES = [
    {"id": "spunta", "nombre": "Spunta", "destino": "consumo fresco",
     "dormancia_dias": 78, "peso_relativo": 0.29},
    {"id": "innovator", "nombre": "Innovator", "destino": "industria (bastón)",
     "dormancia_dias": 102, "peso_relativo": 0.24},
    {"id": "atlantic", "nombre": "Atlantic", "destino": "industria (chip)",
     "dormancia_dias": 94, "peso_relativo": 0.18},
    {"id": "daisy", "nombre": "Daisy", "destino": "consumo fresco",
     "dormancia_dias": 71, "peso_relativo": 0.12},
    {"id": "asterix", "nombre": "Asterix", "destino": "consumo fresco / industria",
     "dormancia_dias": 88, "peso_relativo": 0.10},
    {"id": "kennebec", "nombre": "Kennebec", "destino": "industria (bastón)",
     "dormancia_dias": 84, "peso_relativo": 0.07},
]
VAR_POR_ID = {v["id"]: v for v in VARIEDADES}

# --- Categorías INASE ------------------------------------------------------
# `orden` es la posición en la escala de multiplicación: cuanto más chico, más
# arriba en el pedigrí (y más caro el kilo). `clase` es la fiscalización.
CATEGORIAS = [
    {"id": "preinicial_2", "nombre": "Preinicial II", "clase": "Básica", "orden": 1,
     "ambiente": "condiciones controladas", "costo_kg": 2_140.0,
     "peso_relativo": 0.02, "virus_max_pct": 0.0},
    {"id": "preinicial_3", "nombre": "Preinicial III", "clase": "Básica", "orden": 2,
     "ambiente": "condiciones controladas", "costo_kg": 1_685.0,
     "peso_relativo": 0.03, "virus_max_pct": 0.0},
    {"id": "inicial_1", "nombre": "Inicial I", "clase": "Básica", "orden": 3,
     "ambiente": "campo", "costo_kg": 1_186.0,
     "peso_relativo": 0.08, "virus_max_pct": 0.2},
    {"id": "inicial_2", "nombre": "Inicial II", "clase": "Básica", "orden": 4,
     "ambiente": "campo", "costo_kg": 894.0,
     "peso_relativo": 0.17, "virus_max_pct": 0.6},
    {"id": "inicial_3", "nombre": "Inicial III", "clase": "Básica", "orden": 5,
     "ambiente": "campo", "costo_kg": 713.0,
     "peso_relativo": 0.21, "virus_max_pct": 1.0},
    {"id": "prefundacion", "nombre": "Prefundación", "clase": "Básica", "orden": 6,
     "ambiente": "campo", "costo_kg": 608.0,
     "peso_relativo": 0.16, "virus_max_pct": 1.6},
    {"id": "fundacion", "nombre": "Fundación", "clase": "Básica", "orden": 7,
     "ambiente": "campo", "costo_kg": 521.0,
     "peso_relativo": 0.14, "virus_max_pct": 2.0},
    {"id": "registrada", "nombre": "Registrada", "clase": "Certificada", "orden": 8,
     "ambiente": "campo", "costo_kg": 428.0,
     "peso_relativo": 0.13, "virus_max_pct": 6.0},
    {"id": "certificada", "nombre": "Certificada", "clase": "Certificada", "orden": 9,
     "ambiente": "campo", "costo_kg": 356.0,
     "peso_relativo": 0.06, "virus_max_pct": 15.0},
]

# Los virus que se fiscalizan y cómo se analizan. La tolerancia declarada arriba
# es sobre PVY, que es el que manda; los otros tres se informan igual en el
# análisis. En las categorías de laboratorio (in vitro) la tolerancia es 0%,
# igual que la de mezcla varietal.
VIRUS_FISCALIZADOS = ["PVY", "PVX", "PLRV", "PVS"]
METODO_ANALISIS = "DAS-ELISA"
LABORATORIO = "INTA Balcarce · ProPapa (habilitado por INASE)"

CAT_POR_ID = {c["id"]: c for c in CATEGORIAS}

# --- Calibres (Res. INASE 171/2000, Art. 25) -------------------------------
# El grado se DECLARA en el rótulo y el calibre medido tiene que caer adentro.
# Un lote cuyo calibre medido queda afuera del rango de su grado es un dato mal
# configurado — el rótulo miente, y en exportación eso frena un embarque.
CALIBRES = {
    1: {"min_mm": 45.0, "max_mm": 90.0, "label": "Grado 1 (45–90 mm)"},
    2: {"min_mm": 33.0, "max_mm": 45.0, "label": "Grado 2 (33–45 mm)"},
    3: {"min_mm": 20.0, "max_mm": 33.0, "label": "Grado 3 (20–33 mm)"},
    4: {"min_mm": None, "max_mm": None, "label": "Grado 4 (libre)"},
}
CALIBRE_TOLERANCIA_PCT = 5.0   # Art. 25: 5% en peso del grado contiguo

# --- Grados por PESO (Res. INASE 217/2002, art. 22) ------------------------
# Ojo, no es lo mismo que lo de arriba: los calibres en milímetros aplican al
# TUBÉRCULO SEMILLA producido a campo; estos grados por peso en gramos aplican
# al MINITUBÉRculo de las categorías Preiniciales, que sale de invernáculo y se
# cuenta por unidad, no por kilo. Confundirlos es el tipo de error que un
# productor detecta al toque.
GRADOS_PESO = {
    0: {"min_g": None, "max_g": 5.0, "label": "Grado 0 (menos de 5 g)"},
    1: {"min_g": 5.0, "max_g": 15.0, "label": "Grado 1 (5 a 15 g)"},
    2: {"min_g": 15.0, "max_g": 25.0, "label": "Grado 2 (15 a 25 g)"},
    3: {"min_g": 25.0, "max_g": 40.0, "label": "Grado 3 (25 a 40 g)"},
    4: {"min_g": 40.0, "max_g": 60.0, "label": "Grado 4 (40 a 60 g)"},
    5: {"min_g": 60.0, "max_g": None, "label": "Grado 5 (más de 60 g)"},
}
GRADO_PESO_TOLERANCIA_PCT = 5.0        # mismo 5% de desvío fuera de grado
MAX_UNIDADES_POR_ENVASE = 2_000        # micro/minitubérculos por envase
MAX_MICROPLANTAS_POR_CONJUNTO = 1_000

# --- Envases y conservación ------------------------------------------------
KG_POR_BOLSON = 1_000          # big bag: la unidad con la que se mueve la cámara
KG_MAX_ENVASE_CAMPO = 50       # Art. 23
KG_MAX_ENVASE_PREINICIAL = 20  # Art. 23

TEMP_MIN_CONSERVACION = 3.0    # °C — conservación por más de 3 meses (CIP/INTA)
TEMP_MAX_CONSERVACION = 5.0
HUMEDAD_MIN_PCT = 85           # humedad relativa: por debajo, el tubérculo se deshidrata
HUMEDAD_MAX_PCT = 90           # por encima, condensación y pudrición
# Oscuridad total: la luz genera solanina y verdeo. Y antes de despachar, el
# lote vuelve a temperatura ambiente de forma CONTROLADA: si no, condensa.
TEMP_ROMPE_DORMANCIA = 4.0     # por encima de esto arranca la brotación

# El frío es lo que compra tiempo: a 3–5 °C el reloj fisiológico del tubérculo
# corre mucho más lento y la brotación se posterga hasta que el lote sale de
# cámara. Un lote guardado en el galpón (sin frío) corre a reloj natural — por
# eso el galpón es tránsito y no depósito, y por eso lo que entra ahí tiene que
# salir. Este factor es lo que separa "tengo semilla para la plantación de
# primavera" de "se me brotó todo en agosto".
FACTOR_FRIO = 3.2              # multiplica la dormancia en cámara refrigerada
FACTOR_SIN_FRIO = 1.0

# --- Documentación de exportación (organismos reales) ----------------------
# Cada requisito declara de dónde sale el dato: por eso el copiloto puede
# pre-completar lo que ya sabe y pedir sólo lo que falta.
DOCS_EXPORTACION = [
    {"id": "factura_proforma", "nombre": "Factura proforma",
     "organismo": "Papasud S.A.", "emite": "empresa",
     "requiere": ["cliente", "incoterm", "lotes", "kilos", "precio_unitario", "moneda"]},
    {"id": "packing_list", "nombre": "Packing list",
     "organismo": "Papasud S.A.", "emite": "empresa",
     "requiere": ["lotes", "bultos", "peso_neto", "peso_bruto", "contenedor"]},
    {"id": "certificado_inase", "nombre": "Certificado de exportación de semillas",
     "organismo": "INASE", "emite": "organismo",
     "norma": "Res. SAGYP 715/94",
     "requiere": ["variedad", "categoria", "kilos", "inscripcion_rncfs",
                  "catalogo_nacional", "packing_list"]},
    {"id": "certificado_fitosanitario", "nombre": "Certificado Fitosanitario de Exportación",
     "organismo": "SENASA", "emite": "organismo",
     "requiere": ["certificado_inase", "analisis_sanitario", "pais_destino",
                  "requisitos_onpf", "permiso_embarque"]},
    {"id": "permiso_embarque", "nombre": "Permiso de embarque",
     "organismo": "Aduana (DGA)", "emite": "despachante",
     "requiere": ["factura", "posicion_arancelaria", "puerto", "contenedor"]},
    {"id": "certificado_origen", "nombre": "Certificado de origen",
     "organismo": "Cámara de Comercio", "emite": "organismo",
     "requiere": ["factura", "pais_destino", "posicion_arancelaria"]},
]

# Posición arancelaria de la papa para siembra (NCM/HS).
POSICION_ARANCELARIA = "0701.10.00"

# --- Lo que el semillero está obligado a tener -----------------------------
# La comercialización de papa semilla es obligatoriamente de clase FISCALIZADA
# (Res. SAGyP 146/89). El semillero lleva Registro de Cultivos, obtiene el
# Documento de Autorización de Venta (DAV) o de Multiplicación (DAM), y tiene
# un Director Técnico registrado que responde por la fiscalización.
CLASE_COMERCIAL = "Fiscalizada"
DOCUMENTOS_HABILITANTES = ["DAV", "DAM"]

# Identidad registral de la empresa en el dataset (sintética, con el formato
# real: es lo que va impreso en cada rótulo y en cada documento de exportación).
INSCRIPCION_RNCFS = "RNCyFS N° 14.328"
CUIT = "30-54187629-3"
