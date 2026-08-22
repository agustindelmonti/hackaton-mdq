"""
papasud_real.py · La puerta de entrada a los datos reales de Papasud.

Lee lo que dejó el importador en `data-papasud/real/` — el contrato que está
escrito en `docs/CONTRATO_DATOS.md`. Un solo lugar carga los archivos y los
cachea; todo lo demás del sistema pide por acá.

Que sea UN solo lugar importa: cuando el importador de Agustín reemplace al
provisional, este módulo es el único que se entera.

NO HAY NÚMEROS ACÁ. Este módulo no calcula: carga. El stock se deriva en
`disponibilidad.py` a partir del libro de movimientos, nunca se lee de un campo.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from .paths import DATA_DIR

REAL_DIR = os.path.join(DATA_DIR, "real")

_ARCHIVOS = ("movimientos", "lotes", "ubicaciones", "anomalias",
             "muestras", "campos", "meta")


def hay_datos_reales() -> bool:
    """¿Está la planilla importada? Si no, el sistema sigue con el dataset
    anterior en vez de romperse: la demo no puede depender de un archivo."""
    return os.path.isfile(os.path.join(REAL_DIR, "movimientos.json"))


@lru_cache(maxsize=None)
def _cargar(nombre: str):
    ruta = os.path.join(REAL_DIR, f"{nombre}.json")
    if not os.path.isfile(ruta):
        return {} if nombre == "meta" else []
    with open(ruta, encoding="utf-8") as fh:
        return json.load(fh)


def refrescar() -> None:
    """Después de reimportar la planilla. También lo usan los tests."""
    _cargar.cache_clear()
    for f in (movimientos, lotes, ubicaciones, anomalias, muestras, campos,
              meta, lote_por_id, ubicacion_por_id, muestra_de_variedad):
        f.cache_clear()


@lru_cache(maxsize=1)
def movimientos() -> list[dict]:
    """El libro. Ordenado por fecha: el orden importa para consumir partidas."""
    ms = list(_cargar("movimientos"))
    ms.sort(key=lambda m: (m.get("fecha") or "0000-00-00", m["id"]))
    return ms


@lru_cache(maxsize=1)
def lotes() -> list[dict]:
    return list(_cargar("lotes"))


@lru_cache(maxsize=1)
def ubicaciones() -> list[dict]:
    return list(_cargar("ubicaciones"))


@lru_cache(maxsize=1)
def anomalias() -> list[dict]:
    return list(_cargar("anomalias"))


@lru_cache(maxsize=1)
def muestras() -> list[dict]:
    return list(_cargar("muestras"))


@lru_cache(maxsize=1)
def campos() -> list[dict]:
    return list(_cargar("campos"))


@lru_cache(maxsize=1)
def meta() -> dict:
    return dict(_cargar("meta"))


@lru_cache(maxsize=1)
def lote_por_id() -> dict[str, dict]:
    return {l["id"]: l for l in lotes()}


@lru_cache(maxsize=1)
def ubicacion_por_id() -> dict[str, dict]:
    return {u["id"]: u for u in ubicaciones()}


@lru_cache(maxsize=1)
def muestra_de_variedad() -> dict[str, dict]:
    return {m["variedad"]: m for m in muestras() if m.get("variedad")}


# --- Nombres para la pantalla ---------------------------------------------
# Ellos escriben 'dospanca' y 'wemar-mc cain' en minúscula. En la pantalla van
# con mayúscula, pero el id sigue siendo el de la planilla: si alguien busca el
# dato original, lo encuentra escrito igual.
def nombre_ubicacion(uid: str | None) -> str:
    if not uid:
        return "sin declarar"
    u = ubicacion_por_id().get(uid)
    if u:
        return u["nombre"]
    return uid.replace("_", " ").title()


def nombre_nodo(nodo: dict | None) -> str:
    if not nodo:
        return "sin declarar"
    if nodo["tipo"] == "lote":
        return f"lote {nodo['id']}"
    if nodo["tipo"] == "cliente":
        return nodo["id"].title()
    if nodo["tipo"] == "campo":
        for c in campos():
            if c["id"] == nodo["id"]:
                return c["nombre"]
        return nodo["id"].replace("_", " ").title()
    return nombre_ubicacion(nodo["id"])


ES_STOCK = ("planta", "galpon", "frigorifico")


def es_nodo_de_stock(nodo: dict | None) -> bool:
    """¿Este nodo guarda mercadería? Un lote de campo y un cliente, no."""
    return bool(nodo) and nodo.get("tipo") in ES_STOCK
