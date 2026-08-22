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
     "costo_kg": 2_140.0, "peso_relativo": 0.03, "virus_max_pct": 0.0},
    {"id": "inicial_1", "nombre": "Inicial I", "clase": "Básica", "orden": 2,
     "costo_kg": 1_186.0, "peso_relativo": 0.08, "virus_max_pct": 0.2},
    {"id": "inicial_2", "nombre": "Inicial II", "clase": "Básica", "orden": 3,
     "costo_kg": 894.0, "peso_relativo": 0.18, "virus_max_pct": 0.5},
    {"id": "inicial_3", "nombre": "Inicial III", "clase": "Básica", "orden": 4,
     "costo_kg": 713.0, "peso_relativo": 0.22, "virus_max_pct": 1.0},
    {"id": "prefundacion", "nombre": "Prefundación", "clase": "Básica", "orden": 5,
     "costo_kg": 608.0, "peso_relativo": 0.17, "virus_max_pct": 2.0},
    {"id": "fundacion", "nombre": "Fundación", "clase": "Básica", "orden": 6,
     "costo_kg": 521.0, "peso_relativo": 0.14, "virus_max_pct": 4.0},
    {"id": "registrada", "nombre": "Registrada", "clase": "Certificada", "orden": 7,
     "costo_kg": 428.0, "peso_relativo": 0.12, "virus_max_pct": 6.0},
    {"id": "certificada", "nombre": "Certificada", "clase": "Certificada", "orden": 8,
     "costo_kg": 356.0, "peso_relativo": 0.06, "virus_max_pct": 10.0},
]
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

# --- Envases y conservación ------------------------------------------------
KG_POR_BOLSON = 1_000          # big bag: la unidad con la que se mueve la cámara
KG_MAX_ENVASE_CAMPO = 50       # Art. 23
KG_MAX_ENVASE_PREINICIAL = 20  # Art. 23

TEMP_MIN_CONSERVACION = 3.0    # °C — bibliografía de poscosecha (>3 meses)
TEMP_MAX_CONSERVACION = 5.0
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

# Posición arancelaria de la papa para siembra en el Mercosur.
POSICION_ARANCELARIA = "0701.10.00"
