"""
generar_real.py · Generador determinista del dataset real de Papasud.

Reemplaza generar.py (el dataset viejo de "4 depósitos de semilla fiscalizada").
Este genera el modelo de LINAJE: Campo -> Pivote -> Cuadrante -> Lote, con el
flujo real de la mercadería:

    LOTE (campo)
       |--> PLANTA (Mar del Plata, con báscula) --> CLIENTE
       |         |--> FRIGORÍFICO --> vuelve a PLANTA --> CLIENTE
       |                          |--> CLIENTE (directo, poco común)
       |--> CLIENTE (directo desde el campo, poco común)

Todo lo que compone el stock es un LIBRO DE MOVIMIENTOS append-only. El stock
de hoy es la SUMA de esos movimientos, nunca un número puesto a mano. Si un
número no cruza, el generador aborta con un assert.

Corre:  python data-papasud/generar_real.py
"""
from __future__ import annotations

import datetime
import json
import os
import random

import dominio_real as D

R = random.Random(20260822)
HERE = os.path.dirname(os.path.abspath(__file__))

FECHA_REFERENCIA = "2026-08-22"
HOY = datetime.datetime.strptime(
    os.environ.get("POLPILOT_DEMO_TODAY", "").strip() or FECHA_REFERENCIA,
    "%Y-%m-%d").date()


def dias(n: int) -> datetime.date:
    return HOY - datetime.timedelta(days=n)


def iso(d: datetime.date) -> str:
    return d.isoformat()


# ---------------------------------------------------------------------------
# 1 · ESTRUCTURA CAMPO -> PIVOTE -> CUADRANTE -> LOTE
# ---------------------------------------------------------------------------
def generar_lotes() -> list[dict]:
    """Cada lote real (código provisto por Papasud) recibe UNA variedad, una
    categoría, un calibre y una ubicación en la estructura física del campo.
    Nunca se inventa un código de lote."""
    lotes = []

    # L30..L79 son los 50 lotes del plano de Santa Ana.
    slots_santa_ana = [(p, c) for p in D.PIVOTES for c in D.CUADRANTES]  # 16 slots
    for i, rotulo in enumerate(D.LOTES_PLANO):
        pivote, cuadrante = slots_santa_ana[i % len(slots_santa_ana)]
        lotes.append(_nuevo_lote(rotulo, "santa_ana", pivote, cuadrante))

    # Los 10 códigos sueltos se reparten entre los otros tres campos.
    otros_campos = ["marisol", "trevelin", "oriente"]
    for i, num in enumerate(D.LOTES_SUELTOS):
        campo_id = otros_campos[i % len(otros_campos)]
        pivote = D.PIVOTES[i % 2]
        cuadrante = D.CUADRANTES[i % len(D.CUADRANTES)]
        lotes.append(_nuevo_lote(str(num), campo_id, pivote, cuadrante))

    return lotes


def _nuevo_lote(rotulo: str, campo_id: str, pivote: str, cuadrante: int) -> dict:
    var = R.choice(D.VARIEDADES)
    cat = R.choice(D.CATEGORIAS)
    calibre = R.choices(D.CALIBRES, weights=[0.38, 0.34, 0.28])[0]
    kg_por_bolsa = round(R.uniform(D.KG_POR_BOLSA_MIN, D.KG_POR_BOLSA_MAX), 1)
    kg_cosechado = round(R.uniform(9_400, 58_000), -1)
    color_bolsa = R.choice(D.COLORES_BOLSA)
    color_hilo = R.choice(D.COLORES_HILO)
    ingreso = dias(R.randint(30, 210))
    return {
        # REGLA DURA: una sola variedad por lote. No hay campo "variedades".
        "id": rotulo,
        "lote": rotulo,
        "campo_id": campo_id,
        "campo": D.CAMPO_POR_ID[campo_id]["nombre"],
        "pivote": pivote,
        "cuadrante": cuadrante,
        "variedad_id": var["id"],
        "variedad": var["nombre"],
        "categoria_id": cat["id"],
        "categoria": cat["nombre"],
        "calibre_id": calibre["id"],
        "calibre": calibre["nombre"],
        "campania": D.CAMPANIA_ACTUAL,
        "kg_cosechado": float(kg_cosechado),
        "kg_por_bolsa": kg_por_bolsa,
        "tarjeta": f"TRJ-{rotulo}",
        "color_bolsa": color_bolsa,
        "color_hilo": color_hilo,
        "fecha_cosecha": iso(ingreso),
    }


