"""
Generador del dataset de Papasud — DETERMINISTA (seed fija).

La empresa es real y el modelo del negocio está calcado de su operación (cuatro
ubicaciones, ~150 lotes, semilla de papa, exportación). **Los datos son
sintéticos**: los genera este archivo. Las personas del equipo son inventadas.

CÓMO CRUZA TODO (si un número no cruza, el generador aborta con un assert):

  · La campaña manda. 214,3 ha cosechadas con el rinde de cada campo → 7.394,7 t
    de semilla producida en el ciclo 2025/26. De ahí salen los lotes.
  · Cada lote nace en un campo, con una variedad, una categoría INASE y un
    calibre declarado. El costo por kilo lo fija la CATEGORÍA (una Preinicial II
    cuesta seis veces una Certificada); el precio, el destino (exportación paga
    más que el mercado interno).
  · Los movimientos son la historia: ingreso desde el campo → traslados entre
    frigoríficos → egresos por despacho. El stock de HOY es el resultado de
    aplicar todos los movimientos, no un número puesto a mano.
  · Los conteos físicos son la otra fuente: alguien fue, contó bolsones y anotó.
    Donde el conteo no coincide con el saldo de movimientos, hay discrepancia —
    y la causa está PLANTADA en los datos, no inventada por el modelo.
  · Los despachos consumen stock; las órdenes de carga abiertas lo comprometen.
    Una orden pide más de lo que hay verificado: ese es el bloqueo del remito.

LAS TRES INCONSISTENCIAS PLANTADAS (a propósito, son el corazón de N02):

  1. MOV-2026-0912 · 12/08 · 18.000 kg de Spunta salieron de Ruta 226 hacia el
     Galpón Chapadmalal. Confirmado en ORIGEN, nunca confirmado en DESTINO.
     Es el ejemplo textual del brief ("un movimiento del 12/08 posiblemente no
     se registró en destino").
  2. MOV-2026-0873 · 04/08 · un cero de más al tipear: se registraron 42.000 kg
     donde salieron 4.200. La cámara quedó en rojo contra el conteo.
  3. Sierra · Cámara 3 · merma real por brotación nunca descargada del sistema:
     el conteo da menos y el motivo no es un movimiento, es pérdida física.

Correr:  python data-papasud/generar.py
"""
from __future__ import annotations

import datetime
import json
import os
import random

import dominio as D

R = random.Random(20260822)
HERE = os.path.dirname(os.path.abspath(__file__))

# Fecha de referencia CONGELADA: el dataset commiteado se generó con este "hoy"
# y regenerarlo tiene que dar byte-igual. El backend se levanta con la MISMA var
# (POLPILOT_DEMO_TODAY) para que los análisis coincidan con la historia sembrada.
FECHA_REFERENCIA = "2026-08-22"
HOY = datetime.datetime.strptime(
    os.environ.get("POLPILOT_DEMO_TODAY", "").strip() or FECHA_REFERENCIA,
    "%Y-%m-%d").date()

# --- La escala de la operación (brief: ~200 ha, ~7.500 t, 25-30% exportación) -
HECTAREAS = 214.3
CAMPANIA_ACTUAL = "2025/26"
N_LOTES = 147                      # el brief dice "alrededor de 150"
IVA_SEMILLA = 0.105                # semilla: alícuota reducida


def dias(n: int) -> datetime.date:
    """n días ANTES de hoy."""
    return HOY - datetime.timedelta(days=n)


def iso(d: datetime.date) -> str:
    return d.isoformat()


# ---------------------------------------------------------------------------
# Campos de producción — de dónde viene cada lote
# ---------------------------------------------------------------------------
# El grueso se multiplica en el sudeste bonaerense; los materiales de categoría
# alta se producen en la Patagonia austral, donde el aislamiento sanitario y la
# ausencia de áfidos vectores permiten mantener el pedigrí limpio.
CAMPOS = [
    {"id": "calafate", "nombre": "Campo El Calafate — Santa Cruz", "ha": 38.4,
     "rinde": 28.6, "zona": "Patagonia austral", "categorias_altas": True},
    {"id": "sierra_chica", "nombre": "Campo Sierra Chica — Balcarce", "ha": 61.7,
     "rinde": 37.2, "zona": "Sudeste bonaerense", "categorias_altas": False},
    {"id": "la_brava", "nombre": "Campo La Brava — Balcarce", "ha": 48.9,
     "rinde": 36.1, "zona": "Sudeste bonaerense", "categorias_altas": False},
    {"id": "otamendi", "nombre": "Campo Otamendi — Gral. Alvarado", "ha": 39.2,
     "rinde": 34.8, "zona": "Sudeste bonaerense", "categorias_altas": False},
    {"id": "napaleofu", "nombre": "Campo Napaleofú — Balcarce", "ha": 26.1,
     "rinde": 33.4, "zona": "Sudeste bonaerense", "categorias_altas": False},
]

