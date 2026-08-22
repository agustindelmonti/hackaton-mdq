"""
movimientos.py · N01 — el stock se mueve hablando, no tipeando en una planilla.

EL PROBLEMA QUE RESUELVE (textual del brief): «El registro se hace en una
planilla que varias personas editan al mismo tiempo, lo que genera errores de
versión.» Cuatro ubicaciones, una sola planilla compartida, y nadie sabe cuál es
la última versión.

Acá no hay planilla. Un operario dice «pasé dieciocho bolsones de Spunta de
Ruta 226 al galpón» y eso se convierte en una TRANSACCIÓN con lote, cantidad,
origen y destino. El registro es de a una fila, atribuido a una persona, con
hora — no hay versión que se pise.

DÓNDE ESTÁ EL LÍMITE (el principio de la casa):

    El MODELO interpreta el lenguaje: de qué lote habla, si es un traslado o un
    egreso, a qué ubicación se refiere cuando dice «el galpón».

    El CÓDIGO valida los números y los identificadores: que el lote exista, que
    la ubicación exista, que la cantidad sea un número, y sobre todo QUE HAYA
    ESE STOCK EN EL ORIGEN. «Dieciocho» y «ochenta» suenan parecido adentro de
    una cámara con el motor andando, y la diferencia son sesenta y dos bolsones.

LA VALIDACIÓN DE DISPONIBILIDAD (lo que pide el brief para evitar discrepancias
entre origen y destino): un movimiento no se registra si el origen no tiene los
kilos. No es una advertencia — es un rechazo. Lo que sí se puede registrar es
el movimiento PARCIAL de lo que efectivamente hay, y el sistema lo dice.

EL ESTADO `en_transito` es la pieza que hoy no existe en la planilla y que causa
el problema entero: entre que los bolsones salen de una cámara y alguien los
confirma en la otra, esos kilos NO ESTÁN EN NINGÚN LADO. Mientras nadie
confirme, no se cuentan como disponibles en destino ni siguen disponibles en
origen: quedan a la vista, con nombre y fecha, en `sin_confirmar()`.
"""
from __future__ import annotations

import datetime
import unicodedata

from . import esquema, semilla, store
from .fechas import hoy, parse_fecha

APARTADO = "movimientos"

TIPOS = {
    "ingreso":    "entra semilla desde un campo de producción",
    "traslado":   "se mueve entre dos ubicaciones propias",
    "egreso":     "sale hacia un cliente",
    "descarte":   "se da de baja por sanidad o brotación",
    "reproceso":  "sale del frío a planta para trabajar o repasar",
    "retorno":    "vuelve al origen (galpón, planta, frío) sin ser un egreso",
}

# Un traslado que nadie confirmó en destino después de esto es un problema, no
# un movimiento en curso. Sale de la regla que el encargado le enseñó al sistema
# (core/conocimiento.py, pieza K-004): «esos kilos no están en ningún lado».
HORAS_LIMITE_CONFIRMACION = 72


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def _filas() -> list[dict]:
    return esquema.filas(APARTADO)


def hay_datos() -> bool:
    return bool(_filas())


def listar(limite: int | None = None, lote: str | None = None,
           ubicacion: str | None = None, tipo: str | None = None) -> list[dict]:
    """Los movimientos, del más nuevo al más viejo, con los filtros del oficio."""
    out = []
    for m in _filas():
        if lote and _norm(m.get("lote")) != _norm(lote):
            continue
        if tipo and m.get("tipo") != tipo:
            continue
        if ubicacion:
            u = _norm(ubicacion)
            if u not in _norm(m.get("origen")) and u not in _norm(m.get("destino")):
                continue
        out.append(dict(m))
    out.sort(key=lambda m: (str(m.get("fecha") or ""), str(m.get("numero") or "")),
             reverse=True)
    return out[:limite] if limite else out


