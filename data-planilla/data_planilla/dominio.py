"""
Catálogos del libro real — no del seed inventado.

Fuentes: Planilla de movimientos 2026.xls (12 hojas) y la escalera INASE
que Papasud usa en Trevelin (Inicial I / II / III). Nada de Innovator: no
aparece en la planilla de este ciclo.
"""
from __future__ import annotations

# --- Chacras de origen -----------------------------------------------------
# El nro de lote SOLO es único dentro de una chacra. Lote 50 en Santa Ana es
# Spunta papa chica; lote 50 en Trevelin es Beo Inicial I.
CHACRAS = [
    {"id": "santa_ana", "nombre": "Chacra Santa Ana — Marisol",
     "localidad": "General Pueyrredón", "provincia": "Buenos Aires",
     "ha": 111.1, "zona": "Sudeste bonaerense"},
    {"id": "trevelin", "nombre": "Trevelin",
     "localidad": "Trevelin", "provincia": "Chubut",
     "ha": None, "zona": "Patagonia austral"},
]
CHACRA_POR_ID = {c["id"]: c for c in CHACRAS}

# --- Ubicaciones de custodia -----------------------------------------------
# Propias: planta, galpón, campo. El frío que manda en la planilla es de
# terceros (Dospanca/Pancani, Cecive, Sasula, Belmonte, Frigopap, Teramal).
UBICACIONES = [
    {"id": "campo_santa_ana", "nombre": "Campo Santa Ana",
     "tipo": "campo", "propia": True, "chacra_id": "santa_ana",
     "alias": ["santa ana", "sta ana", "marisol"],
     "camaras": [], "capacidad_kg": None},
    {"id": "planta_santa_ana", "nombre": "Planta Santa Ana",
     "tipo": "planta", "propia": True, "chacra_id": "santa_ana",
     "alias": ["planta", "en planta", "tolvas", "papasud"],
     "camaras": [], "capacidad_kg": None},
    {"id": "galpon_mdp", "nombre": "Galpón Mar del Plata",
     "tipo": "galpon", "propia": True,
     "alias": ["galpon", "galpón", "galpon-galpon", "galpon mdp",
               "galpon mar del plata"],
     "camaras": ["Sector Norte", "Sector Sur"], "capacidad_kg": 900_000},
    {"id": "campo_trevelin", "nombre": "Campo Trevelin",
     "tipo": "campo", "propia": False, "chacra_id": "trevelin",
     "alias": ["trevelin"],
     "camaras": [], "capacidad_kg": None},
    {"id": "pancani", "nombre": "Frigorífico Pancani (Dospanca)",
     "tipo": "frio_tercero", "propia": False,
     "alias": ["dospanca", "pancani", "dos panca", "dj panc"],
     "camaras": ["Cámara 1", "Cámara 2", "Cámara 3"], "capacidad_kg": None},
    {"id": "cecive", "nombre": "Cecive",
     "tipo": "frio_tercero", "propia": False,
     "alias": ["cecive"],
     "camaras": ["Cámara 1", "Cámara 2"], "capacidad_kg": None},
    {"id": "sasula", "nombre": "Sasula Balcarce",
     "tipo": "frio_tercero", "propia": False,
     "alias": ["sasula", "sasula balcarce"],
     "camaras": [], "capacidad_kg": None},
    {"id": "belmonte", "nombre": "Belmonte",
     "tipo": "frio_tercero", "propia": False,
     "alias": ["belmonte"],
     "camaras": [], "capacidad_kg": None},
    {"id": "frigopap", "nombre": "Frigopap",
     "tipo": "frio_tercero", "propia": False,
     "alias": ["frigopap"],
     "camaras": [], "capacidad_kg": None},
    {"id": "teramal", "nombre": "Teramal",
     "tipo": "frio_tercero", "propia": False,
     "alias": ["teramal"],
     "camaras": [], "capacidad_kg": None},
]
UBIC_POR_ID = {u["id"]: u for u in UBICACIONES}


def ubicacion_por_alias(texto: str) -> dict | None:
    t = (texto or "").strip().lower()
    if not t:
        return None
    for u in UBICACIONES:
        if u["id"] == t or u["nombre"].lower() == t:
            return u
        if t in [a.lower() for a in u.get("alias") or []]:
            return u
    return None


