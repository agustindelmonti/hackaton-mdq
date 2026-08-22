"""
valorizacion.py · Cuánto vale lo que hay en cámara.

En Papasud el "artículo" del núcleo de verdad es un LOTE DE SEMILLA, y todo se
mide en kilos: no hay unidades sueltas, ni calibre de mostrador, ni precio de
góndola. Un lote tiene un costo de producción por kilo y un precio de venta por
kilo (distinto según sea mercado interno o exportación), y el valor inmovilizado
es simplemente kilos × costo.

Este módulo reemplaza al `pricing` de la línea de retail: misma posición en el
núcleo (lo consume `store.panorama()`), pero las preguntas que responde son las
del negocio de la semilla — cuánta plata hay parada en la cámara 2, cuánto vale
un bolsón, y si un lote se está vendiendo por debajo de lo que costó producirlo.
"""
from __future__ import annotations

UNIDAD = "kg"          # en semilla NO hay ambigüedad de unidad: siempre kilos
KG_POR_BOLSON = 1000   # el bolsón (big bag) estándar de movimiento interno


def unidad(_art: dict) -> str:
    """Siempre kilos. Existe para que el núcleo no tenga que preguntar."""
    return UNIDAD


def label_precio(_art: dict) -> str:
    return "$/kg"


def margen_pct(art: dict) -> float | None:
    """Margen del lote: (precio − costo) / precio. None si falta algún lado."""
    costo = art.get("costo_kg")
    precio = art.get("precio_kg")
    if not costo or not precio or precio <= 0:
        return None
    return round((precio - costo) / precio * 100, 2)


def es_a_perdida(art: dict) -> bool:
    """Un lote cuyo precio de lista no cubre el costo de producción. Es un dato
    a CORREGIR, no una decisión comercial: casi siempre es un precio viejo."""
    costo = art.get("costo_kg")
    precio = art.get("precio_kg")
    return bool(costo and precio and precio < costo)


def bolsones_de(art: dict) -> float | None:
    """Los mismos kilos, contados como los cuenta el operario: en bolsones."""
    kg = art.get("stock")
    if kg is None:
        return None
    return round(float(kg) / KG_POR_BOLSON, 2)


def valor_inmovilizado(art: dict) -> float:
    """Kilos × costo por kilo. La plata que está quieta adentro de una cámara."""
    kg = float(art.get("stock") or 0)
    costo = float(art.get("costo_kg") or 0)
    return round(kg * costo, 2)


def enriquecer(art: dict) -> dict:
    """El lote con sus lecturas derivadas, para mostrar o para pasarle a Ángela."""
    return {
        **art,
        "unidad": UNIDAD,
        "label_precio": label_precio(art),
        "margen_pct": margen_pct(art),
        "bolsones": bolsones_de(art),
    }