# ---------------------------------------------------------------------------
# Resolución de identificadores — el modelo propone, el código decide
# ---------------------------------------------------------------------------
def buscar_lote(texto: str) -> list[dict]:
    """Los lotes que podrían ser el que la persona nombró.

    NUNCA elige solo. Si «Spunta» matchea nueve lotes, devuelve los nueve y
    alguien decide: elegir por el sistema el lote equivocado mueve kilos reales
    de una cámara real. Si el texto es el rótulo exacto, hay un solo candidato y
    el flujo sigue sin preguntar.
    """
    t = _norm(texto)
    if not t:
        return []
    arts = store.raw_actual()
    exactos = [a for a in arts
               if _norm(a.get("lote")) == t or str(a.get("codigo")) == t.strip()]
    if exactos:
        return [dict(a) for a in exactos]
    parciales = [a for a in arts
                 if t in _norm(a.get("lote"))
                 or t in _norm(a.get("variedad"))
                 or t in _norm(a.get("descripcion"))]
    # los de más kilos primero: es el que la persona probablemente está mirando
    parciales.sort(key=lambda a: -abs(float(a.get("stock") or 0)))
    return [dict(a) for a in parciales[:12]]


def buscar_ubicacion(texto: str) -> dict | None:
    """«el galpón», «Ruta 226», «Batán», «la cámara 3 de Sierra» → la ubicación.

    La gente no dice «Frigorífico Sierra de los Padres»: dice «Sierra». El
    matcheo va de lo más específico a lo más laxo y, si queda ambiguo, devuelve
    None — mejor preguntar que adivinar un destino.
    """
    t = _norm(texto)
    if not t:
        return None
    ubis = semilla.ubicaciones()
    for u in ubis:
        if _norm(u["nombre"]) == t or u["id"] == t:
            return dict(u)
        if t in [_norm(a) for a in (u.get("alias") or [])]:
            return dict(u)
    # por palabra distintiva del nombre ("galpón", "batán", "226", "sierra")
    hits = [u for u in ubis
            if _norm(u["nombre"]).find(t) >= 0 or t in _norm(u["id"])]
    if len(hits) == 1:
        return dict(hits[0])
    # por tipo: "el galpón" es uno solo
    if t in ("galpon", "el galpon", "deposito seco"):
        galpones = [u for u in ubis if u.get("tipo") == "galpon"]
        if len(galpones) == 1:
            return dict(galpones[0])
    return None


# ---------------------------------------------------------------------------
# Disponibilidad — el corazón de N01
# ---------------------------------------------------------------------------
def disponible(codigo: int, ubicacion_id: str | None = None) -> dict:
    """Cuántos kilos de este lote hay REALMENTE disponibles en una ubicación.

    Disponible = lo que está en cámara − lo que ya salió sin confirmar −
    lo que está comprometido en una orden de carga abierta.

    Esa resta es la que la planilla no hace, y es la razón por la que la
    diferencia aparece recién cuando el camión está cargando.
    """
    art = next((a for a in store.raw_actual() if a.get("codigo") == codigo), None)
    if not art:
        return {"existe": False, "codigo": codigo}
    en_camara = float(art.get("stock") or 0)
    uid = ubicacion_id or art.get("ubicacion_id")

    # kilos que salieron de acá y nadie confirmó en destino
    en_transito = 0.0
    for m in _filas():
        if m.get("codigo") != codigo:
            continue
        if m.get("estado") != "en_transito":
            continue
        if _norm(m.get("origen")) == _norm(_nombre_ubicacion(uid)):
            en_transito += float(m.get("kg") or 0)

    comprometido = _comprometido_en_ordenes(codigo)
    libre = en_camara - en_transito - comprometido
    return {
        "existe": True,
        "codigo": codigo,
        "lote": art.get("lote"),
        "descripcion": art.get("descripcion"),
        "ubicacion_id": uid,
        "ubicacion": _nombre_ubicacion(uid),
        "camara": art.get("camara"),
        "en_camara_kg": round(en_camara, 1),
        "en_transito_kg": round(en_transito, 1),
        "comprometido_kg": round(comprometido, 1),
        "disponible_kg": round(libre, 1),
        "disponible_bolsones": round(libre / 1000, 2),
        # Disponible negativo NO es un error de cálculo: es un lote que ya se
        # prometió más veces de las que se puede cumplir. Tiene nombre propio
        # porque es exactamente el problema que termina en el papelón frente al
        # cliente, y conviene decirlo con todas las letras.
        "sobrecomprometido": libre < 0,
        "sobrecomprometido_kg": round(-libre, 1) if libre < 0 else 0.0,
    }


def _nombre_ubicacion(uid: str | None) -> str:
    u = semilla.ubicacion(uid) if uid else None
    return u["nombre"] if u else ""


def _comprometido_en_ordenes(codigo: int) -> float:
    """Kilos ya prometidos en órdenes de carga que todavía no se despacharon."""
    total = 0.0
    for o in esquema.filas("ordenes_carga"):
        if o.get("estado") not in ("emitida", "pendiente"):
            continue
        for it in o.get("items") or []:
            if it.get("codigo") == codigo:
                total += float(it.get("kg") or 0)
    return total


