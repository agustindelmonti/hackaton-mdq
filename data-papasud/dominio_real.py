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

CHARLA DEL 22/08 (primera mano): la planta NO es un depósito más. Es el hub
de la mercadería. El lote sale del campo, entra a recepción/báscula, se
reclasifica y de ahí va a cliente, a frigorífico, o a frío y VUELVE a planta
para salir. El frío es almacenamiento subcontratado, no el mostrador de venta.

Todos los datos de catálogo (variedades, campos, lotes, frigoríficos, clientes,
transportistas, categorías, calibres, rango de kg por bolsa) son REALES,
provistos por Papasud. Nada inventado. Ver PLAN_TRACKS_PAPASUD.md para la
fuente de cada uno. Los kilos y fechas de movimiento son sintéticos.
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
# Laboratorio in vitro — arranque de la escalera. Lo nombraron en la charla
# ("inclusive laboratorios in vitro"). Un solo nodo: no inventamos sucursales.
# ---------------------------------------------------------------------------
LABORATORIO = {
    "id": "lab_invitro",
    "nombre": "Laboratorio in vitro",
    "tipo": "laboratorio",
    "detalle": "Cultivo de meristemas. De acá salen las categorías más altas, no mercadería a granel.",
}

# ---------------------------------------------------------------------------
# Campos — de donde nace todo. Cada campo tiene pivotes (A, B) y cada pivote
# cuadrantes (1 a 8), según los planos que nos pasó Papasud.
#
# San Cayetano / Cayetano Chávez lo nombraron textual: "Del Campo San Cayetano,
# lote 300". Santa Ana también (solapa "Ingreso Tolva Santa Ana").
# ---------------------------------------------------------------------------
CAMPOS = [
    {
        "id": "santa_ana",
        "nombre": "Santa Ana",
        "partido": "San Cayetano",
        "provincia": "Buenos Aires",
        "tipo": "campo",
    },
    {
        "id": "marisol",
        "nombre": "Marisol",
        "partido": "Tres Arroyos",
        "provincia": "Buenos Aires",
        "tipo": "campo",
    },
    {
        "id": "trevelin",
        "nombre": "Trevelin",
        "partido": "Futaleufú",
        "provincia": "Chubut",
        "tipo": "campo",
    },
    {
        "id": "oriente",
        "nombre": "Oriente",
        "partido": "Coronel Dorrego",
        "provincia": "Buenos Aires",
        "tipo": "campo",
    },
    {
        "id": "san_cayetano",
        "nombre": "Cayetano Chávez",
        "partido": "San Cayetano",
        "provincia": "Buenos Aires",
        "tipo": "campo",
        "alias": ["San Cayetano", "Campo San Cayetano"],
    },
]
CAMPO_POR_ID = {c["id"]: c for c in CAMPOS}

PIVOTES = ["A", "B"]
CUADRANTES = list(range(1, 9))  # 1 a 8

# Lote que Papasud citó junto al campo: "Del Campo San Cayetano, lote 300".
LOTE_CAMPO_FORZADO = {"300": "san_cayetano"}

# ---------------------------------------------------------------------------
# Lotes — los códigos REALES que nos dieron. Nunca inventar un número de lote.
# Los L30..L79 salen literal de los planos (estructura pivote/cuadrante); el
# resto son los códigos sueltos que mencionaron en la charla.
# ---------------------------------------------------------------------------
LOTES_PLANO = [f"L{n}" for n in range(30, 80)]          # L30 .. L79  (50 lotes)
LOTES_SUELTOS = [14, 18, 222, 223, 224, 241, 300, 810, 811, 910]  # 10 lotes

# ---------------------------------------------------------------------------
# La planta — UNA, en Mar del Plata, con báscula. Es el centro del flujo real.
# No es un layout de fábrica: las mercaderías se hacen en los campos, vienen
# a la planta, y de ahí tienen distintos orígenes de almacenamiento o venta.
#
# Zonas internas (estaciones de proceso, NO depósitos de inventario):
#   recepción     — el camión entra, se pesa, nace la planilla de recepción
#   reclasificacion — de granel con tierra a bolsas calibradas
#   playa         — sale a cliente, a frigorífico o a exportación
# ---------------------------------------------------------------------------
ZONAS_PLANTA = [
    {
        "id": "recepcion",
        "nombre": "Recepción / báscula",
        "rol": "primer_ingreso",
        "detalle": "El camión (tolva) entra, se pesa, se anota chofer, producto y lote. Nace la planilla de recepción.",
    },
    {
        "id": "reclasificacion",
        "nombre": "Reclasificación y empaque",
        "rol": "calibre_empaque",
        "detalle": "La papa llegó a granel, con tierra. Acá se prolija, se calibra y se embalsa.",
    },
    {
        "id": "playa",
        "nombre": "Playa de carga",
        "rol": "despacho",
        "detalle": "De acá sale a cliente, a frigorífico, o se recibe el retiro de frío para despachar.",
    },
]
ZONA_POR_ID = {z["id"]: z for z in ZONAS_PLANTA}