# ---------------------------------------------------------------------------
# Clientes — mercado interno y exportación
# ---------------------------------------------------------------------------
CLIENTES = [
    # Exportación (25-30% del negocio). El canal industrial va vía la filial
    # local del cliente global, que es quien articula con su planta en destino.
    {"id": "vn_ind", "nombre": "Southern Foods Vietnam Co., Ltd.", "tipo": "exportacion",
     "pais": "Vietnam", "puerto": "Puerto de Mar del Plata", "destino_puerto": "Hai Phong",
     "incoterm": "FOB", "moneda": "USD", "canal": "industrial",
     "requisitos_onpf": ["Libre de Ralstonia solanacearum", "Libre de Globodera spp.",
                         "Tratamiento en origen declarado", "Análisis de virus PVY < 0,5%"]},
    {"id": "br_sul", "nombre": "Batata Sul Comércio Ltda.", "tipo": "exportacion",
     "pais": "Brasil", "puerto": "Paso fronterizo Uruguaiana", "destino_puerto": "Curitiba",
     "incoterm": "CIF", "moneda": "USD", "canal": "distribución",
     "requisitos_onpf": ["Certificado fitosanitario MERCOSUR",
                         "Libre de Synchytrium endobioticum", "Declaración de origen varietal"]},
    {"id": "uy_este", "nombre": "Semillas del Este S.R.L.", "tipo": "exportacion",
     "pais": "Uruguay", "puerto": "Paso fronterizo Fray Bentos", "destino_puerto": "Montevideo",
     "incoterm": "CIF", "moneda": "USD", "canal": "distribución",
     "requisitos_onpf": ["Certificado fitosanitario MERCOSUR", "Análisis de virus PVY < 1%"]},
    # Mercado interno: productores y semilleros
    {"id": "int_tandil", "nombre": "Establecimiento Los Cardales — Tandil",
     "tipo": "interno", "pais": "Argentina", "canal": "productor"},
    {"id": "int_balcarce", "nombre": "Agrícola Balcarce S.A.",
     "tipo": "interno", "pais": "Argentina", "canal": "productor"},
    {"id": "int_noa", "nombre": "Semillera del Norte — Tafí del Valle",
     "tipo": "interno", "pais": "Argentina", "canal": "semillero"},
    {"id": "int_cordoba", "nombre": "Papas Villa Dolores S.R.L.",
     "tipo": "interno", "pais": "Argentina", "canal": "productor"},
    {"id": "int_otamendi", "nombre": "Hnos. Etcheverry — Otamendi",
     "tipo": "interno", "pais": "Argentina", "canal": "productor"},
]
CLI_POR_ID = {c["id"]: c for c in CLIENTES}


# ---------------------------------------------------------------------------
# 1 · LOS LOTES
# ---------------------------------------------------------------------------
def _elegir(pesos: list[dict]) -> dict:
    """Elige un elemento según su `peso_relativo`."""
    total = sum(x["peso_relativo"] for x in pesos)
    r = R.random() * total
    acum = 0.0
    for x in pesos:
        acum += x["peso_relativo"]
        if r <= acum:
            return x
    return pesos[-1]


def generar_lotes() -> list[dict]:
    """147 lotes de semilla. El código interno es un entero (lo pide el núcleo de
    verdad); el rótulo `lote` es el que va impreso en el bolsón."""
    lotes = []
    codigo = 24_001
    numero_lote = 0
    # Campañas en cámara: la nueva es el grueso; queda remanente de la anterior
    # y un resto chico de material de conservación de dos campañas atrás.
    campanias = [(CAMPANIA_ACTUAL, 0.88), ("2024/25", 0.10), ("2023/24", 0.02)]

    for _ in range(N_LOTES):
        numero_lote += 1
        var = _elegir(D.VARIEDADES)
        cat = _elegir(D.CATEGORIAS)
        campania = R.choices([c for c, _ in campanias],
                             weights=[w for _, w in campanias])[0]

        # El material de categoría alta sale de la Patagonia (aislamiento sanitario).
        if cat["orden"] <= 2:
            campo = CAMPOS[0]
        else:
            campo = R.choices(CAMPOS[1:], weights=[c["ha"] for c in CAMPOS[1:]])[0]

        # Kilos del lote: las categorías altas son lotes chicos (son caros y
        # escasos); las bajas, lotes grandes de multiplicación.
        base_kg = {1: 4_800, 2: 11_500, 3: 26_000, 4: 38_000,
                   5: 44_000, 6: 47_000, 7: 51_000, 8: 54_000}[cat["orden"]]
        kg = round(base_kg * R.uniform(0.72, 1.28), -2)

        # Calibre declarado. Grado 2 es el calibre de semilla por excelencia.
        grado = R.choices([1, 2, 3, 4], weights=[0.16, 0.52, 0.27, 0.05])[0]
        rango = D.CALIBRES[grado]
        if rango["min_mm"] is not None:
            medido = round(R.uniform(rango["min_mm"] + 1.2, rango["max_mm"] - 1.2), 1)
        else:
            medido = None

        # Sanidad: el análisis de virus. Cuanto más alta la categoría, más exigente.
        virus = round(R.uniform(0.0, max(cat["virus_max_pct"], 0.05)) * 0.72, 2)
        analisis_fecha = dias(R.randint(24, 190))

        # Ingreso a cámara: la cosecha del sudeste es de febrero a abril.
        if campania == CAMPANIA_ACTUAL:
            ingreso = dias(R.randint(138, 196))
        elif campania == "2024/25":
            ingreso = dias(R.randint(486, 552))
        else:
            ingreso = dias(R.randint(852, 918))

        # Dormancia natural de la variedad. La FECHA de brotación se calcula
        # después de saber en qué ubicación quedó el lote: en cámara el frío la
        # estira, en el galpón no (ver `calcular_brotacion`).
        dormancia = var["dormancia_dias"] + R.randint(-9, 11)

        costo_kg = round(cat["costo_kg"] * R.uniform(0.94, 1.07), 2)
        # Exportación paga mejor: es material de categoría alta y sale con
        # certificación completa.
        destino = "exportacion" if (cat["orden"] <= 5 and R.random() < 0.42) else "interno"
        markup = R.uniform(1.72, 1.94) if destino == "exportacion" else R.uniform(1.48, 1.66)
        precio_kg = round(costo_kg * markup, 2)

        rotulo = (f"PS-{campania.replace('/', '')}-{var['id'][:3].upper()}-"
                  f"{numero_lote:03d}")
        desc = (f"{var['nombre'].upper()} · {cat['nombre']} · "
                f"Campaña {campania} · {D.CALIBRES[grado]['label']}")

        lotes.append({
            # --- lo que el núcleo de verdad necesita ---
            "codigo": codigo,
            "descripcion": desc,
            "estado": "activo",
            "tipo": var["nombre"],          # el "grupo" del inventario = la variedad
            "proveedor": campo["nombre"],   # el origen del lote
            "um": "kg",
            "stock": float(kg),
            "costo_neto": round(costo_kg / (1 + IVA_SEMILLA), 2),
            "costo_iva": costo_kg,
            "pvp": precio_kg,
            "antiguedad_costo_dias": round(R.uniform(4.0, 88.0), 2),
            "inmovilizado": round(kg * costo_kg, 2),
            # --- calibre: el rótulo declara un grado y el medido tiene que caer
            #     adentro del rango de ese grado (Res. INASE 171/2000 art. 25) ---
            "calibrado": rango["min_mm"] is not None,
            "calibre_grado": grado,
            "cota_inf": rango["min_mm"],
            "cota_sup": rango["max_mm"],
            "valor_peso": medido,
            # --- dominio de la semilla ---
            "lote": rotulo,
            "variedad": var["nombre"],
            "variedad_id": var["id"],
            "categoria_semilla": cat["nombre"],
            "categoria_id": cat["id"],
            "clase": cat["clase"],
            "campania": campania,
            "campo_origen": campo["nombre"],
            "zona_origen": campo["zona"],
            "fecha_ingreso": iso(ingreso),
            "analisis_estado": "aprobado",
            "analisis_fecha": iso(analisis_fecha),
            "virus_pct": virus,
            "virus_max_pct": cat["virus_max_pct"],
            "dormancia_dias": dormancia,
            "destino": destino,
        })
        codigo += 1
    return lotes