# ---------------------------------------------------------------------------
# 2 · EL LIBRO DE MOVIMIENTOS — append-only, es la única fuente de stock
# ---------------------------------------------------------------------------
def _dtv(n: int) -> str:
    base = 13_000_000 + n * 137
    return f"dtv {base}-{n % 10}"


def _camion() -> str:
    letras = "".join(R.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(2))
    numeros = "".join(str(R.randint(0, 9)) for _ in range(3))
    letras2 = "".join(R.choice("ABCDEFGHJKLMNPQRSTUVWXYZ") for _ in range(2))
    return f"{letras}{numeros}{letras2}"


class Ledger:
    """El libro append-only. El stock es SIEMPRE una vista derivada de esto."""

    def __init__(self):
        self.movs: list[dict] = []
        self._n = 0
        self._remito = 4800

    def _numero(self) -> str:
        self._n += 1
        return f"MOV-R-{self._n:04d}"

    def _num_remito(self) -> str:
        self._remito += 1
        return f"R-{self._remito}"

    def agregar(self, **kw) -> dict:
        m = {
            "numero": self._numero(),
            "remito": kw.pop("remito", None) or self._num_remito(),
            "confirmado_en_destino": True,
            "canal": R.choice(["voz", "texto", "foto"]),
            "registrado_por": R.choice(["ruben", "marcos", "nestor", "maxi"]),
        }
        m.update(kw)
        self.movs.append(m)
        return m

    def stock(self) -> dict[tuple[str, str], float]:
        """Vista derivada: kg netos por (lote_id, ubicacion_id), sólo contando
        movimientos confirmados en destino (lo en_transito no está en ningún
        lado todavía, que es justo el punto)."""
        saldo: dict[tuple[str, str], float] = {}
        for m in self.movs:
            if m["tipo"] == "entrega_cliente":
                # sale del sistema: sólo resta en origen
                saldo[(m["lote_id"], m["origen_id"])] = saldo.get(
                    (m["lote_id"], m["origen_id"]), 0.0) - m["kg"]
                continue
            saldo[(m["lote_id"], m["origen_id"])] = saldo.get(
                (m["lote_id"], m["origen_id"]), 0.0) - m["kg"]
            if m["confirmado_en_destino"]:
                saldo[(m["lote_id"], m["destino_id"])] = saldo.get(
                    (m["lote_id"], m["destino_id"]), 0.0) + m["kg"]
        return saldo