PLANTA = {
    "id": "planta_mdp",
    "nombre": "Planta Mar del Plata",
    "tipo": "planta",
    "localidad": "Mar del Plata",
    "provincia": "Buenos Aires",
    "tiene_bascula": True,
    "zonas": ZONAS_PLANTA,
}

# ---------------------------------------------------------------------------
# Frigoríficos — subcontratados. Papasud paga por sus servicios, no son de
# ellos: por eso el track de liquidación importa tanto como el de stock.
# El frío NO es el mostrador: la venta sale de la planta. El circuito más
# común es planta → frío → vuelve a planta → cliente.
# ---------------------------------------------------------------------------
FRIGORIFICOS = [
    {"id": "dospanca", "nombre": "Dospanca", "tipo": "frigorifico", "subcontratado": True},
    {"id": "galpon_mdp", "nombre": "Galpón Mar del Plata", "tipo": "frigorifico", "subcontratado": True},
    {"id": "pancani", "nombre": "Pancani", "tipo": "frigorifico", "subcontratado": True},
    {"id": "sasula", "nombre": "Sasula", "tipo": "frigorifico", "subcontratado": True},
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
# Tipos de camión — la tolva es el dato que delata que entendimos la operación.
# "Tolva se llama el camión que trae la papa a granel."
# ---------------------------------------------------------------------------
TIPOS_VEHICULO = [
    {
        "id": "tolva",
        "nombre": "Tolva",
        "carga": "granel",
        "detalle": "Camión que trae la papa suelta, con tierra, desde el campo a la planta.",
    },
    {
        "id": "camion_bolsas",
        "nombre": "Camión de bolsas",
        "carga": "bolsas",
        "detalle": "Mercadería ya embolsada: envío a frío, retiro de frío, o entrega a cliente.",
    },
]
VEHICULO_POR_ID = {v["id"]: v for v in TIPOS_VEHICULO}

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
# La planta está SIEMPRE en el medio salvo los dos atajos (campo→frío y
# campo→cliente) que ellos mismos marcaron como menos comunes.
# ---------------------------------------------------------------------------
TIPOS_MOVIMIENTO = [
    "ingreso_tolva",     # campo -> planta, a granel, con tierra (báscula pesa)
    "campo_a_frio",      # campo -> frigorífico, directo (menos común)
    "envio_frio",        # planta -> frigorífico (la más usada)
    "retiro_frio",       # frigorífico -> planta (vuelve para salir a cliente)
    "entrega_cliente",   # planta (lo normal) o campo/frigorífico -> cliente
]

# Qué tipo de vehículo usa cada movimiento. Determinista, no lo decide el LLM.
VEHICULO_POR_TIPO = {
    "ingreso_tolva": "tolva",
    "campo_a_frio": "camion_bolsas",
    "envio_frio": "camion_bolsas",
    "retiro_frio": "camion_bolsas",
    "entrega_cliente": "camion_bolsas",
}

# Zona de planta que toca cada movimiento (None = no pasa por la planta).
ZONA_PLANTA_POR_TIPO = {
    "ingreso_tolva": "recepcion",
    "campo_a_frio": None,
    "envio_frio": "playa",
    "retiro_frio": "playa",
    "entrega_cliente": "playa",
}

# ---------------------------------------------------------------------------
# Roles de la operación — cada uno ve recortes distintos del mismo libro.
# Textual: "cada empleado, dependiendo de si es frigorífico o planta, necesita
# ver diferentes cosas". Los depósitos son subcontratados.
# ---------------------------------------------------------------------------
ROLES_OPERACION = [
    {
        "id": "campo",
        "nombre": "Operario de campo",
        "ve": ["orden_carga", "lote", "mapa_campo"],
        "carga": "orden de carga en papel (a veces no hay señal)",
    },
    {
        "id": "planta",
        "nombre": "Operario de planta",
        "ve": ["recepcion", "stock_planta", "reclasificacion", "playa"],
        "carga": "planilla de recepción + báscula",
    },
    {
        "id": "frigorifico",
        "nombre": "Depósito subcontratado",
        "ve": ["stock_frio", "retiro_frio", "envio_frio"],
        "carga": "conteo al guardar / al retirar",
    },
    {
        "id": "administracion",
        "nombre": "Administración",
        "ve": ["fletes", "liquidacion", "remitos", "mano_de_obra"],
        "carga": "paga camiones y servicios con el mismo libro",
    },
    {
        "id": "comercial",
        "nombre": "Comercial / gerencia",
        "ve": ["disponibilidad", "clientes", "mapa"],
        "carga": "consulta: ¿tengo 1.200 bolsas de Spunta?",
    },
]

# Albor Agro: el sistema contable que YA usan. No se reemplaza; se integra.
# Textual: "Albor agro se llama. Es un sistema de gestión contable que solo
# usamos el paquete contable."
SISTEMA_CONTABLE = {
    "id": "albor_agro",
    "nombre": "Albor Agro",
    "uso": "paquete_contable",
    "rol": "no_reemplazar",
    "detalle": "Papasud usa sólo el módulo contable. Esta plataforma no lo pisa: el movimiento confirmado es lo que después se liquida allá.",
}

CAMPANIA_ACTUAL = "2025/26"