def inyectar_problemas(lotes: list[dict]) -> None:
    """Los "puntitos" de una planilla que editan cuatro personas a la vez. No es
    un desastre: es el 4% sucio que tiene cualquier operación real, y es lo que
    la conciliación tiene que encontrar."""
    # 1) Lotes dados de baja que siguen figurando con kilos (el clásico de la
    #    planilla: alguien marcó "descartado" y nadie puso el stock en cero).
    for i in (11, 63, 118):
        lotes[i]["estado"] = "anulado"

    # 2) Stock negativo: sacaron más de lo que el sistema decía que había.
    lotes[27]["stock"] = -1_400.0
    lotes[27]["inmovilizado"] = round(lotes[27]["stock"] * lotes[27]["costo_iva"], 2)
    lotes[91]["stock"] = -600.0
    lotes[91]["inmovilizado"] = round(lotes[91]["stock"] * lotes[91]["costo_iva"], 2)

    # 3) Lotes activos sin precio cargado — no se pueden cotizar.
    for i in (7, 34, 52, 76, 103, 129):
        lotes[i]["pvp"] = None

    # 4) CALIBRE FUERA DEL GRADO DECLARADO. El rótulo dice grado 2 (33-45 mm) y
    #    el calibre medido da 47,8: el rótulo miente. En exportación eso frena
    #    un embarque, y es exactamente el dato que nadie mira hasta que es tarde.
    #    Se eligen sobre lotes que declaren grado (el grado 4 es "libre": no tiene
    #    rango contra el cual estar afuera).
    calibrados = [i for i, l in enumerate(lotes) if l["calibrado"]]
    for i, delta in zip((calibrados[19], calibrados[58], calibrados[112]),
                        (2.8, -1.6, 1.9)):
        l = lotes[i]
        # el medido se corre apenas por fuera del borde del grado declarado:
        # así de sutil es el error que hoy nadie ve hasta el embarque
        l["valor_peso"] = round((l["cota_sup"] + delta) if delta > 0
                                else (l["cota_inf"] + delta), 1)

    # 5) Costo de producción sin actualizar hace más de un año.
    for i in (23, 88, 141):
        lotes[i]["antiguedad_costo_dias"] = round(R.uniform(398.0, 611.0), 2)

    # 6) Un lote cuyo análisis de virus superó la tolerancia de su categoría:
    #    sanitariamente no puede salir como esa categoría.
    l = lotes[45]
    l["virus_pct"] = round(l["virus_max_pct"] + 0.8, 2)
    l["analisis_estado"] = "observado"


# ---------------------------------------------------------------------------
# 2 · UBICACIÓN DE CADA LOTE + MOVIMIENTOS
# ---------------------------------------------------------------------------
def repartir_en_ubicaciones(lotes: list[dict]) -> None:
    """Cada lote vive en una cámara concreta. El reparto respeta la capacidad de
    cada sitio y manda al galpón (sin frío) lo que está por salir."""
    # Cada frigorífico tiene su vocación y por eso NO se llenan parejo: Sierra es
    # la casa matriz y absorbe el grueso, Ruta 226 la sigue, Batán es el más
    # chico y se usa para lo que rota menos. El galpón es tránsito: sólo entra
    # lo que ya tiene fecha de salida.
    PESO = {"sierra": 0.46, "ruta226": 0.33, "batan": 0.21}
    TOPE = 0.93                        # nadie llena una cámara hasta el borde
    ocupado = {u["id"]: 0.0 for u in D.UBICACIONES}
    orden = sorted(lotes, key=lambda l: -abs(l["stock"]))
    for l in orden:
        kg = abs(l["stock"])
        if l["destino"] == "exportacion" and R.random() < 0.22:
            candidatos = ["chapadmalal"]
        else:
            candidatos = [uid for uid in PESO
                          if ocupado[uid] + kg <= D.UBIC_POR_ID[uid]["capacidad_kg"] * TOPE]
            if not candidatos:
                candidatos = ["chapadmalal"]
        if len(candidatos) > 1:
            elegido = R.choices(candidatos, weights=[PESO[c] for c in candidatos])[0]
        else:
            elegido = candidatos[0]
        ocupado[elegido] += kg
        camaras = D.UBIC_POR_ID[elegido]["camaras"]
        l["ubicacion_id"] = elegido
        l["ubicacion"] = D.UBIC_POR_ID[elegido]["nombre"]
        l["camara"] = R.choice(camaras)