# ---------------------------------------------------------------------------
# Registrar — la transacción
# ---------------------------------------------------------------------------
def validar(codigo: int, kg: float, origen_id: str | None,
            destino: str | None, tipo: str = "traslado") -> dict:
    """El peaje. Devuelve `{ok, motivo, disponibilidad}` SIN escribir nada.

    Lo llama tanto la carga por voz como la de pantalla: un movimiento dictado
    pasa por exactamente el mismo control que uno tipeado."""
    if tipo not in TIPOS:
        return {"ok": False, "motivo": "tipo_desconocido", "tipo": tipo}
    try:
        kg = float(kg)
    except (TypeError, ValueError):
        return {"ok": False, "motivo": "cantidad_invalida", "kg": kg}
    if kg <= 0:
        return {"ok": False, "motivo": "cantidad_invalida", "kg": kg}

    disp = disponible(codigo, origen_id)
    if not disp.get("existe"):
        return {"ok": False, "motivo": "lote_inexistente", "codigo": codigo}

    # Un ingreso viene de afuera: no se valida disponibilidad de origen.
    if tipo == "ingreso":
        return {"ok": True, "disponibilidad": disp}

    if destino and _norm(destino) == _norm(disp["ubicacion"]):
        return {"ok": False, "motivo": "origen_igual_destino",
                "ubicacion": disp["ubicacion"], "disponibilidad": disp}

    if kg > disp["disponible_kg"]:
        return {
            "ok": False,
            "motivo": "sin_stock_suficiente",
            "pedido_kg": round(kg, 1),
            "disponible_kg": disp["disponible_kg"],
            "faltante_kg": round(kg - disp["disponible_kg"], 1),
            "disponibilidad": disp,
        }
    return {"ok": True, "disponibilidad": disp}


def registrar(codigo: int, kg: float, destino: str, actor: str,
              tipo: str = "traslado", origen_id: str | None = None,
              nota: str | None = None, canal: str = "texto") -> dict:
    """Escribe el movimiento. Sólo si pasa `validar()`.

    Un traslado entre ubicaciones propias nace `en_transito`: los kilos salieron
    pero todavía nadie los vio llegar. Un egreso a cliente y un descarte se
    cierran en el acto (no hay nadie del otro lado que confirme adentro del
    sistema). Un ingreso desde campo entra confirmado.
    """
    v = validar(codigo, kg, origen_id, destino, tipo)
    if not v["ok"]:
        return v
    disp = v["disponibilidad"]
    kg = float(kg)

    filas = _filas()
    numero = _siguiente_numero(filas)
    art = next((a for a in store.raw_actual() if a.get("codigo") == codigo), {})
    es_traslado_interno = (tipo in ("traslado", "reproceso", "retorno")
                           and semilla.ubicacion_por_nombre(destino))

    mov = {
        "numero": numero,
        "fecha": hoy().isoformat(),
        "hora": datetime.datetime.now().strftime("%H:%M"),
        "tipo": tipo,
        "lote": art.get("lote"),
        "codigo": codigo,
        "variedad": art.get("variedad"),
        "kg": round(kg, 1),
        "bolsones": round(kg / 1000, 2),
        "origen": disp["ubicacion"] if tipo != "ingreso" else (nota or "Campo"),
        "destino": destino,
        "registrado_por": actor,
        "estado": "en_transito" if es_traslado_interno else "confirmado",
        "confirmado_en_destino": not es_traslado_interno,
        "canal": canal,
    }
    if nota:
        mov["nota"] = nota

    esquema.crear_apartado(APARTADO, [mov])
    _aplicar_al_stock(mov)
    store.audit.record(actor=actor, accion="registrar_movimiento",
                 antes={"lote": mov["lote"], "stock": disp["en_camara_kg"],
                        "ubicacion": disp["ubicacion"]},
                 despues={"numero": numero, "tipo": tipo, "kg": mov["kg"],
                          "destino": destino, "estado": mov["estado"]})
    return {"ok": True, "movimiento": mov,
            "disponible_despues_kg": round(disp["disponible_kg"] - kg, 1)}