# --- Variedades (las que la planilla mueve en 2026) ------------------------
VARIEDADES = [
    {"id": "spunta", "nombre": "Spunta"},
    {"id": "agata", "nombre": "Ágata"},
    {"id": "atlantic", "nombre": "Atlantic"},
    {"id": "daifla", "nombre": "Daifla"},
    {"id": "asterix", "nombre": "Asterix"},
    {"id": "sagitta", "nombre": "Sagitta"},
    {"id": "ludmilla", "nombre": "Ludmilla"},
    {"id": "sababa", "nombre": "Sababa"},
    {"id": "seven_four_7", "nombre": "7 Four 7"},
    {"id": "king_russet", "nombre": "King Russet"},
    {"id": "memphis", "nombre": "Memphis"},
    {"id": "sunred", "nombre": "Sunred"},
    {"id": "edison", "nombre": "Edison"},
    {"id": "sinatra", "nombre": "Sinatra"},
    {"id": "tilbury", "nombre": "Tilbury"},
    {"id": "quintera", "nombre": "Quintera"},
    {"id": "red_magic", "nombre": "Red Magic"},
    {"id": "orchestra", "nombre": "Orchestra"},
    {"id": "acoustic", "nombre": "Acoustic"},
    {"id": "rock", "nombre": "Rock"},
    {"id": "sound", "nombre": "Sound"},
    {"id": "yona", "nombre": "Yona"},
    {"id": "lady_anna", "nombre": "Lady Anna"},
    {"id": "lady_jane", "nombre": "Lady Jane"},
    {"id": "alverstone", "nombre": "Alverstone"},
    {"id": "markies", "nombre": "Markies"},
    {"id": "ikarus", "nombre": "Ikarus"},
    {"id": "noha", "nombre": "Noha"},
    {"id": "farida", "nombre": "Farida"},
    {"id": "beo", "nombre": "Beo"},
    {"id": "picus", "nombre": "Picus"},
    {"id": "linus", "nombre": "Linus"},
    {"id": "primus", "nombre": "Primus"},
    {"id": "lady_avlone", "nombre": "Lady Avlone"},
    {"id": "lady_alicia", "nombre": "Lady Alicia"},
    {"id": "lady_ada", "nombre": "Lady Ada"},
    {"id": "rivola", "nombre": "Rivola"},
    {"id": "taurus", "nombre": "Taurus"},
    {"id": "ribola", "nombre": "Ribola"},
    {"id": "kennebec", "nombre": "Kennebec"},
    {"id": "kelly", "nombre": "Kelly"},
    {"id": "pampeana", "nombre": "Pampeana"},
    {"id": "punchy", "nombre": "Punchy"},
]
VAR_POR_ID = {v["id"]: v for v in VARIEDADES}

_VAR_ALIAS = {
    "agatha": "agata", "ágata": "agata",
    "ludmila": "ludmilla",
    "7 f 7": "seven_four_7", "7f7": "seven_four_7", "7 four 7": "seven_four_7",
    "7 four seven": "seven_four_7",
    "king russet": "king_russet",
    "red magic": "red_magic",
    "lady anna": "lady_anna", "lady jane": "lady_jane",
    "lady avlone": "lady_avlone", "lady alicia": "lady_alicia",
    "lady ada": "lady_ada",
    "rivola 75": "rivola",
}


def variedad_id(nombre: str) -> str | None:
    t = (nombre or "").strip().lower()
    if not t:
        return None
    if t in VAR_POR_ID:
        return t
    if t in _VAR_ALIAS:
        return _VAR_ALIAS[t]
    for v in VARIEDADES:
        if v["nombre"].lower() == t:
            return v["id"]
    return None


# --- Categorías INASE (ids cortos: los que usa Trevelin) -------------------
# orden: más chico = más arriba en el pedigrí.
CATEGORIAS = [
    {"id": "preinicial_0", "nombre": "Preinicial 0", "clase": "Básica", "orden": 0},
    {"id": "preinicial_1", "nombre": "Preinicial I", "clase": "Básica", "orden": 1},
    {"id": "preinicial_2", "nombre": "Preinicial II", "clase": "Básica", "orden": 2},
    {"id": "inicial_1", "nombre": "Inicial I", "clase": "Básica", "orden": 3},
    {"id": "inicial_2", "nombre": "Inicial II", "clase": "Básica", "orden": 4},
    {"id": "inicial_3", "nombre": "Inicial III", "clase": "Básica", "orden": 5},
    {"id": "fundacion", "nombre": "Fundación", "clase": "Básica", "orden": 6},
    {"id": "registrada", "nombre": "Registrada", "clase": "Certificada", "orden": 7},
    {"id": "certificada_a", "nombre": "Certificada A", "clase": "Certificada", "orden": 8},
    {"id": "certificada_b", "nombre": "Certificada B", "clase": "Certificada", "orden": 9},
]
CAT_POR_ID = {c["id"]: c for c in CATEGORIAS}
CAT_ORDEN = [c["id"] for c in CATEGORIAS]


def categoria_id(texto: str) -> str | None:
    t = (texto or "").strip().lower().replace("  ", " ")
    t = t.replace("inicial3", "inicial 3")
    aliases = {
        "inicial 1": "inicial_1", "inicial i": "inicial_1", "inicial1": "inicial_1",
        "inicial 2": "inicial_2", "inicial ii": "inicial_2",
        "inicial 3": "inicial_3", "inicial iii": "inicial_3",
    }
    return aliases.get(t) or (t if t in CAT_POR_ID else None)