def calcular_brotacion(lotes: list[dict]) -> None:
    """Cuándo brota cada lote — y por lo tanto cuándo deja de ser semilla de su
    categoría. Depende de DÓNDE está guardado: el frío estira la dormancia, el
    galpón no. Es el reloj real del negocio y el que le da urgencia al tablero."""
    for l in lotes:
        u = D.UBIC_POR_ID[l["ubicacion_id"]]
        factor = D.FACTOR_FRIO if u["tipo"] == "frigorifico" else D.FACTOR_SIN_FRIO
        dias_efectivos = int(round(l["dormancia_dias"] * factor))
        ingreso = datetime.date.fromisoformat(l["fecha_ingreso"])
        brot = ingreso + datetime.timedelta(days=dias_efectivos)
        l["dormancia_efectiva_dias"] = dias_efectivos
        l["brotacion_estimada"] = iso(brot)
        l["dias_hasta_brotacion"] = (brot - HOY).days
        l["conservacion"] = "refrigerado" if u["tipo"] == "frigorifico" else "sin frío"


def generar_movimientos(lotes: list[dict]) -> list[dict]:
    """La historia de cada kilo. Un movimiento tiene origen, destino, quién lo
    hizo y cuándo — y en destino alguien tiene que CONFIRMAR que llegó.

    El estado `en_transito` es el que importa: mientras nadie confirme en
    destino, esos kilos no están verificados en ningún lado. Ahí nacen las
    discrepancias que hoy se descubren recién frente al cliente.
    """
    movs = []
    n = 0
    operarios = ["marcos", "nestor", "ruben"]

    def nuevo(fecha, tipo, lote, kg, origen, destino, quien, estado="confirmado",
              nota=None, numero=None):
        nonlocal n
        n += 1
        m = {
            "numero": numero or f"MOV-2026-{n:04d}",
            "fecha": iso(fecha),
            "tipo": tipo,                      # ingreso | traslado | egreso | descarte
            "lote": lote["lote"],
            "codigo": lote["codigo"],
            "variedad": lote["variedad"],
            "kg": round(kg, 1),
            "bolsones": round(kg / D.KG_POR_BOLSON, 2),
            "origen": origen,
            "destino": destino,
            "registrado_por": quien,
            "estado": estado,                  # confirmado | en_transito | anulado
            "confirmado_en_destino": estado == "confirmado",
            "canal": R.choice(["voz", "texto", "planilla"]),
        }
        if nota:
            m["nota"] = nota
        movs.append(m)
        return m

    # (a) INGRESOS desde los campos: cada lote entró a cámara al cosecharse.
    for l in sorted(lotes, key=lambda x: x["fecha_ingreso"]):
        f = datetime.date.fromisoformat(l["fecha_ingreso"])
        nuevo(f, "ingreso", l, abs(l["stock"]), l["campo_origen"], l["ubicacion"],
              "ruben", nota="Ingreso de cosecha")

    # (b) TRASLADOS entre ubicaciones a lo largo del año: reordenar cámaras,
    #     juntar lo que sale junto, liberar espacio para la cosecha nueva.
    for _ in range(96):
        l = R.choice([x for x in lotes if x["stock"] > 5_000])
        f = dias(R.randint(3, 168))
        origen = l["ubicacion"]
        destino = D.ubicacion_nombre(
            R.choice([u["id"] for u in D.UBICACIONES if u["nombre"] != origen]))
        kg = round(R.randint(2, 9) * D.KG_POR_BOLSON)
        nuevo(f, "traslado", l, kg, origen, destino, R.choice(operarios))

    # (c) EGRESOS por despacho a clientes.
    for _ in range(74):
        l = R.choice([x for x in lotes if x["stock"] > 8_000])
        f = dias(R.randint(2, 152))
        cli = R.choice(CLIENTES)
        kg = round(R.randint(4, 22) * D.KG_POR_BOLSON)
        nuevo(f, "egreso", l, kg, l["ubicacion"], cli["nombre"], R.choice(operarios),
              nota=f"Despacho a {cli['nombre']}")

    # (d) DESCARTES por sanidad o brotación.
    for _ in range(11):
        l = R.choice(lotes)
        f = dias(R.randint(5, 140))
        kg = round(R.randint(1, 3) * D.KG_POR_BOLSON)
        nuevo(f, "descarte", l, kg, l["ubicacion"], "Descarte",
              "dalia", nota=R.choice(["Brotación avanzada", "Pudrición húmeda",
                                      "Fuera de tolerancia sanitaria"]))

    movs.sort(key=lambda m: (m["fecha"], m["numero"]))
    # renumerar en orden cronológico: así el número dice algo
    for i, m in enumerate(movs, start=1):
        if not m["numero"].startswith("MOV-2026-09"):   # los plantados conservan su número
            m["numero"] = f"MOV-2026-{i:04d}"
    return movs


