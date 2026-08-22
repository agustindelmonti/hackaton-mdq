"""
usuarios_papasud.py · El equipo de Papasud S.A.

La empresa es real; **las personas de este archivo son inventadas**. El
organigrama sí está calcado de cómo se opera una semillera de este tamaño:
dirección, administración y comercio exterior, un encargado que responde por
las cuatro ubicaciones, operarios de frigorífico y de galpón, y una agrónoma
que firma la sanidad de cada lote.

Seis personas, seis PolPilot distintos. El operario que está parado adentro de
una cámara a 4 grados con un celular en la mano no necesita ver el tablero del
dueño: necesita decir en voz alta lo que acaba de mover. Y el dueño no necesita
aprender a usar el sistema del operario.

Los perfiles usan el formato de BLOQUES ("Mi función: … Me encargo de: … Todos
los días miro: … Decido sobre: …"): de ahí sale el sugeridor de módulos, que
lee el texto y propone qué necesita cada persona.

BILINGÜE: cada descripción viaja también en inglés (`descripcion_en`). No es
decorativo — entre el 25% y el 30% del negocio es exportación y la
documentación, los requisitos de la ONPF de destino y la correspondencia con el
cliente viajan en inglés.

El CASTELLANO es la fuente: `perfiles.sugerir_modulos` matchea sobre
`descripcion`, y lo que una persona reescribe de su propio perfil se guarda tal
cual — son SUS palabras.
"""

# Todo lo que el dueño ve. El resto de los roles son un subconjunto.
_TODO = [
    "panel", "mapa", "inventario", "deposito", "movimientos", "conciliacion",
    "logistica", "exportacion", "trazabilidad", "saneamiento", "evolucion",
    "alertas", "oportunidades", "equipo", "gestion_equipo", "cargar",
    "documentos", "auditoria", "perfil", "angela",
]