# --- Calibre COMERCIAL (no es el grado INASE en mm) ------------------------
CALIBRES_COMERCIALES = [
    {"id": "recibo", "nombre": "Recibo"},
    {"id": "exportacion", "nombre": "Exportación"},
    {"id": "expo_buena", "nombre": "Exportación buena"},
    {"id": "desc_expo", "nombre": "Descarte exportación"},
    {"id": "sin_chicas", "nombre": "Sin chicas"},
    {"id": "granel", "nombre": "Granel"},
    {"id": "desc_paraguay", "nombre": "Desc. Paraguay"},
    {"id": "sin_tamanar", "nombre": "Sin tamañar"},
    {"id": "cepillada_25", "nombre": "Bolsa 25 kg cepillada"},
]
CAL_COM_POR_ID = {c["id"]: c for c in CALIBRES_COMERCIALES}

# El grado INASE en mm sigue existiendo como dato de rótulo, aparte.
CALIBRES_INASE = {
    1: {"min_mm": 45.0, "max_mm": 90.0, "label": "Grado 1 (45–90 mm)"},
    2: {"min_mm": 33.0, "max_mm": 45.0, "label": "Grado 2 (33–45 mm)"},
    3: {"min_mm": 20.0, "max_mm": 33.0, "label": "Grado 3 (20–33 mm)"},
    4: {"min_mm": None, "max_mm": None, "label": "Grado 4 (libre)"},
}


# --- Envases ---------------------------------------------------------------
# Env a Frio 2026: kg/bolsa promedio 50,67 (rango 25–53,4). El bolsón de la
# operación es ~700 kg, no 1.000. Granel no tiene peso de envase.
KG_POR_BOLSA = 50
ENVASES = [
    {"id": "bolsa", "nombre": "Bolsa", "kg_nominal": KG_POR_BOLSA},
    {"id": "bolson", "nombre": "Bolsón", "kg_nominal": 700},
    {"id": "granel", "nombre": "Granel", "kg_nominal": None},
    {"id": "chasis", "nombre": "Granel (chasis)", "kg_nominal": None},
    {"id": "acopiador", "nombre": "Granel (acopiador)", "kg_nominal": None},
    {"id": "tarima", "nombre": "Tarima", "kg_nominal": None},
    {"id": "bolsa_25", "nombre": "Bolsa 25 kg", "kg_nominal": 25},
]
ENV_POR_ID = {e["id"]: e for e in ENVASES}


def envase(eid: str) -> dict:
    return ENV_POR_ID[eid]


# --- Transportes (empresa + chofer habitual) -------------------------------
TRANSPORTES = [
    {"id": "camillo_gaston", "empresa": "Camillo", "chofer": "Gastón"},
    {"id": "camillo_mario", "empresa": "Camillo", "chofer": "Mario"},
    {"id": "camillo_jaimez", "empresa": "Camillo", "chofer": "Jaimez"},
    {"id": "cerone_raphael", "empresa": "Cerone", "chofer": "Raphael"},
    {"id": "cerone_sotelo", "empresa": "Cerone", "chofer": "Sotelo"},
    {"id": "arenas", "empresa": "Arenas", "chofer": None},
    {"id": "arenas_jaimez", "empresa": "Arenas", "chofer": "Jaimez"},
    {"id": "arenas_de_grandis", "empresa": "Arenas", "chofer": "De Grandis"},
    {"id": "serantes_vera", "empresa": "Serantes-Vera", "chofer": None},
    {"id": "fran_cambronera", "empresa": "Fran Cambronera", "chofer": None},
    {"id": "el_salvador", "empresa": "El Salvador", "chofer": None},
    {"id": "delcasagro", "empresa": "Delcasagro", "chofer": None},
    {"id": "s_garcia", "empresa": "S. García", "chofer": None},
]
TR_POR_ID = {t["id"]: t for t in TRANSPORTES}


# --- Clientes: broker y productor final son dos entidades ------------------
CLIENTES = [
    {"id": "wemar_mccain", "nombre": "Wemar — McCain", "tipo": "industria",
     "canal": "industria"},
    {"id": "lamb_weston", "nombre": "Lamb Weston", "tipo": "industria",
     "canal": "industria"},
    {"id": "parmentier", "nombre": "Parmentier", "tipo": "industria",
     "canal": "industria"},
    {"id": "hzpc", "nombre": "HZPC", "tipo": "obtentor", "canal": "semillero"},
    {"id": "delcaso", "nombre": "Delcaso", "tipo": "broker",
     "canal": "comisionista"},
    {"id": "papalini", "nombre": "Papalini", "tipo": "broker",
     "canal": "comisionista"},
    {"id": "romero_m", "nombre": "Romero M", "tipo": "interno",
     "canal": "productor", "broker_id": "delcaso"},
    {"id": "agro_selmi", "nombre": "Agro Selmi", "tipo": "interno",
     "canal": "productor"},
    {"id": "mazzeo_cristian", "nombre": "Mazzeo Cristian", "tipo": "interno",
     "canal": "productor"},
    {"id": "francisco_andreu", "nombre": "Francisco Andreu", "tipo": "interno",
     "canal": "productor"},
    {"id": "la_union_del_sur", "nombre": "La Unión del Sur", "tipo": "interno",
     "canal": "productor"},
    {"id": "frigopap_cliente", "nombre": "Frigopap (carga Lamb Weston)",
     "tipo": "industria", "canal": "industria"},
]
CLI_POR_ID = {c["id"]: c for c in CLIENTES}