def plantar_inconsistencias(lotes: list[dict], movs: list[dict]) -> dict:
    """Las tres diferencias que el sistema tiene que encontrar y EXPLICAR.

    Están plantadas en los datos con su causa real adentro. La hipótesis que
    Ángela cuenta después no es una especulación del modelo: es este movimiento,
    con este número y esta fecha, encontrado por código."""
    plantadas = {}

    # (1) EL CASO DEL BRIEF — 12/08, movimiento sin confirmar en destino.
    #     Se eligió un lote de Spunta que esté en Ruta 226 y tenga kilos de sobra.
    candidatos = [l for l in lotes
                  if l["variedad"] == "Spunta" and l["ubicacion_id"] == "ruta226"
                  and l["stock"] > 20_000]
    lote1 = candidatos[0] if candidatos else [
        l for l in lotes if l["variedad"] == "Spunta" and l["stock"] > 20_000][0]
    f1 = datetime.date(2026, 8, 12)
    mov1 = {
        "numero": "MOV-2026-0912",
        "fecha": iso(f1),
        "tipo": "traslado",
        "lote": lote1["lote"],
        "codigo": lote1["codigo"],
        "variedad": lote1["variedad"],
        "kg": 18_000.0,
        "bolsones": 18.0,
        "origen": lote1["ubicacion"],
        "destino": D.ubicacion_nombre("chapadmalal"),
        "registrado_por": "marcos",
        "estado": "en_transito",
        "confirmado_en_destino": False,
        "canal": "voz",
        "nota": "Preparación de carga para exportación",
    }
    movs.append(mov1)
    plantadas["movimiento_sin_confirmar"] = mov1

    # (2) EL CERO DE MÁS — 04/08. Salieron 4.200 kg y se tipearon 42.000.
    lote2 = [l for l in lotes
             if l["ubicacion_id"] == "sierra" and l["stock"] > 30_000
             and l["codigo"] != lote1["codigo"]][0]
    mov2 = {
        "numero": "MOV-2026-0873",
        "fecha": iso(datetime.date(2026, 8, 4)),
        "tipo": "egreso",
        "lote": lote2["lote"],
        "codigo": lote2["codigo"],
        "variedad": lote2["variedad"],
        "kg": 42_000.0,
        "bolsones": 42.0,
        "origen": lote2["ubicacion"],
        "destino": CLI_POR_ID["int_balcarce"]["nombre"],
        "registrado_por": "nestor",
        "estado": "confirmado",
        "confirmado_en_destino": True,
        "canal": "planilla",
        "nota": "Despacho a Agrícola Balcarce",
        "kg_reales": 4_200.0,   # lo que realmente salió (no lo ve el sistema)
    }
    movs.append(mov2)
    plantadas["cantidad_mal_tipeada"] = mov2

    # (3) MERMA FÍSICA NUNCA DESCARGADA — Sierra, Cámara 3. La cámara viene
    #     marcando de más desde hace semanas (está en las notas del equipo) y
    #     un lote brotó. Nadie lo dio de baja: el conteo lo va a encontrar.
    lote3 = [l for l in lotes
             if l["ubicacion_id"] == "sierra" and l["camara"] == "Cámara 3"
             and l["stock"] > 15_000
             and l["codigo"] not in (lote1["codigo"], lote2["codigo"])][0]
    plantadas["merma_no_registrada"] = {"lote": lote3["lote"], "codigo": lote3["codigo"],
                                        "variedad": lote3["variedad"],
                                        "camara": lote3["camara"],
                                        "kg": 3_100.0, "motivo": "brotación"}

    movs.sort(key=lambda m: (m["fecha"], m["numero"]))
    return plantadas


# ---------------------------------------------------------------------------
# 3 · STOCK POR UBICACIÓN (el saldo declarado) Y CONTEOS FÍSICOS
# ---------------------------------------------------------------------------
def generar_filas_deposito(lotes: list[dict]) -> list[dict]:
    """La vista de stock por lote y ubicación: lo que la planilla DICE que hay.
    Es el apartado que consume core/deposito.py."""
    filas = []
    for l in lotes:
        filas.append({
            "codigo": l["codigo"],
            "producto": l["descripcion"],
            "lote": l["lote"],
            "variedad": l["variedad"],
            "categoria_semilla": l["categoria_semilla"],
            "campania": l["campania"],
            "ubicacion": l["ubicacion"],
            "ubicacion_id": l["ubicacion_id"],
            "camara": l["camara"],
            "cantidad": float(l["stock"]),
            "bolsones": round(l["stock"] / D.KG_POR_BOLSON, 2),
            # El "vencimiento" de la semilla es la brotación: pasada esa fecha
            # el lote pierde categoría comercial. Mismo campo, reloj real.
            "vencimiento": l["brotacion_estimada"],
            "destino": l["destino"],
        })
    return filas


def generar_conteos(lotes: list[dict], plantadas: dict) -> list[dict]:
    """Conteos físicos: alguien fue a la cámara, contó bolsones y anotó.

    La mayoría cuadra. Los que no cuadran son los tres casos plantados, más
    unas diferencias chicas de redondeo de bolsón que son normales y que el
    sistema NO tiene que gritar (esa es la regla que el encargado le enseña)."""
    conteos = []
    n = 0
    mov_sin_confirmar = plantadas["movimiento_sin_confirmar"]
    mov_mal_tipeado = plantadas["cantidad_mal_tipeada"]
    merma = plantadas["merma_no_registrada"]

    # Conteo del ciclo de agosto: se contaron las cámaras una por una.
    contados = R.sample([l for l in lotes if l["stock"] > 0], 58)
    # los tres lotes con causa plantada TIENEN que estar contados
    forzados = [mov_sin_confirmar["codigo"], mov_mal_tipeado["codigo"], merma["codigo"]]
    for cod in forzados:
        if not any(l["codigo"] == cod for l in contados):
            contados.append(next(l for l in lotes if l["codigo"] == cod))

    for l in contados:
        n += 1
        declarado = float(l["stock"])
        fisico = declarado
        nota = None
        if l["codigo"] == mov_sin_confirmar["codigo"]:
            # Los kilos salieron del origen pero nadie los confirmó en destino:
            # en origen faltan y en destino no aparecen.
            fisico = declarado - mov_sin_confirmar["kg"]
            nota = "Contado bolsón por bolsón, dos veces"
        elif l["codigo"] == mov_mal_tipeado["codigo"]:
            # Se descargaron 42.000 del sistema pero salieron 4.200: sobran kilos.
            fisico = declarado + (mov_mal_tipeado["kg"] - mov_mal_tipeado["kg_reales"])
        elif l["codigo"] == merma["codigo"]:
            fisico = declarado - merma["kg"]
            nota = "Bolsones del fondo con brotación avanzada"
        elif R.random() < 0.22:
            # Diferencia chica y normal: un bolsón nunca pesa exactamente 1.000 kg.
            fisico = declarado + R.choice([-1, 1]) * R.uniform(18, 74)

        conteos.append({
            "numero": f"CNT-2026-{n:03d}",
            "fecha": iso(dias(R.randint(1, 9))),
            "codigo": l["codigo"],
            "lote": l["lote"],
            "producto": l["descripcion"],
            "ubicacion": l["ubicacion"],
            "ubicacion_id": l["ubicacion_id"],
            "camara": l["camara"],
            "declarado_kg": round(declarado, 1),
            "fisico_kg": round(fisico, 1),
            "diferencia_kg": round(fisico - declarado, 1),
            "contado_por": R.choice(["marcos", "nestor", "ruben"]),
            "metodo": "bolsones",
            **({"nota": nota} if nota else {}),
        })
    conteos.sort(key=lambda c: c["fecha"])
    return conteos