def generar_movimientos(lotes: list[dict]) -> Ledger:
    lg = Ledger()
    planta_id = D.PLANTA["id"]

    for lote in lotes:
        campo_ubic = f"campo:{lote['campo_id']}"
        kg_total = lote["kg_cosechado"]
        f0 = datetime.date.fromisoformat(lote["fecha_cosecha"])

        # (a) La cosecha entra a la planta en 1 a 3 camiones (tolva, a granel).
        n_camiones = R.randint(1, 3)
        restos = _repartir(kg_total, n_camiones)
        pesos_netos = []
        for i, kg in enumerate(restos):
            peso_neto = round(kg * R.uniform(0.985, 1.0), 1)  # la báscula pesa un poco menos (tierra/humedad)
            pesos_netos.append(peso_neto)
            transp = R.choice(D.TRANSPORTISTAS)
            lg.agregar(
                tipo="ingreso_tolva",
                dtv=_dtv(lg._n + 1),
                fecha=iso(f0 + datetime.timedelta(days=i)),
                lote_id=lote["id"], variedad_id=lote["variedad_id"],
                kg=peso_neto, bolsas=None,
                origen_id=campo_ubic, origen_nombre=lote["campo"],
                destino_id=planta_id, destino_nombre=D.PLANTA["nombre"],
                transportista_id=transp["id"],
                chofer=R.choice(transp["choferes"]) if transp["choferes"] else None,
                camion=_camion(),
                peso_bascula_kg=peso_neto,
                valor_flete=round(peso_neto / 1000 * R.uniform(3_200, 4_600), -1),
                observaciones="Ingreso Tolva — a granel, con tierra",
            )

        # Lo que queda disponible en planta es lo que la BÁSCULA acreditó, no
        # el reparto teórico del lote (la báscula pesa un poco menos: tierra,
        # humedad). Si esto no cruza, el ledger da stock negativo más adelante.
        kg_en_planta = round(sum(pesos_netos), 1)
        f_actual = f0 + datetime.timedelta(days=n_camiones)

        # (b) De la planta, la mercadería toma distintos caminos.
        camino = R.choices(
            ["directo_planta", "via_frigorifico", "vuelta_planta"],
            weights=[0.30, 0.30, 0.40],
        )[0]

        if camino == "directo_planta":
            _entregar_a_cliente(lg, lote, planta_id, D.PLANTA["nombre"],
                                 kg_en_planta, f_actual + datetime.timedelta(days=R.randint(2, 20)))
            continue

        # envía a frigorífico
        frigo = R.choice(D.FRIGORIFICOS)
        frigo_ubic = f"frigorifico:{frigo['id']}"
        f_envio = f_actual + datetime.timedelta(days=R.randint(1, 10))
        bolsas_envio = round(kg_en_planta / lote["kg_por_bolsa"])
        transp = R.choice(D.TRANSPORTISTAS)
        lg.agregar(
            tipo="envio_frio",
            dtv=_dtv(lg._n + 1),
            fecha=iso(f_envio),
            lote_id=lote["id"], variedad_id=lote["variedad_id"],
            kg=kg_en_planta, bolsas=bolsas_envio,
            origen_id=planta_id, origen_nombre=D.PLANTA["nombre"],
            destino_id=frigo_ubic, destino_nombre=frigo["nombre"],
            transportista_id=transp["id"],
            chofer=R.choice(transp["choferes"]) if transp["choferes"] else None,
            camion=_camion(),
            tarjeta_declarada=lote["tarjeta"], color_bolsa=lote["color_bolsa"],
            color_hilo=lote["color_hilo"],
            valor_flete=round(kg_en_planta / 1000 * R.uniform(2_800, 3_900), -1),
            observaciones=f"Envío a frío — {frigo['nombre']}",
        )

        if camino == "via_frigorifico":
            _entregar_a_cliente(lg, lote, frigo_ubic, frigo["nombre"],
                                 kg_en_planta, f_envio + datetime.timedelta(days=R.randint(5, 60)))
            continue

        # vuelve a planta y de ahí sale al cliente (el circuito más común)
        f_retiro = f_envio + datetime.timedelta(days=R.randint(10, 80))
        bolsas_retiro = round(kg_en_planta / lote["kg_por_bolsa"])
        transp = R.choice(D.TRANSPORTISTAS)
        lg.agregar(
            tipo="retiro_frio",
            dtv=_dtv(lg._n + 1),
            fecha=iso(f_retiro),
            lote_id=lote["id"], variedad_id=lote["variedad_id"],
            kg=kg_en_planta, bolsas=bolsas_retiro,
            origen_id=frigo_ubic, origen_nombre=frigo["nombre"],
            destino_id=planta_id, destino_nombre=D.PLANTA["nombre"],
            transportista_id=transp["id"],
            chofer=R.choice(transp["choferes"]) if transp["choferes"] else None,
            camion=_camion(),
            tarjeta_declarada=lote["tarjeta"], color_bolsa=lote["color_bolsa"],
            color_hilo=lote["color_hilo"],
            valor_flete=round(kg_en_planta / 1000 * R.uniform(2_800, 3_900), -1),
            observaciones="Retiro de frío — vuelve a planta para despacho",
        )
        _entregar_a_cliente(lg, lote, planta_id, D.PLANTA["nombre"],
                             kg_en_planta, f_retiro + datetime.timedelta(days=R.randint(2, 15)))

    return lg


def _repartir(total: float, n: int) -> list[float]:
    if n == 1:
        return [round(total, 1)]
    cortes = sorted(R.uniform(0.15, 0.85) for _ in range(n - 1))
    bordes = [0.0] + cortes + [1.0]
    return [round(total * (bordes[i + 1] - bordes[i]), 1) for i in range(n)]


