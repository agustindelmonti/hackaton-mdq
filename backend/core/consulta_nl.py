"""
consulta_nl.py · De «¿tenés 1.200 bolsas de Spunta?» a una consulta con números.

EL MODELO INTERPRETA EL LENGUAJE. EL CÓDIGO BUSCA EL NÚMERO.

Este módulo hace la primera mitad, y la hace **sin modelo**: reconoce variedad,
calibre, ubicación, lote y cantidad contra el catálogo real que salió de la
planilla. Es determinista, corre en milisegundos y funciona con el wifi caído.

Por qué importa que funcione sin modelo: el dueño está manejando y pregunta por
el celular. Si la respuesta depende de que un servicio conteste, la respuesta a
veces no llega. Ángela le pone la voz y el contexto arriba de esto, pero el
número sale de acá abajo aunque no haya nadie escuchando.

LO QUE NO HACE: desempatar solo. Si la pregunta dice «spunta» y hay doce lotes
de spunta, no elige uno — devuelve los candidatos y los muestra. Elegir el lote
equivocado son bolsones reales en una cámara real.
"""
from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from . import papasud_real as real

# El vocabulario de ellos, no el nuestro. «frío» es un frigorífico, «el galpón»
# es el de Mar del Plata, «la planta» es la de la báscula.
SINONIMOS_UBICACION = {
    "planta_mdp": ["planta", "la planta", "mar del plata", "mdp", "bascula", "báscula"],
    "galpon_mdp": ["galpon", "galpón", "el galpon", "el galpón"],
    "dospanca": ["dospanca", "dos panca"],
    "cecive": ["cecive"],
    "sasula": ["sasula", "sasula balcarce", "balcarce"],
    "belmonte": ["belmonte"],
    "frigopap": ["frigopap"],
    "pancani": ["pancani", "panc"],
    "teramal": ["teramal"],
}

SINONIMOS_CALIBRE = {
    "exportacion": ["exportacion", "exportación", "expo", "para exportar",
                    "de exportacion", "de exportación"],
    "sin chicas": ["sin chicas", "sin chica", "s/chica", "s/chicas"],
    "recibo": ["recibo"],
    "granel": ["granel", "a granel", "suelto"],
}

UNIDAD_BOLSAS = ["bolsa", "bolsas", "bolson", "bolsón", "bolsones"]
UNIDAD_TON = ["tonelada", "toneladas", "ton", "tn", "t."]

# Preguntas que NO son de stock. Se detectan acá para mandarlas al módulo que
# corresponde en vez de contestar cualquier cosa con el stock a mano.
INTENCIONES = {
    "venta_cliente": [r"\bcu[aá]nto le (vend|compr)", r"\bvend\w+ a\b",
                      r"\bqu[eé] le (vendimos|mandamos)", r"\bcompr[oó] "],
    "trazabilidad": [r"\bde d[oó]nde (sali|vino|viene)", r"\brecorrido\b",
                     r"\bhistoria del lote\b", r"\btrazabilidad\b"],
    "liquidacion": [r"\bcu[aá]nto (le )?(tengo que )?pag", r"\bflete", r"\bliquidaci"],
    "disponibilidad": [r"\bteng\w*\b", r"\bten[eé]s\b", r"\bhay\b", r"\bqueda\w*\b",
                       r"\bdisponible", r"\bnecesito\b", r"\bstock\b"],
}


def _sn(s: str) -> str:
    t = unicodedata.normalize("NFKD", str(s or ""))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


@lru_cache(maxsize=1)
def _catalogo() -> dict:
    variedades, lotes, clientes = set(), {}, set()
    for l in real.lotes():
        if l.get("variedad"):
            variedades.add(l["variedad"])
        lotes[l["id"]] = l
    for m in real.movimientos():
        d = m.get("destino")
        if d and d.get("tipo") == "cliente":
            clientes.add(d["id"])
    return {"variedades": sorted(variedades), "lotes": lotes,
            "clientes": sorted(clientes)}


def variedades() -> list[str]:
    return _catalogo()["variedades"]


def clientes() -> list[str]:
    return _catalogo()["clientes"]


# ---------------------------------------------------------------------------
# Cantidades. En la planilla los miles van con punto: «1.200 bolsas» son mil
# doscientas, no una con dos décimas.
# ---------------------------------------------------------------------------
_RE_CANT = re.compile(r"(\d{1,3}(?:\.\d{3})+|\d+(?:,\d+)?|\d+)")