# ---------------------------------------------------------------------------
# 4 · ÓRDENES DE CARGA Y DESPACHOS
# ---------------------------------------------------------------------------
def generar_ordenes_carga(lotes: list[dict], plantadas: dict) -> list[dict]:
    """Las órdenes de carga: qué hay que subir al camión y para quién.

    Una de ellas — la de exportación a Vietnam — pide justo el lote cuyos kilos
    quedaron en el limbo del movimiento del 12/08. Ese es el bloqueo: el sistema
    no la deja emitir hasta que alguien verifique el stock real."""
    ordenes = []
    n = 0

    def nueva(cli_id, items, estado, fecha, nota=None, numero=None):
        nonlocal n
        n += 1
        cli = CLI_POR_ID[cli_id]
        kg = sum(i["kg"] for i in items)
        o = {
            "numero": numero or f"OC-2026-{2400 + n}",
            "fecha": iso(fecha),
            "cliente_id": cli_id,
            "cliente": cli["nombre"],
            "tipo": cli["tipo"],
            "pais": cli["pais"],
            "estado": estado,           # emitida | despachada | pendiente | bloqueada
            "items": items,
            "kg_total": round(kg, 1),
            "bolsones_total": round(kg / D.KG_POR_BOLSON, 2),
            "ubicacion_carga": items[0]["ubicacion"],
        }
        if cli["tipo"] == "exportacion":
            o["incoterm"] = cli["incoterm"]
            o["moneda"] = cli["moneda"]
            o["puerto"] = cli["puerto"]
            o["destino_puerto"] = cli["destino_puerto"]
        if nota:
            o["nota"] = nota
        ordenes.append(o)
        return o

    def item(l, kg):
        return {"codigo": l["codigo"], "lote": l["lote"], "producto": l["descripcion"],
                "variedad": l["variedad"], "categoria_semilla": l["categoria_semilla"],
                "kg": float(kg), "bolsones": round(kg / D.KG_POR_BOLSON, 2),
                "ubicacion": l["ubicacion"], "camara": l["camara"]}

    por_cod = {l["codigo"]: l for l in lotes}

    # Órdenes ya despachadas (historia).
    for _ in range(9):
        cli = R.choice(CLIENTES)
        l = R.choice([x for x in lotes if x["stock"] > 12_000])
        nueva(cli["id"], [item(l, R.randint(6, 18) * D.KG_POR_BOLSON)],
              "despachada", dias(R.randint(12, 140)))

    # Órdenes abiertas del mercado interno.
    for _ in range(3):
        cli = R.choice([c for c in CLIENTES if c["tipo"] == "interno"])
        l = R.choice([x for x in lotes if x["stock"] > 15_000])
        nueva(cli["id"], [item(l, R.randint(5, 12) * D.KG_POR_BOLSON)],
              "emitida", dias(R.randint(1, 6)))

    # LA ORDEN QUE SE BLOQUEA: exportación a Vietnam, sobre el lote del 12/08.
    lote_conflictivo = por_cod[plantadas["movimiento_sin_confirmar"]["codigo"]]
    nueva("vn_ind",
          [item(lote_conflictivo, 24_000)],
          "pendiente", dias(1),
          nota="Embarque programado. Contenedor reservado en el puerto de Mar del Plata.",
          numero="OC-2026-2461")
    return ordenes


# ---------------------------------------------------------------------------
# 5 · EL EQUIPO, SUS NOTAS Y LO QUE LE ENSEÑARON AL SISTEMA
# ---------------------------------------------------------------------------
def generar_notas_equipo(plantadas: dict) -> list[dict]:
    """La capa que no está en ninguna planilla: lo que la gente dice.

    Es la mitad que le falta a cualquier sistema de stock. La cámara que viene
    marcando de más, el bolsón que quedó afuera, el cliente que avisó por
    teléfono. Cuando el conteo no cuadra, la explicación suele estar acá."""
    # La nota de la agrónoma nombra EL lote que efectivamente mermó: la nota es
    # el testigo de un hecho plantado en los datos, no un texto decorativo. Si
    # nombrara otra variedad, la conciliación cruzaría mal y se notaría.
    merma = plantadas["merma_no_registrada"]
    var_merma = merma["variedad"]
    base = [
        ("ruben", "encargado",
         "La Cámara 3 de Sierra viene marcando 1,5 °C por encima del objetivo desde el jueves. "
         "Ya avisé a mantenimiento. Los bolsones del fondo son los que más lo sufren.",
         "The Cámara 3 unit at Sierra has been running 1.5 °C above target since Thursday. "
         "I already told maintenance. The bags at the back are the ones taking the hit.", 6),
        ("marcos", "operario",
         "El martes cargué 18 bolsones de Spunta para el galpón. Salieron de Ruta 226 con el "
         "camión de las 14. No sé si alguien los descargó, yo no estuve.",
         "On Tuesday I loaded 18 bags of Spunta for the shed. They left Ruta 226 on the 2 p.m. "
         "truck. I don't know if anyone unloaded them, I wasn't there.", 10),
        ("dalia", "agrónoma",
         f"El lote de {var_merma} de la Cámara 3 está brotando antes de tiempo. Con la temperatura "
         "que viene marcando esa cámara no me sorprende. Habría que adelantarle la salida.",
         f"The {var_merma} lot in Cámara 3 is sprouting ahead of schedule. With the temperature "
         "that chamber has been running, I'm not surprised. We should move up its dispatch.", 4),
        ("nestor", "operario",
         "Che, ¿los bolsones del Sector Norte del galpón de quién son? No tienen remito arriba y "
         "están hace días. Nadie me supo decir.",
         "Hey — whose are the bags in the shed's North Sector? They have no delivery note on them "
         "and they've been sitting for days. Nobody could tell me.", 7),
        ("cecilia", "administración",
         "Los de Vietnam confirmaron el contenedor para la semana que viene. Necesito el "
         "certificado del INASE antes del jueves o se cae el embarque.",
         "Vietnam confirmed the container for next week. I need the INASE certificate before "
         "Thursday or the shipment falls through.", 2),
        ("ruben", "encargado",
         "Ojo con el conteo de Batán: la Cámara 2 la contamos con dos personas distintas el mismo "
         "día y dio parecido pero no igual. Un bolsón nunca pesa mil justo.",
         "Careful with the Batán count: two different people counted Cámara 2 the same day and it "
         "came out close but not equal. A big bag never weighs exactly a thousand.", 15),
        ("dalia", "agrónoma",
         "El análisis del lote de Asterix vino observado — el PVY dio por encima de la tolerancia "
         "de su categoría. Ese no puede salir como Prefundación.",
         "The Asterix lot's analysis came back flagged — PVY tested above its category tolerance. "
         "That one can't ship as Prefundación.", 9),
        ("cecilia", "administración",
         "Recordá que Brasil pide el certificado fitosanitario del MERCOSUR, no el genérico. La "
         "última vez lo mandamos mal y perdimos cuatro días.",
         "Remember Brazil asks for the MERCOSUR phytosanitary certificate, not the generic one. "
         "Last time we sent the wrong one and lost four days.", 21),
    ]
    out = []
    for i, (autor, rol, texto, texto_en, hace) in enumerate(base, start=1):
        out.append({
            "id": f"NOTA-{i:03d}",
            "fecha": iso(dias(hace)),
            "autor": autor,
            "rol": rol,
            "texto": texto,
            "texto_en": texto_en,
            "canal": R.choice(["voz", "texto"]),
            "tipo": "observacion",
        })
    return out