def _entregar_a_cliente(lg: Ledger, lote: dict, origen_id: str, origen_nombre: str,
                         kg: float, fecha: datetime.date) -> None:
    # No todo lo disponible se vende ya: dejamos un remanente vendible (esto
    # es lo que hace que "disponibilidad" tenga sentido en la demo).
    kg_vender = round(kg * R.uniform(0.35, 0.75), 1)
    if kg_vender < 500:
        return
    cliente = R.choice(D.CLIENTES)
    bolsas = round(kg_vender / lote["kg_por_bolsa"])
    transp = R.choice(D.TRANSPORTISTAS)
    lg.agregar(
        tipo="entrega_cliente",
        dtv=_dtv(lg._n + 1),
        fecha=iso(fecha),
        lote_id=lote["id"], variedad_id=lote["variedad_id"],
        kg=kg_vender, bolsas=bolsas,
        origen_id=origen_id, origen_nombre=origen_nombre,
        destino_id=f"cliente:{cliente['id']}", destino_nombre=cliente["nombre"],
        cliente_id=cliente["id"],
        transportista_id=transp["id"],
        chofer=R.choice(transp["choferes"]) if transp["choferes"] else None,
        camion=_camion(),
        tarjeta_declarada=lote["tarjeta"], color_bolsa=lote["color_bolsa"],
        color_hilo=lote["color_hilo"],
        valor_flete=round(kg_vender / 1000 * R.uniform(3_000, 4_200), -1),
        observaciones=f"Entrega a {cliente['nombre']}",
    )


# ---------------------------------------------------------------------------
# 3 · ESCENARIOS PLANTADOS — el bloqueo-con-alternativa y las inconsistencias
# ---------------------------------------------------------------------------
def plantar_bloqueo_con_alternativa(lg: Ledger, lotes: list[dict]) -> dict:
    """El caso que pidieron textual: 'no hay tanto en este lugar, pero se
    puede vender yendo a este otro lote'. Elegimos una variedad con al menos
    dos lotes en planta con calibre APTO para exportación: uno casi agotado
    (para que el pedido lo exceda) y otro con sobra."""
    stock = lg.stock()
    planta_id = D.PLANTA["id"]
    por_var: dict[str, list[dict]] = {}
    for l in lotes:
        if l["calibre_id"] in D.CALIBRES_APTOS_EXPORTACION:
            kg = stock.get((l["id"], planta_id), 0.0)
            if kg > 0:
                por_var.setdefault(l["variedad_id"], []).append((l, kg))

    variedad_elegida = max(
        (vid for vid, xs in por_var.items() if len(xs) >= 2),
        key=lambda vid: max(kg for _, kg in por_var[vid]),
    )
    candidatos = sorted(por_var[variedad_elegida], key=lambda x: x[1])
    lote_escaso, kg_escaso = candidatos[0]
    lote_sobrante, kg_sobrante = candidatos[-1]

    pedido_kg = round(kg_escaso * 1.6, -2)  # el pedido excede lo que hay en ESE lote

    return {
        "descripcion": (
            f"Pedido de {pedido_kg:.0f} kg de {D.VAR_POR_ID[variedad_elegida]['nombre']} "
            f"contra el lote {lote_escaso['id']} en planta (hay {kg_escaso:.0f} kg) — "
            f"bloquea, y el lote {lote_sobrante['id']} (mismo calibre apto para "
            f"exportación) tiene {kg_sobrante:.0f} kg disponibles."
        ),
        "variedad_id": variedad_elegida,
        "lote_pedido_id": lote_escaso["id"],
        "ubicacion_pedido_id": planta_id,
        "kg_pedido": pedido_kg,
        "kg_disponible_en_lote": kg_escaso,
        "lote_alternativa_id": lote_sobrante["id"],
        "kg_disponible_alternativa": kg_sobrante,
    }


