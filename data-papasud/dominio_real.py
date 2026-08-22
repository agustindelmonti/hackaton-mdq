"""
dominio_real.py · El modelo real de Papasud, tal como lo describieron los dueños
(Leandro y Sergio Pérsico) en la charla del 22/08/2026 y en PLAN_TRACKS_PAPASUD.md.

Reemplaza la fantasía de "4 depósitos de semilla fiscalizada categoría INASE"
del dataset viejo (dominio.py). Ese dataset asumía un modelo de INVENTARIO
(el lote es una partida de stock). El modelo real es de LINAJE DE CAMPO:
un lote es una superficie de campo inscripta en INASE, y la mercadería fluye
desde ahí hacia la planta, los frigoríficos (subcontratados) y los clientes.

REGLA DURA (textual de ellos): "el lote 300 son peras, el 101 son manzanas,
son totalmente diferentes" — cada lote tiene UNA sola variedad. Nunca dos
variedades en el mismo lote.

Todos los datos de acá (variedades, campos, lotes, frigoríficos, clientes,
transportistas, categorías, calibres, rango de kg por bolsa) son REALES,
provistos por Papasud. Nada inventado. Ver PLAN_TRACKS_PAPASUD.md para la
fuente de cada uno.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Variedades — reales, cuatro nada más. Sin inventar Innovator/Atlantic/etc.
# ---------------------------------------------------------------------------
VARIEDADES = [
    {"id": "agata", "nombre": "Agata"},
    {"id": "spunta", "nombre": "Spunta"},
    {"id": "asterix", "nombre": "Asterix"},
    {"id": "king_russet", "nombre": "King Russet"},
]
VAR_POR_ID = {v["id"]: v for v in VARIEDADES}

# ---------------------------------------------------------------------------
# Campos — de donde nace todo. Cada campo tiene pivotes (A, B) y cada pivote
# cuadrantes (1 a 8), según los planos que nos pasó Papasud.
# ---------------------------------------------------------------------------
CAMPOS = [
    {"id": "santa_ana", "nombre": "Santa Ana"},
    {"id": "marisol", "nombre": "Marisol"},
    {"id": "trevelin", "nombre": "Trevelin"},
    {"id": "oriente", "nombre": "Oriente"},
]
CAMPO_POR_ID = {c["id"]: c for c in CAMPOS}

PIVOTES = ["A", "B"]
CUADRANTES = list(range(1, 9))  # 1 a 8

# ---------------------------------------------------------------------------
# Lotes — los códigos REALES que nos dieron. Nunca inventar un número de lote.
# Los L30..L79 salen literal de los planos (estructura pivote/cuadrante); el
# resto son los códigos sueltos que mencionaron en la charla.
# ---------------------------------------------------------------------------
LOTES_PLANO = [f"L{n}" for n in range(30, 80)]          # L30 .. L79  (50 lotes)
LOTES_SUELTOS = [14, 18, 222, 223, 224, 241, 300, 810, 811, 910]  # 10 lotes

# ---------------------------------------------------------------------------
# La planta — una sola, con báscula. Es el centro del flujo real.
# ---------------------------------------------------------------------------
PLANTA = {"id": "planta_mdp", "nombre": "Planta Mar del Plata", "tiene_bascula": True}

# ---------------------------------------------------------------------------
# Frigoríficos — subcontratados. Papasud paga por sus servicios, no son de
# ellos: por eso el track de liquidación importa tanto como el de stock.
# ---------------------------------------------------------------------------
FRIGORIFICOS = [
    {"id": "dospanca", "nombre": "Dospanca"},
    {"id": "galpon_mdp", "nombre": "Galpón Mar del Plata"},
    {"id": "pancani", "nombre": "Pancani"},
    {"id": "sasula", "nombre": "Sasula"},
]
FRIGO_POR_ID = {f["id"]: f for f in FRIGORIFICOS}

# ---------------------------------------------------------------------------
# Clientes — los que nos dieron. No inventar más.
# ---------------------------------------------------------------------------
CLIENTES = [
    {"id": "wemar_mc_cain", "nombre": "Wemar-McCain"},
    {"id": "parmentier", "nombre": "Parmentier"},
]
CLI_POR_ID = {c["id"]: c for c in CLIENTES}

# ---------------------------------------------------------------------------
# Transportistas — reales, con sus choferes tal como los nombraron.
# ---------------------------------------------------------------------------
TRANSPORTISTAS = [
    {"id": "serantes_vera", "nombre": "Serantes-Vera", "choferes": []},
    {"id": "camillo", "nombre": "Camillo", "choferes": ["Gastón", "Mario"]},
    {"id": "arenas", "nombre": "Arenas", "choferes": ["Jaimez", "De Grandis"]},
    {"id": "cerone", "nombre": "Cerone", "choferes": ["Raphael", "Sotelo"]},
    {"id": "fran_cambronera", "nombre": "Fran Cambronera", "choferes": []},
    {"id": "s_garcia", "nombre": "S. García", "choferes": ["Verdicchio", "Scho", "Stadler"]},
    {"id": "jose_hernandez", "nombre": "José Hernández", "choferes": []},
    {"id": "alvaro_arenas", "nombre": "Álvaro Arenas", "choferes": []},
]
TRANSP_POR_ID = {t["id"]: t for t in TRANSPORTISTAS}

# ---------------------------------------------------------------------------
# Categorías y calibres — los que Papasud usa hoy, no la escalera INASE
# completa del dataset viejo (que no pudimos confirmar con ellos).
# ---------------------------------------------------------------------------
CATEGORIAS = [
    {"id": "inicial_2", "nombre": "Inicial 2"},
    {"id": "inicial_3", "nombre": "Inicial 3"},
]
CAT_POR_ID = {c["id"]: c for c in CATEGORIAS}

CALIBRES = [
    {"id": "exportacion", "nombre": "Exportación"},
    {"id": "granel", "nombre": "Granel"},
    {"id": "sin_chicas", "nombre": "Sin chicas"},
]
CALIBRE_POR_ID = {c["id"]: c for c in CALIBRES}

# Calibre incompatible con exportación: granel es papa suelta sin calibrar,
# no sirve para un pedido de exportación (regla de compatibilidad del
# bloqueo-con-alternativa: Track A no debe sugerir un lote de calibre granel
# para un pedido de exportación).
CALIBRES_APTOS_EXPORTACION = {"exportacion", "sin_chicas"}

# ---------------------------------------------------------------------------
# Kg por bolsa — entre 47 y 54, según el lote (nunca 700, nunca 1.000).
# ---------------------------------------------------------------------------
KG_POR_BOLSA_MIN = 47.0
KG_POR_BOLSA_MAX = 54.0

# ---------------------------------------------------------------------------
# Colores de identificación física (tarjeta + color de bolsa + color de hilo).
# Es lo que usa la gente de campo/frigorífico para reconocer un lote a mano,
# y lo que se confunde en la vida real (ver notas de P.Chica).
# ---------------------------------------------------------------------------
COLORES_BOLSA = ["blanca", "roja", "verde"]
COLORES_HILO = ["verde", "blanco", "negro", "amarillo", "rojo"]

# ---------------------------------------------------------------------------
# Tipos de movimiento — el flujo real, no un depósito-a-depósito genérico.
# ---------------------------------------------------------------------------
TIPOS_MOVIMIENTO = [
    "ingreso_tolva",     # campo -> planta, a granel, con tierra (báscula pesa)
    "campo_a_frio",      # campo -> frigorífico, directo (menos común)
    "envio_frio",        # planta -> frigorífico (la más usada)
    "retiro_frio",       # frigorífico -> planta (vuelve para salir a cliente)
    "entrega_cliente",   # planta (lo normal) o campo/frigorífico -> cliente
]

CAMPANIA_ACTUAL = "2025/26"