def _cantidad(texto: str) -> tuple[float | None, str]:
    t = _sn(texto)
    for m in _RE_CANT.finditer(t):
        crudo = m.group(1)
        # Un número que es claramente un remito o un DTV no es una cantidad.
        cola = t[m.end():m.end() + 24]
        if re.match(r"\s*-\s*\d", cola):
            continue
        valor = float(crudo.replace(".", "").replace(",", "."))
        unidad = "kg"
        contexto = t[max(0, m.start() - 14):m.end() + 24]
        if any(u in contexto for u in UNIDAD_BOLSAS):
            unidad = "bolsas"
        elif any(re.search(rf"\b{re.escape(u)}", contexto) for u in UNIDAD_TON):
            valor, unidad = valor * 1000, "kg"
        elif re.search(r"\blote\s*$", t[:m.start()]):
            continue                      # «el lote 300» no es una cantidad
        return valor, unidad
    return None, "kg"


def _buscar(texto: str, mapa: dict[str, list[str]]) -> str | None:
    t = _sn(texto)
    mejor, largo = None, 0
    for clave, palabras in mapa.items():
        for p in palabras:
            p = _sn(p)
            if re.search(rf"(?<![a-z]){re.escape(p)}(?![a-z])", t) and len(p) > largo:
                mejor, largo = clave, len(p)
    return mejor


def _variedad(texto: str) -> tuple[str | None, list[str]]:
    t = _sn(texto)
    hits = [v for v in variedades()
            if re.search(rf"(?<![a-z]){re.escape(_sn(v))}(?![a-z])", t)]
    if len(hits) == 1:
        return hits[0], []
    return (None, hits) if hits else (None, [])


def _lote(texto: str) -> str | None:
    m = re.search(r"\blote\s*n?[°º]?\s*([a-z0-9 ]{1,5}?)\b", _sn(texto))
    if not m:
        return None
    cand = m.group(1).strip()
    return cand if cand in _catalogo()["lotes"] else None


def _cliente(texto: str) -> str | None:
    t = _sn(texto)
    mejor, largo = None, 0
    for c in clientes():
        # Se busca por cualquier palabra propia del nombre: ellos dicen «wemar»
        # y en la planilla figura «wemar-mc cain».
        for parte in re.split(r"[\s\-()]+", _sn(c)):
            if len(parte) < 4:
                continue
            if re.search(rf"(?<![a-z]){re.escape(parte)}(?![a-z])", t) and len(parte) > largo:
                mejor, largo = c, len(parte)
    return mejor


def _intencion(texto: str) -> str:
    t = _sn(texto)
    for nombre in ("venta_cliente", "liquidacion", "trazabilidad", "disponibilidad"):
        for patron in INTENCIONES[nombre]:
            if re.search(patron, t):
                return nombre
    return "disponibilidad"


def interpretar(texto: str) -> dict:
    """Devuelve qué se entendió, y qué quedó sin resolver.

    Lo ambiguo se declara: `ambiguo` trae los candidatos para que elija una
    persona. El sistema nunca desempata solo.
    """
    cantidad, unidad = _cantidad(texto)
    variedad, candidatas = _variedad(texto)
    p = {
        "texto": texto,
        "intencion": _intencion(texto),
        "variedad": variedad,
        "calibre": _buscar(texto, SINONIMOS_CALIBRE),
        "ubicacion": _buscar(texto, SINONIMOS_UBICACION),
        "lote": _lote(texto),
        "cliente": _cliente(texto),
        "cantidad": cantidad,
        "unidad": unidad,
        "ambiguo": {},
    }
    if candidatas:
        p["ambiguo"]["variedad"] = candidatas
    if p["lote"] and p["variedad"]:
        lo = _catalogo()["lotes"].get(p["lote"], {})
        if lo.get("variedad") and lo["variedad"] != p["variedad"]:
            # Un lote tiene UNA variedad. Si la pregunta las cruza, se avisa en
            # vez de devolver cero kilos sin explicar por qué.
            p["ambiguo"]["lote_variedad"] = (
                f"el lote {p['lote']} es {lo['variedad']}, no {p['variedad']}")
    return p


def entendido(p: dict) -> str:
    """Lo que la máquina escuchó, en una línea, para que la persona confirme."""
    partes = []
    if p.get("cantidad"):
        n = f"{round(p['cantidad']):,}".replace(",", ".")
        partes.append(f"{n} {p['unidad']}")
    if p.get("variedad"):
        partes.append(p["variedad"].title())
    if p.get("calibre"):
        partes.append(f"calibre {p['calibre']}")
    if p.get("lote"):
        partes.append(f"lote {p['lote']}")
    if p.get("ubicacion"):
        partes.append(f"en {real.nombre_ubicacion(p['ubicacion'])}")
    if p.get("cliente"):
        partes.append(f"cliente {p['cliente'].title()}")
    return " · ".join(partes) if partes else "no reconocí nada concreto"