def plantar_inconsistencias(lg: Ledger, lotes: list[dict]) -> dict:
    """Las que el detector de Track B tiene que encontrar. Cada una imita un
    hallazgo real de la planilla de Papasud (ver PLAN_TRACKS_PAPASUD.md)."""
    plantadas = {}

    # 1) REMITO DUPLICADO — dos movimientos distintos con el mismo remito.
    m_a, m_b = R.sample([m for m in lg.movs if m["tipo"] != "ingreso_tolva"], 2)
    m_b["remito"] = m_a["remito"]
    plantadas["remito_duplicado"] = {"remito": m_a["remito"],
                                      "movimientos": [m_a["numero"], m_b["numero"]]}

    # 2) MOVIMIENTO SIN DTV — típico: se cargó el camión sin anotar el DTV.
    m_sin_dtv = R.choice([m for m in lg.movs if m["tipo"] == "entrega_cliente"])
    m_sin_dtv["dtv"] = None
    plantadas["sin_dtv"] = {"movimiento": m_sin_dtv["numero"], "lote": m_sin_dtv["lote_id"]}

    # 3) TARJETA CRUZADA — el hallazgo real de P.Chica: "tarjetas del lote 50
    #    corresponden al lote 52". Dos lotes vecinos de Santa Ana, un envío a
    #    frío se cargó con la tarjeta del vecino.
    lote_a, lote_b = [l for l in lotes if l["campo_id"] == "santa_ana"][:2]
    m_cruzado = next((m for m in lg.movs
                       if m["lote_id"] == lote_a["id"] and m["tipo"] == "envio_frio"), None)
    if m_cruzado:
        m_cruzado["tarjeta_declarada"] = lote_b["tarjeta"]
        plantadas["tarjeta_cruzada"] = {
            "movimiento": m_cruzado["numero"],
            "lote_real": lote_a["id"],
            "tarjeta_usada": lote_b["tarjeta"],
            "lote_de_la_tarjeta": lote_b["id"],
            "nota": f"Del {lote_a['id']} tienen tarjetas del lote {lote_b['id']} "
                    f"pero corresponden al {lote_a['id']}.",
        }

    # 4) FECHA INCOHERENTE — una entrega fechada antes que su propio ingreso.
    m_fecha = R.choice([m for m in lg.movs if m["tipo"] == "entrega_cliente"])
    ingreso_lote = next(m for m in lg.movs
                         if m["lote_id"] == m_fecha["lote_id"] and m["tipo"] == "ingreso_tolva")
    f_ingreso = datetime.date.fromisoformat(ingreso_lote["fecha"])
    m_fecha["fecha"] = iso(f_ingreso - datetime.timedelta(days=5))
    plantadas["fecha_incoherente"] = {
        "movimiento": m_fecha["numero"], "lote": m_fecha["lote_id"],
        "fecha_entrega": m_fecha["fecha"], "fecha_ingreso": ingreso_lote["fecha"],
    }

    # 5) KILOS QUE NO CIERRAN EN FRIGORÍFICO — un retiro que saca más de lo
    #    que había entrado a ese frigorífico para ese lote (kilos fantasma).
    pares = []
    for m_envio in [m for m in lg.movs if m["tipo"] == "envio_frio"]:
        m_retiro = next((m for m in lg.movs if m["tipo"] == "retiro_frio"
                          and m["lote_id"] == m_envio["lote_id"]
                          and m["origen_id"] == m_envio["destino_id"]), None)
        if m_retiro:
            pares.append((m_envio, m_retiro))
    m_envio, m_retiro = R.choice(pares)
    m_retiro["kg"] = round(m_envio["kg"] + 3_150.0, 1)
    plantadas["kilos_no_cierran"] = {
        "lote": m_envio["lote_id"], "frigorifico": m_envio["destino_nombre"],
        "kg_enviados": m_envio["kg"], "kg_retirados": m_retiro["kg"],
        "diferencia_kg": round(m_retiro["kg"] - m_envio["kg"], 1),
    }

    return plantadas


# ---------------------------------------------------------------------------
# 4 · CATÁLOGOS + ESCRITURA
# ---------------------------------------------------------------------------
def escribir(nombre: str, data) -> None:
    ruta = os.path.join(HERE, nombre)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    kb = os.path.getsize(ruta) / 1024
    print(f"  {nombre:<30} {kb:>8.1f} KB")