def generar_conocimiento() -> list[dict]:
    """"Lo que el encargado le enseñó al sistema": reglas del oficio que no están
    en ningún manual y que tienen EFECTO verificable sobre lo que el sistema
    hace. En una empresa de 140 años esto es el activo más grande y el menos
    escrito."""
    piezas = [
        {"id": "K-001", "nodo": "deposito", "efecto": "suprime_alerta",
         "titulo": "Un bolsón nunca pesa mil justo",
         "texto": "Diferencias de menos del 0,5% en un conteo de bolsones son de tara, no de "
                  "faltante. No me alertes por eso.",
         "texto_en": "Differences under 0.5% in a big-bag count are tare, not shrinkage. "
                     "Don't alert me on those.",
         "params": {"umbral_pct": 0.5}, "autor": "ruben"},
        {"id": "K-002", "nodo": "deposito", "efecto": "genera_alerta",
         "titulo": "Cámara por encima de 4 °C, la dormancia se rompe",
         "texto": "Si una cámara pasa de 4 grados más de 48 horas, avisame: los lotes que están "
                  "adentro empiezan a brotar y pierden categoría.",
         "texto_en": "If a chamber goes above 4 °C for more than 48 hours, tell me: the lots "
                     "inside start sprouting and lose their grade.",
         "params": {"temp_max": 4.0, "horas": 48}, "autor": "dalia"},
        {"id": "K-003", "nodo": "despachos", "efecto": "requiere_aprobacion",
         "titulo": "Exportación no sale sin análisis vigente",
         "texto": "Ninguna carga de exportación se emite si el análisis sanitario del lote tiene "
                  "más de 180 días. Eso lo firmo yo.",
         "texto_en": "No export load goes out if the lot's sanitary analysis is older than "
                     "180 days. I sign off on that myself.",
         "params": {"dias_analisis": 180}, "autor": "dalia"},
        {"id": "K-004", "nodo": "movimientos", "efecto": "genera_alerta",
         "titulo": "Un traslado sin confirmar en destino es plata en el aire",
         "texto": "Si un traslado entre ubicaciones no se confirma en destino dentro de las 72 "
                  "horas, quiero saberlo. Esos kilos no están en ningún lado.",
         "texto_en": "If a transfer between locations isn't confirmed at destination within 72 "
                     "hours, I want to know. Those kilos are nowhere.",
         "params": {"horas": 72}, "autor": "ruben"},
        {"id": "K-005", "nodo": "lotes", "efecto": "contexto",
         "titulo": "El galpón es tránsito, no depósito",
         "texto": "Chapadmalal no tiene frío. Lo que entra ahí sale en menos de tres semanas o "
                  "se echa a perder. No es una cámara más.",
         "texto_en": "Chapadmalal has no refrigeration. Whatever goes in there ships within "
                     "three weeks or it spoils. It's not just another chamber.",
         "params": {"dias_max": 21}, "autor": "ruben"},
        {"id": "K-006", "nodo": "lotes", "efecto": "ajusta_umbral",
         "titulo": "La Patagonia da otra sanidad",
         "texto": "El material de El Calafate viene con carga viral mucho más baja que el del "
                  "sudeste. Para esos lotes el umbral de virus puede ser más exigente.",
         "texto_en": "Material from El Calafate comes with a much lower viral load than the "
                     "southeast's. For those lots the virus threshold can be stricter.",
         "params": {"zona": "Patagonia austral", "factor": 0.6}, "autor": "dalia"},
    ]
    for p in piezas:
        p["fecha"] = iso(dias(R.randint(30, 400)))
        p["activa"] = True
    return piezas