USUARIOS = {
    "ernesto": {
        "username": "ernesto", "nombre": "Ernesto", "apellido": "Sagardía",
        "rol": "Dueño", "es_admin": True,
        "telefono": "+5492230000001", "color": "#1e2f6f",
        "superficies": ["desktop", "mobile"],
        "descripcion": (
            "Mi función: soy la cuarta generación de la familia en la empresa. Dirijo "
            "Papasud: la producción, las cuatro ubicaciones y la exportación. "
            "Me encargo de: la relación con los clientes grandes, los precios de la "
            "semilla, las decisiones de campaña y todo lo que sea plata — firmo yo. "
            "Todos los días miro: cuánto stock hay y dónde está de verdad, qué se está "
            "por brotar, qué embarque tengo comprometido y si llegamos con la "
            "documentación. "
            "Decido sobre: precios, campañas, inversiones en frío y la gente."
        ),
        "descripcion_en": (
            "My role: I'm the fourth generation of the family in the company. I run "
            "Papasud: production, the four locations and exports. "
            "I take care of: the relationship with our large customers, seed pricing, "
            "campaign decisions and anything involving money — I sign that myself. "
            "Every day I look at: how much stock there actually is and where, what's "
            "about to sprout, which shipment I've committed to and whether the paperwork "
            "will make it in time. "
            "I decide on: prices, campaigns, cold-storage investments and the people."
        ),
        "features": _TODO,
    },
    "cecilia": {
        "username": "cecilia", "nombre": "Cecilia", "apellido": "Bruzzone",
        "rol": "Administración y Comercio Exterior", "es_admin": False,
        "telefono": "+5492230000002", "color": "#b8860b",
        "superficies": ["desktop", "mobile"],
        "descripcion": (
            "Mi función: administración y comercio exterior. Hace once años que armo la "
            "carpeta de cada embarque. "
            "Me encargo de: las facturas proforma, el packing list, el certificado del "
            "INASE y el fitosanitario del SENASA, y de pelearme con los tiempos del "
            "despachante. "
            "Todos los días miro: qué embarque tengo abierto, qué documento falta para "
            "cerrarlo y qué lote quedó comprometido con qué cliente. "
            "Decido sobre: en qué orden se tramita cada certificado; los montos grandes "
            "los consulto con Ernesto."
        ),
        "descripcion_en": (
            "My role: admin and foreign trade. For eleven years I've been the one putting "
            "together the file for every shipment. "
            "I take care of: proforma invoices, packing lists, the INASE certificate and "
            "the SENASA phytosanitary one, and fighting with the customs broker's timing. "
            "Every day I look at: which shipment is open, which document is missing to "
            "close it, and which lot is committed to which customer. "
            "I decide on: the order in which each certificate gets filed; the large "
            "amounts I check with Ernesto."
        ),
        "features": ["exportacion", "documentos", "trazabilidad", "logistica",
                     "inventario", "alertas", "equipo", "perfil", "angela"],
    },
    "ruben": {
        "username": "ruben", "nombre": "Rubén", "apellido": "Ocampo",
        "rol": "Encargado de depósito", "es_admin": False,
        "telefono": "+5492230000003", "color": "#2f6f4f",
        "superficies": ["desktop", "mobile"],
        "descripcion": (
            "Mi función: encargado de las cuatro ubicaciones. Los tres frigoríficos y el "
            "galpón responden a mí. "
            "Me encargo de: que cada bolsón esté donde dice la planilla, de los traslados "
            "entre cámaras, de los conteos y de que el equipo cargue lo que movió. "
            "Todos los días miro: qué se movió ayer, qué traslado quedó sin confirmar en "
            "destino, qué cámara está fuera de temperatura y qué carga sale hoy. "
            "Decido sobre: dónde se guarda cada lote, cuándo se cuenta una cámara y qué "
            "diferencia hay que investigar."
        ),
        "descripcion_en": (
            "My role: I run the four locations. The three cold stores and the shed report "
            "to me. "
            "I take care of: making sure every big bag is where the spreadsheet says, the "
            "transfers between chambers, the counts, and that the team logs what they moved. "
            "Every day I look at: what moved yesterday, which transfer was never confirmed "
            "at destination, which chamber is off-temperature and what's shipping today. "
            "I decide on: where each lot is stored, when a chamber gets counted and which "
            "discrepancy needs investigating."
        ),
        "features": ["panel", "deposito", "movimientos", "conciliacion", "inventario",
                     "logistica", "trazabilidad", "alertas", "cargar", "equipo",
                     "perfil", "angela"],
    },
    "marcos": {
        "username": "marcos", "nombre": "Marcos", "apellido": "Quiroga",
        "rol": "Operario de frigorífico", "es_admin": False,
        "telefono": "+5492230000004", "color": "#3d7ea6",
        # El celular es su herramienta: está parado adentro de una cámara a 4 °C.
        "superficies": ["mobile", "desktop"],
        "descripcion": (
            "Mi función: operario de frigorífico. Estoy en Ruta 226 y en Sierra. "
            "Me encargo de: mover los bolsones entre cámaras, armar las cargas y contar "
            "cuando me lo piden. "
            "Todos los días miro: qué tengo que mover hoy y qué carga sale. "
            "Decido sobre: nada de plata — yo aviso lo que muevo y lo que veo."
        ),
        "descripcion_en": (
            "My role: cold-store operator. I work at Ruta 226 and at Sierra. "
            "I take care of: moving the big bags between chambers, building the loads and "
            "counting when I'm asked to. "
            "Every day I look at: what I have to move today and what's shipping. "
            "I decide on: nothing involving money — I report what I move and what I see."
        ),
        "features": ["movimientos", "deposito", "cargar", "perfil", "angela"],
    },
    "dalia": {
        "username": "dalia", "nombre": "Dalia", "apellido": "Ferreyra",
        "rol": "Ingeniera agrónoma", "es_admin": False,
        "telefono": "+5492230000005", "color": "#6b4f9e",
        "superficies": ["desktop", "mobile"],
        "descripcion": (
            "Mi función: ingeniera agrónoma. Respondo por la sanidad y la categoría de "
            "cada lote que sale de acá. "
            "Me encargo de: los análisis de virus, la categoría INASE que le corresponde a "
            "cada lote, el calibre declarado y el seguimiento de la brotación. "
            "Todos los días miro: qué lote tiene el análisis por vencer, cuál está "
            "brotando antes de tiempo y cuál quedó fuera de la tolerancia de su categoría. "
            "Decido sobre: si un lote puede salir con la categoría que dice el rótulo."
        ),
        "descripcion_en": (
            "My role: agronomist. I'm accountable for the health status and the grade of "
            "every lot that leaves here. "
            "I take care of: virus testing, the INASE category each lot qualifies for, the "
            "declared size grade and sprouting follow-up. "
            "Every day I look at: which lot has an expiring analysis, which one is "
            "sprouting ahead of schedule and which fell outside its category tolerance. "
            "I decide on: whether a lot can ship under the category printed on its label."
        ),
        "features": ["inventario", "trazabilidad", "deposito", "conciliacion",
                     "alertas", "documentos", "perfil", "angela"],
    },
    "nestor": {
        "username": "nestor", "nombre": "Néstor", "apellido": "Painé",
        "rol": "Operario de galpón", "es_admin": False,
        "telefono": "+5492230000006", "color": "#a65d3d",
        "superficies": ["mobile", "desktop"],
        # Entró hace poco: el sistema lo sabe y lo acompaña (core/onboarding.py).
        "ingreso": "2026-07-27",
        "puesto": {"sector": "Galpón Chapadmalal", "turno": "mañana",
                   "mentor": "ruben", "contrato": "efectivo"},
        "descripcion": (
            "Mi función: operario del galpón de Chapadmalal. Entré hace poco. "
            "Me encargo de: recibir lo que llega de los frigoríficos, acondicionar y "
            "preparar lo que se va a cargar. "
            "Todos los días miro: qué llegó y qué tengo que dejar listo. "
            "Decido sobre: nada todavía — pregunto mucho."
        ),
        "descripcion_en": (
            "My role: operator at the Chapadmalal shed. I started recently. "
            "I take care of: receiving what comes in from the cold stores, conditioning it "
            "and getting the loads ready. "
            "Every day I look at: what arrived and what I need to have ready. "
            "I decide on: nothing yet — I ask a lot of questions."
        ),
        "features": ["movimientos", "deposito", "cargar", "perfil", "angela"],
    },
}