def main() -> None:
    print(f"Generando el dataset REAL de Papasud (hoy = {HOY})\n")

    lotes = generar_lotes()
    assert len(lotes) == len(D.LOTES_PLANO) + len(D.LOTES_SUELTOS)
    # regla dura: un lote, una sola variedad (por construcción, pero lo verificamos)
    assert all(isinstance(l["variedad_id"], str) for l in lotes)
    assert len({l["id"] for l in lotes}) == len(lotes), "código de lote repetido"

    lg = generar_movimientos(lotes)
    bloqueo = plantar_bloqueo_con_alternativa(lg, lotes)

    # El ledger, ANTES de plantar inconsistencias, tiene que cerrar limpio:
    # ningún (lote, ubicación) puede quedar en negativo. Si esto no cruza, el
    # modelo de movimientos está mal armado (no las inconsistencias a propósito).
    # El campo es ORIGEN, no una ubicación de inventario que trackeamos con
    # saldo inicial: drena a medida que se cosecha, y eso es esperable.
    stock_limpio = lg.stock()
    negativos = [k for k, v in stock_limpio.items()
                 if v < -1.0 and not k[1].startswith("campo:")]
    assert not negativos, f"stock negativo (imposible en un ledger bien armado): {negativos}"
    assert len(lg.movs) > 100, len(lg.movs)
    assert bloqueo["kg_pedido"] > bloqueo["kg_disponible_en_lote"]
    assert bloqueo["kg_disponible_alternativa"] > 0

    # Recién ahora plantamos las inconsistencias que el detector de Track B
    # tiene que encontrar (una de ellas ROMPE el cierre en un frigorífico a
    # propósito: "kilos que no cierran" es justamente eso, visible en la vista
    # de stock final, no en el ledger limpio de arriba).
    plantadas = plantar_inconsistencias(lg, lotes)
    stock = lg.stock()
    stock_filas = [
        {"lote_id": lid, "ubicacion_id": uid, "kg": round(kg, 1)}
        for (lid, uid), kg in stock.items() if abs(kg) > 0.5
    ]

    # ---- asserts de sanidad ----
    assert "remito_duplicado" in plantadas
    assert "sin_dtv" in plantadas
    assert "tarjeta_cruzada" in plantadas
    assert "fecha_incoherente" in plantadas
    assert "kilos_no_cierran" in plantadas

    print("Archivos:")
    escribir("lotes_real.json", {"lotes": lotes})
    escribir("movimientos_real.json", {"movimientos": lg.movs})
    escribir("stock_real.json", {"stock": stock_filas})
    escribir("bloqueo_alternativa_real.json", bloqueo)
    escribir("plantadas_real.json", plantadas)
    escribir("catalogos_real.json", {
        "campos": D.CAMPOS,
        "variedades": D.VARIEDADES,
        "frigorificos": D.FRIGORIFICOS,
        "planta": D.PLANTA,
        "clientes": D.CLIENTES,
        "transportistas": D.TRANSPORTISTAS,
        "categorias": D.CATEGORIAS,
        "calibres": D.CALIBRES,
        "meta": {
            "empresa": "Papasud S.A.", "hoy": iso(HOY), "campania": D.CAMPANIA_ACTUAL,
            "sintetico": True,
            "nota": "Catálogos (variedades, campos, lotes, frigoríficos, clientes, "
                    "transportistas) son datos REALES provistos por Papasud. Los "
                    "movimientos y kilos son sintéticos pero deterministas.",
        },
    })

    kg_total = sum(l["kg_cosechado"] for l in lotes)
    print(f"""
Resumen del dataset real
  Lotes                      {len(lotes)}  (L30-L79 + 10 códigos sueltos)
  Kg cosechados (total)      {kg_total:,.0f} kg
  Movimientos                {len(lg.movs)}
  Filas de stock (>0)        {len(stock_filas)}
  Bloqueo-con-alternativa    lote {bloqueo['lote_pedido_id']} -> alternativa {bloqueo['lote_alternativa_id']}
  Inconsistencias plantadas  {len(plantadas)}
""".replace(",", "."))


if __name__ == "__main__":
    main()
