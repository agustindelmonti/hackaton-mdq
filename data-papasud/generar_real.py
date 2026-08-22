"""
generar_real.py · Generador determinista del dataset real de Papasud.

Reemplaza generar.py (el dataset viejo de "4 depósitos de semilla fiscalizada").
Este genera el modelo de LINAJE: Campo -> Pivote -> Cuadrante -> Lote, con el
flujo real de la mercadería:

    LOTE (campo)
       |--> PLANTA (Mar del Plata)
       |       recepción/báscula → reclasificación → playa
       |         |--> CLIENTE
       |         |--> FRIGORÍFICO --> vuelve a PLANTA --> CLIENTE
       |         |--> FRIGORÍFICO --> CLIENTE (poco común)
       |--> FRIGORÍFICO (directo, poco común)
       |--> CLIENTE (directo desde el campo, poco común)

En el medio entre el lote y el frío viven entidades de verdad, no un salto:
orden de carga (papel, porque en el campo a veces no hay señal), viaje en
tolva, planilla de recepción con peso de báscula, reclasificación (granel
con tierra → bolsas).

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

    # Los 10 códigos sueltos se reparten entre los otros campos, con la
    # excepción forzada: lote 300 vive en Cayetano Chávez (charla 22/08).
    otros_campos = ["marisol", "trevelin", "oriente", "san_cayetano"]
    for i, num in enumerate(D.LOTES_SUELTOS):
        rotulo = str(num)
        campo_id = D.LOTE_CAMPO_FORZADO.get(rotulo) or otros_campos[i % len(otros_campos)]
        pivote = D.PIVOTES[i % 2]
        cuadrante = D.CUADRANTES[i % len(D.CUADRANTES)]
        lotes.append(_nuevo_lote(rotulo, campo_id, pivote, cuadrante))

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
    campo = D.CAMPO_POR_ID[campo_id]
    return {
        # REGLA DURA: una sola variedad por lote. No hay campo "variedades".
        "id": rotulo,
        "lote": rotulo,
        "campo_id": campo_id,
        "campo": campo["nombre"],
        "partido": campo.get("partido"),
        "provincia": campo.get("provincia"),
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
        "origen_laboratorio": cat["id"] == "inicial_2" and R.random() < 0.35,
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


def _chofer_de(transp: dict) -> str | None:
    return R.choice(transp["choferes"]) if transp["choferes"] else None


def _obs_cosecha() -> tuple[float, str]:
    temp = round(R.uniform(8.0, 18.5), 1)
    notas = [
        f"Cosecha a {temp} °C. Papa sucia, viene con tierra.",
        f"Temperatura de cosecha {temp} °C. Tolva a granel.",
        f"{temp} °C en lote. Sin señal: orden de carga en papel.",
        f"Cosecha {temp} °C. Remito se carga al llegar a planta.",
    ]
    return temp, R.choice(notas)


class Ledger:
    """El libro append-only. El stock es SIEMPRE una vista derivada de esto."""

    def __init__(self):
        self.movs: list[dict] = []
        self._n = 0
        self._remito = 4800
        self.ordenes: list[dict] = []
        self.recepciones: list[dict] = []
        self.reclasificaciones: list[dict] = []
        self._oc = 0
        self._rec = 0
        self._rcl = 0

    def _numero(self) -> str:
        self._n += 1
        return f"MOV-R-{self._n:04d}"

    def _num_remito(self) -> str:
        self._remito += 1
        return f"R-{self._remito}"

    def _num_oc(self) -> str:
        self._oc += 1
        return f"OC-{self._oc:04d}"

    def _num_rec(self) -> str:
        self._rec += 1
        return f"REC-{self._rec:04d}"

    def _num_rcl(self) -> str:
        self._rcl += 1
        return f"RCL-{self._rcl:04d}"

    def agregar(self, **kw) -> dict:
        tipo = kw.get("tipo")
        m = {
            "numero": self._numero(),
            "remito": kw.pop("remito", None) or self._num_remito(),
            "confirmado_en_destino": True,
            "canal": kw.pop("canal", None) or R.choice(["voz", "texto", "foto"]),
            "registrado_por": R.choice(["ruben", "marcos", "nestor", "maxi"]),
            "tipo_vehiculo": kw.pop("tipo_vehiculo", None) or D.VEHICULO_POR_TIPO.get(tipo),
            "zona_planta": kw.pop("zona_planta", None) or D.ZONA_PLANTA_POR_TIPO.get(tipo),
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

        camino = R.choices(
            ["directo_planta", "via_frigorifico", "vuelta_planta",
             "campo_a_frio", "campo_a_cliente"],
            weights=[0.28, 0.26, 0.36, 0.06, 0.04],
        )[0]

        if camino == "campo_a_cliente":
            _entregar_a_cliente(lg, lote, campo_ubic, lote["campo"],
                                 kg_total, f0 + datetime.timedelta(days=R.randint(1, 5)),
                                 atajo="campo")
            continue

        if camino == "campo_a_frio":
            frigo = R.choice(D.FRIGORIFICOS)
            frigo_ubic = f"frigorifico:{frigo['id']}"
            kg_neto = _viaje_desde_campo(lg, lote, campo_ubic, frigo_ubic,
                                         frigo["nombre"], f0, tipo="campo_a_frio",
                                         kg=kg_total)
            _entregar_a_cliente(lg, lote, frigo_ubic, frigo["nombre"],
                                 kg_neto, f0 + datetime.timedelta(days=R.randint(8, 40)))
            continue

        # (a) La cosecha entra a la planta en 1 a 3 camiones (tolva, a granel).
        n_camiones = R.randint(1, 3)
        restos = _repartir(kg_total, n_camiones)
        pesos_netos = []
        ingresos = []
        for i, kg in enumerate(restos):
            peso_neto = round(kg * R.uniform(0.985, 1.0), 1)  # báscula: tierra/humedad
            pesos_netos.append(peso_neto)
            _viaje_desde_campo(
                lg, lote, campo_ubic, planta_id, D.PLANTA["nombre"],
                f0 + datetime.timedelta(days=i), tipo="ingreso_tolva", kg=peso_neto,
            )
            ingresos.append(lg.movs[-1])

        # Lo que queda disponible en planta es lo que la BÁSCULA acreditó, no
        # el reparto teórico del lote (la báscula pesa un poco menos: tierra,
        # humedad). Si esto no cruza, el ledger da stock negativo más adelante.
        kg_en_planta = round(sum(pesos_netos), 1)
        f_actual = f0 + datetime.timedelta(days=n_camiones)

        # Reclasificación: granel con tierra → bolsas. No mueve stock (sigue
        # en planta); deja el rastro de la estación del medio.
        _reclasificar(lg, lote, ingresos, kg_en_planta, f_actual)

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
            chofer=_chofer_de(transp),
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
            chofer=_chofer_de(transp),
            camion=_camion(),
            tarjeta_declarada=lote["tarjeta"], color_bolsa=lote["color_bolsa"],
            color_hilo=lote["color_hilo"],
            valor_flete=round(kg_en_planta / 1000 * R.uniform(2_800, 3_900), -1),
            observaciones="Retiro de frío — vuelve a planta para despacho",
        )
        _entregar_a_cliente(lg, lote, planta_id, D.PLANTA["nombre"],
                             kg_en_planta, f_retiro + datetime.timedelta(days=R.randint(2, 15)))

    return lg


def _viaje_desde_campo(lg: Ledger, lote: dict, origen_id: str, destino_id: str,
                       destino_nombre: str, fecha: datetime.date, *,
                       tipo: str, kg: float) -> float:
    """Orden de carga (papel en el campo) + viaje + planilla de recepción
    cuando el destino es la planta. El kg que entra al ledger es el de la
    báscula si hay recepción; si no, el declarado en la orden."""
    transp = R.choice(D.TRANSPORTISTAS)
    chofer = _chofer_de(transp)
    camion = _camion()
    temp, obs = _obs_cosecha()
    kg_estimado = round(kg * R.uniform(0.97, 1.04), 1)
    sin_remito = tipo == "ingreso_tolva" and R.random() < 0.08
    oc_id = lg._num_oc()
    oc = {
        "id": oc_id,
        "fecha": iso(fecha),
        "lote_id": lote["id"],
        "variedad_id": lote["variedad_id"],
        "variedad": lote["variedad"],
        "campo_id": lote["campo_id"],
        "campo": lote["campo"],
        "kg_estimado": kg_estimado,
        "kg_estimado_pendiente_pesaje": True,
        "transportista_id": transp["id"],
        "chofer": chofer,
        "camion": camion,
        "tipo_vehiculo": D.VEHICULO_POR_TIPO[tipo],
        "canal": "papel",
        "sin_senal": True,
        "sin_remito": sin_remito,
        "temperatura_cosecha_c": temp,
        "observaciones": obs,
        "destino_id": destino_id,
        "destino_nombre": destino_nombre,
        "estado": "recibida",
    }
    lg.ordenes.append(oc)

    peso_bascula = round(kg, 1) if tipo == "ingreso_tolva" else None
    rec_id = None
    if tipo == "ingreso_tolva":
        rec_id = lg._num_rec()
        lg.recepciones.append({
            "id": rec_id,
            "orden_carga_id": oc_id,
            "fecha": iso(fecha),
            "lote_id": lote["id"],
            "variedad_id": lote["variedad_id"],
            "variedad": lote["variedad"],
            "campo_id": lote["campo_id"],
            "campo": lote["campo"],
            "zona_id": "recepcion",
            "zona": "Recepción / báscula",
            "kg_estimado": kg_estimado,
            "peso_bascula_kg": peso_bascula,
            "diferencia_kg": round((peso_bascula or 0) - kg_estimado, 1),
            "transportista_id": transp["id"],
            "chofer": chofer,
            "camion": camion,
            "tipo_vehiculo": "tolva",
            "temperatura_cosecha_c": temp,
            "observaciones": "Planilla de recepción — primer ingreso a planta.",
            "sin_remito_de_origen": sin_remito,
            "registrado_por": R.choice(["ruben", "marcos", "nestor"]),
        })

    mov = lg.agregar(
        tipo=tipo,
        dtv=_dtv(lg._n + 1),
        fecha=iso(fecha),
        lote_id=lote["id"], variedad_id=lote["variedad_id"],
        kg=round(kg, 1),
        bolsas=None if tipo == "ingreso_tolva" else round(kg / lote["kg_por_bolsa"]),
        origen_id=origen_id, origen_nombre=lote["campo"],
        destino_id=destino_id, destino_nombre=destino_nombre,
        transportista_id=transp["id"],
        chofer=chofer,
        camion=camion,
        peso_bascula_kg=peso_bascula,
        valor_flete=round(kg / 1000 * R.uniform(3_200, 4_600), -1),
        observaciones=("Ingreso Tolva — a granel, con tierra" if tipo == "ingreso_tolva"
                       else f"Campo a frío — {destino_nombre}"),
        orden_carga_id=oc_id,
        recepcion_id=rec_id,
        temperatura_cosecha_c=temp,
        canal="papel" if sin_remito else None,
    )
    oc["movimiento_id"] = mov["numero"]
    oc["remito"] = mov["remito"]
    if rec_id:
        lg.recepciones[-1]["movimiento_id"] = mov["numero"]
        lg.recepciones[-1]["remito"] = mov["remito"]
    return round(kg, 1)


def _reclasificar(lg: Ledger, lote: dict, ingresos: list[dict],
                  kg_en_planta: float, fecha: datetime.date) -> None:
    bolsas = round(kg_en_planta / lote["kg_por_bolsa"])
    tierra = round(sum(max(0.0, (m.get("kg") or 0) * 0.008) for m in ingresos), 1)
    lg.reclasificaciones.append({
        "id": lg._num_rcl(),
        "fecha": iso(fecha),
        "lote_id": lote["id"],
        "variedad_id": lote["variedad_id"],
        "variedad": lote["variedad"],
        "zona_id": "reclasificacion",
        "zona": "Reclasificación y empaque",
        "kg_granel": kg_en_planta,
        "kg_embolsado": kg_en_planta,
        "bolsas": bolsas,
        "calibre_id": lote["calibre_id"],
        "calibre": lote["calibre"],
        "tierra_kg": tierra,
        "ingresos": [m["numero"] for m in ingresos],
        "observaciones": (
            "Granel con tierra → bolsas. La merma de tierra ya la descontó la "
            "báscula; acá no se vuelve a restar del stock."
        ),
    })


def _repartir(total: float, n: int) -> list[float]:
    if n == 1:
        return [round(total, 1)]
    cortes = sorted(R.uniform(0.15, 0.85) for _ in range(n - 1))
    bordes = [0.0] + cortes + [1.0]
    return [round(total * (bordes[i + 1] - bordes[i]), 1) for i in range(n)]


def _entregar_a_cliente(lg: Ledger, lote: dict, origen_id: str, origen_nombre: str,
                         kg: float, fecha: datetime.date, atajo: str | None = None) -> None:
    # No todo lo disponible se vende ya: dejamos un remanente vendible (esto
    # es lo que hace que "disponibilidad" tenga sentido en la demo).
    kg_vender = round(kg * R.uniform(0.35, 0.75), 1)
    if kg_vender < 500:
        return
    cliente = R.choice(D.CLIENTES)
    bolsas = round(kg_vender / lote["kg_por_bolsa"])
    transp = R.choice(D.TRANSPORTISTAS)
    nota = f"Entrega a {cliente['nombre']}"
    if atajo == "campo":
        nota = f"Atajo campo → cliente (sin pasar por planta) — {cliente['nombre']}"
    elif origen_id.startswith("frigorifico:"):
        nota = f"Sale de frío directo a {cliente['nombre']} (poco común)"
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
        chofer=_chofer_de(transp),
        camion=_camion(),
        tarjeta_declarada=lote["tarjeta"], color_bolsa=lote["color_bolsa"],
        color_hilo=lote["color_hilo"],
        valor_flete=round(kg_vender / 1000 * R.uniform(3_000, 4_200), -1),
        observaciones=nota,
        zona_planta="playa" if origen_id == D.PLANTA["id"] else None,
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
    ingreso_lote = next((m for m in lg.movs
                         if m["lote_id"] == m_fecha["lote_id"]
                         and m["tipo"] in ("ingreso_tolva", "campo_a_frio")), None)
    if ingreso_lote is None:
        ingreso_lote = next(m for m in lg.movs if m["lote_id"] == m_fecha["lote_id"])
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

    # 6) ORDEN DE CARGA SIN REMITO — "che, te lo mandé sin remito". El campo
    #    cargó el camión y el papel llegó después (o no llegó).
    ocs_sin = [o for o in lg.ordenes if o.get("sin_remito")]
    if ocs_sin:
        oc = ocs_sin[0]
        plantadas["orden_sin_remito"] = {
            "orden_carga_id": oc["id"], "lote": oc["lote_id"],
            "campo": oc["campo"], "camion": oc["camion"],
            "nota": "Salió del campo sin remito. La recepción en planta lo cargó después.",
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
    print(f"  {nombre:<36} {kb:>8.1f} KB")


def main() -> None:
    print(f"Generando el dataset REAL de Papasud (hoy = {HOY})\n")

    lotes = generar_lotes()
    assert len(lotes) == len(D.LOTES_PLANO) + len(D.LOTES_SUELTOS)
    # regla dura: un lote, una sola variedad (por construcción, pero lo verificamos)
    assert all(isinstance(l["variedad_id"], str) for l in lotes)
    assert len({l["id"] for l in lotes}) == len(lotes), "código de lote repetido"
    lote_300 = next(l for l in lotes if l["id"] == "300")
    assert lote_300["campo_id"] == "san_cayetano", lote_300["campo_id"]

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
    assert lg.ordenes, "sin órdenes de carga no hay rastro del campo"
    assert lg.recepciones, "sin planilla de recepción la planta no existe"
    assert lg.reclasificaciones, "falta la estación del medio (granel → bolsas)"
    assert any(m["tipo"] == "ingreso_tolva" for m in lg.movs)
    assert any(m["tipo"] == "campo_a_frio" for m in lg.movs)
    assert any(m["tipo"] == "entrega_cliente" and m["origen_id"].startswith("campo:")
               for m in lg.movs)

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
    escribir("ordenes_carga_real.json", {"ordenes": lg.ordenes})
    escribir("recepciones_planta_real.json", {"recepciones": lg.recepciones})
    escribir("reclasificaciones_real.json", {"reclasificaciones": lg.reclasificaciones})
    escribir("stock_real.json", {"stock": stock_filas})
    escribir("bloqueo_alternativa_real.json", bloqueo)
    escribir("plantadas_real.json", plantadas)
    escribir("catalogos_real.json", {
        "laboratorio": D.LABORATORIO,
        "campos": D.CAMPOS,
        "variedades": D.VARIEDADES,
        "frigorificos": D.FRIGORIFICOS,
        "planta": D.PLANTA,
        "zonas_planta": D.ZONAS_PLANTA,
        "tipos_vehiculo": D.TIPOS_VEHICULO,
        "clientes": D.CLIENTES,
        "transportistas": D.TRANSPORTISTAS,
        "categorias": D.CATEGORIAS,
        "calibres": D.CALIBRES,
        "roles_operacion": D.ROLES_OPERACION,
        "sistema_contable": D.SISTEMA_CONTABLE,
        "tipos_movimiento": D.TIPOS_MOVIMIENTO,
        "meta": {
            "empresa": "Papasud S.A.", "hoy": iso(HOY), "campania": D.CAMPANIA_ACTUAL,
            "sintetico": True,
            "regla_flujo": (
                "lote → planta (recepción/báscula → reclasificación → playa) → "
                "cliente | frío. El frío suele volver a planta. Atajos: campo→frío "
                "y campo→cliente."
            ),
            "nota": "Catálogos (variedades, campos, lotes, frigoríficos, clientes, "
                    "transportistas) son datos REALES provistos por Papasud. Los "
                    "movimientos y kilos son sintéticos pero deterministas. "
                    "Cayetano Chávez / lote 300 sale de la charla del 22/08.",
        },
    })

    kg_total = sum(l["kg_cosechado"] for l in lotes)
    n_tolva = sum(1 for m in lg.movs if m["tipo"] == "ingreso_tolva")
    print(f"""
Resumen del dataset real
  Lotes                      {len(lotes)}  (L30-L79 + 10 códigos sueltos)
  Campos                     {len(D.CAMPOS)}  (incluye Cayetano Chávez)
  Kg cosechados (total)      {kg_total:,.0f} kg
  Movimientos                {len(lg.movs)}
  Ingresos tolva             {n_tolva}
  Órdenes de carga           {len(lg.ordenes)}
  Recepciones de planta      {len(lg.recepciones)}
  Reclasificaciones          {len(lg.reclasificaciones)}
  Filas de stock (>0)        {len(stock_filas)}
  Bloqueo-con-alternativa    lote {bloqueo['lote_pedido_id']} -> alternativa {bloqueo['lote_alternativa_id']}
  Inconsistencias plantadas  {len(plantadas)}
""".replace(",", "."))


if __name__ == "__main__":
    main()