# ---------------------------------------------------------------------------
# 6 · ESCRITURA
# ---------------------------------------------------------------------------
def escribir(nombre: str, data) -> None:
    ruta = os.path.join(HERE, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    kb = os.path.getsize(ruta) / 1024
    print(f"  {nombre:<28} {kb:>8.1f} KB")


def main() -> None:
    print(f"Generando el dataset de Papasud (hoy = {HOY})\n")

    lotes = generar_lotes()
    repartir_en_ubicaciones(lotes)
    calcular_brotacion(lotes)
    inyectar_problemas(lotes)
    movs = generar_movimientos(lotes)
    plantadas = plantar_inconsistencias(lotes, movs)
    conteos = generar_conteos(lotes, plantadas)
    ordenes = generar_ordenes_carga(lotes, plantadas)
    filas_dep = generar_filas_deposito(lotes)
    notas = generar_notas_equipo(plantadas)
    conocimiento = generar_conocimiento()

    # ---- asserts de sanidad: si un número no cruza, esto aborta -------------
    kg_total = sum(abs(l["stock"]) for l in lotes)
    prod_ciclo = sum(c["ha"] * c["rinde"] for c in CAMPOS) * 1000
    ha_total = round(sum(c["ha"] for c in CAMPOS), 1)
    assert len(lotes) == N_LOTES, len(lotes)
    assert abs(ha_total - HECTAREAS) < 0.05, ha_total
    assert 7_000_000 <= prod_ciclo <= 8_000_000, prod_ciclo
    for u in D.UBICACIONES:
        ocupado = sum(abs(l["stock"]) for l in lotes if l["ubicacion_id"] == u["id"])
        assert ocupado <= u["capacidad_kg"], (u["nombre"], ocupado, u["capacidad_kg"])
    exp = sum(abs(l["stock"]) for l in lotes if l["destino"] == "exportacion")
    pct_exp = exp / kg_total * 100
    assert 18 <= pct_exp <= 40, f"exportación {pct_exp:.1f}% fuera de rango"
    # las tres inconsistencias tienen que estar y ser encontrables
    assert any(m["numero"] == "MOV-2026-0912" and not m["confirmado_en_destino"]
               for m in movs)
    assert any(c["diferencia_kg"] <= -17_000 for c in conteos), \
        "falta la discrepancia grande del 12/08"
    assert any(o["estado"] == "pendiente" and o["tipo"] == "exportacion" for o in ordenes)
    # ningún lote activo puede tener el calibre medido fuera de su grado sin que
    # el sistema lo vea: verificamos que los tres plantados estén ahí
    # El reloj de la brotación tiene que dar la ventana de plantación de
    # primavera para lo que está en cámara, y ya vencido para lo que quedó en el
    # galpón sin frío. Si eso no pasa, el dataset miente sobre el negocio.
    en_camara = [l for l in lotes if l["conservacion"] == "refrigerado"]
    galpon = [l for l in lotes if l["conservacion"] == "sin frío"]
    vivos = [l for l in en_camara if l["dias_hasta_brotacion"] > 0]
    assert len(vivos) / len(en_camara) > 0.85,         f"sólo {len(vivos)}/{len(en_camara)} lotes en cámara llegan sin brotar"
    assert any(l["dias_hasta_brotacion"] <= 0 for l in galpon),         "el galpón sin frío debería tener lotes pasados de brotación"

    fuera = [l for l in lotes if l["calibrado"] and l["valor_peso"] is not None
             and (l["valor_peso"] < l["cota_inf"] or l["valor_peso"] > l["cota_sup"])]
    assert len(fuera) >= 3, f"calibres fuera de grado: {len(fuera)}"

    print("Archivos:")
    escribir("inventory.json", {"articulos": lotes})
    escribir("apartados.json", {
        "deposito": {"nombre": "Stock por ubicación", "filas": filas_dep},
        "movimientos": {"nombre": "Movimientos de stock", "filas": movs},
        "conteos": {"nombre": "Conteos físicos", "filas": conteos},
        "ordenes_carga": {"nombre": "Órdenes de carga", "filas": ordenes},
    })
    escribir("notas_equipo.json", {"notas": notas})
    escribir("conocimiento_negocio.json", {"piezas": conocimiento})
    escribir("catalogos.json", {
        "ubicaciones": D.UBICACIONES,
        "variedades": D.VARIEDADES,
        "categorias": D.CATEGORIAS,
        "calibres": {str(k): v for k, v in D.CALIBRES.items()},
        "campos": CAMPOS,
        "clientes": CLIENTES,
        "docs_exportacion": D.DOCS_EXPORTACION,
        "meta": {
            "empresa": "Papasud S.A.",
            "hoy": iso(HOY),
            "hectareas": ha_total,
            "produccion_ciclo_kg": round(prod_ciclo, 1),
            "campania": CAMPANIA_ACTUAL,
            "posicion_arancelaria": D.POSICION_ARANCELARIA,
            "sintetico": True,
        },
    })
    escribir("plantadas.json", plantadas)

    # ---- resumen legible ---------------------------------------------------
    valor = sum(abs(l["stock"]) * l["costo_iva"] for l in lotes)
    print(f"""
Resumen del dataset
  Superficie                {ha_total} ha
  Producción del ciclo      {prod_ciclo/1000:,.1f} t   (campaña {CAMPANIA_ACTUAL})
  Lotes en cámara           {len(lotes)}
  Stock total               {kg_total/1000:,.1f} t
  Valor inmovilizado        ${valor:,.0f}
  Exportación               {pct_exp:.1f}% del stock
  Movimientos               {len(movs)}
  Conteos físicos           {len(conteos)}
  Órdenes de carga          {len(ordenes)}  (1 pendiente de verificación)
  Notas del equipo          {len(notas)}
  Piezas de conocimiento    {len(conocimiento)}

Ocupación por ubicación""".replace(",", "."))
    for u in D.UBICACIONES:
        ocup = sum(abs(l["stock"]) for l in lotes if l["ubicacion_id"] == u["id"])
        n = sum(1 for l in lotes if l["ubicacion_id"] == u["id"])
        print(f"  {u['nombre']:<34} {ocup/1000:>7.1f} t / {u['capacidad_kg']/1000:>7.1f} t"
              f"  ({ocup/u['capacidad_kg']*100:>4.1f}%)  {n:>3} lotes")


if __name__ == "__main__":
    main()