def _siguiente_numero(filas: list[dict]) -> str:
    n = 0
    for m in filas:
        num = str(m.get("numero") or "")
        if num.startswith("MOV-"):
            try:
                n = max(n, int(num.rsplit("-", 1)[-1]))
            except ValueError:
                pass
    return f"MOV-{hoy().year}-{n + 1:04d}"


def _aplicar_al_stock(mov: dict) -> None:
    """El movimiento toca el stock del lote. Un traslado entre ubicaciones NO
    duplica: descuenta del origen y, al confirmarse en destino, actualiza dónde
    está. Un egreso o un descarte descuentan y listo."""
    codigo = mov.get("codigo")
    kg = float(mov.get("kg") or 0)
    raw = store.raw_actual()
    art = next((a for a in raw if a.get("codigo") == codigo), None)
    if not art:
        return
    if mov["tipo"] == "ingreso":
        art["stock"] = round(float(art.get("stock") or 0) + kg, 1)
    else:
        art["stock"] = round(float(art.get("stock") or 0) - kg, 1)
    art["inmovilizado"] = round(float(art["stock"]) * float(art.get("costo_iva") or 0), 2)
    store.guardar(raw)


def confirmar_en_destino(numero: str, actor: str) -> dict:
    """Alguien del otro lado dice «llegó». Recién ahí los kilos existen en destino.

    Este es el paso que hoy no existe, y por eso la diferencia entre origen y
    destino se descubre frente al cliente."""
    filas = _filas()
    mov = next((m for m in filas if m.get("numero") == numero), None)
    if not mov:
        return {"ok": False, "motivo": "movimiento_inexistente", "numero": numero}
    if mov.get("estado") != "en_transito":
        return {"ok": False, "motivo": "no_esta_en_transito",
                "numero": numero, "estado": mov.get("estado")}

    destino = semilla.ubicacion_por_nombre(mov.get("destino") or "")
    mov["estado"] = "confirmado"
    mov["confirmado_en_destino"] = True
    mov["confirmado_por"] = actor
    mov["confirmado_fecha"] = hoy().isoformat()
    esquema.reemplazar_filas(APARTADO, filas)

    # el lote ahora vive en el destino
    if destino:
        raw = store.raw_actual()
        art = next((a for a in raw if a.get("codigo") == mov.get("codigo")), None)
        if art:
            art["ubicacion_id"] = destino["id"]
            art["ubicacion"] = destino["nombre"]
            art["camara"] = (destino.get("camaras") or [""])[0]
            store.guardar(raw)

    store.audit.record(actor=actor, accion="confirmar_movimiento",
                 antes={"numero": numero, "estado": "en_transito"},
                 despues={"estado": "confirmado", "destino": mov.get("destino")})
    return {"ok": True, "movimiento": mov}


# ---------------------------------------------------------------------------
# Lo que quedó en el aire
# ---------------------------------------------------------------------------
def sin_confirmar(horas: int = HORAS_LIMITE_CONFIRMACION) -> list[dict]:
    """Traslados que salieron y nadie confirmó en destino.

    Ordenados por antigüedad: el de arriba es el que más tiempo lleva sin
    aparecer, y probablemente el que está causando la diferencia de hoy."""
    h = hoy()
    out = []
    for m in _filas():
        if m.get("estado") != "en_transito":
            continue
        f = parse_fecha(m.get("fecha"))
        d = (h - f).days if f else 0
        out.append({**m, "dias_en_transito": d, "vencido": d * 24 >= horas})
    out.sort(key=lambda m: -m["dias_en_transito"])
    return out


def resumen() -> dict:
    """El pulso de los movimientos: cuánto se movió, por quién y qué quedó abierto."""
    filas = _filas()
    abiertos = sin_confirmar()
    h = hoy()
    ultimos_7 = [m for m in filas
                 if (f := parse_fecha(m.get("fecha"))) and 0 <= (h - f).days <= 7]
    kg_transito = sum(float(m.get("kg") or 0) for m in abiertos)
    por_canal: dict[str, int] = {}
    for m in filas:
        c = m.get("canal") or "texto"
        por_canal[c] = por_canal.get(c, 0) + 1
    return {
        "hay_datos": bool(filas),
        "total": len(filas),
        "ultimos_7_dias": len(ultimos_7),
        "sin_confirmar": len(abiertos),
        "sin_confirmar_vencidos": sum(1 for m in abiertos if m["vencido"]),
        "kg_en_transito": round(kg_transito, 1),
        "bolsones_en_transito": round(kg_transito / 1000, 2),
        "por_canal": por_canal,
    }
