"""
modelo_real.py · Carga el modelo REAL de Papasud (Track B — feat/modelo-real).

Este módulo es la fundación de la que dependen los otros dos tracks (consultas
y Ángela / mapa y móvil): expone el catálogo real, los lotes, el libro de
movimientos append-only y la vista de stock derivada.

No toca ni reemplaza el `core.store` viejo (el de "4 depósitos" / Articulo):
convive aparte, bajo el namespace `/api/papasud/...` en main.py, para no
romper lo que Track A y Track C ya construyeron contra el modelo anterior.

REGLA DURA DEL DOMINIO: cada lote tiene UNA sola variedad. Nunca dos
variedades en un mismo lote. Se verifica al cargar (`validar_regla_linaje`).
"""
from __future__ import annotations

import json
import os

from . import paths

_CACHE: dict | None = None


def _leer(nombre: str) -> dict:
    ruta = os.path.join(paths.DATA_DIR, nombre)
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _cargar() -> dict:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    lotes = _leer("lotes_real.json")["lotes"]
    movimientos = _leer("movimientos_real.json")["movimientos"]
    catalogos = _leer("catalogos_real.json")
    bloqueo_demo = _leer("bloqueo_alternativa_real.json")
    plantadas = _leer("plantadas_real.json")

    validar_regla_linaje(lotes)

    _CACHE = {
        "lotes": lotes,
        "lotes_por_id": {l["id"]: l for l in lotes},
        "movimientos": movimientos,
        "catalogos": catalogos,
        "bloqueo_demo": bloqueo_demo,
        "plantadas": plantadas,
    }
    return _CACHE


def reload() -> None:
    """Fuerza a releer los JSON del disco (después de un importer, por ejemplo)."""
    global _CACHE
    _CACHE = None
    _cargar()


def validar_regla_linaje(lotes: list[dict]) -> None:
    """Cada lote (código INASE) tiene UNA sola variedad. Si el mismo código de
    lote aparece dos veces con variedades distintas, el dato está corrompido
    — textual de Papasud: 'el lote 300 son peras, el 101 son manzanas'."""
    variedad_por_lote: dict[str, str] = {}
    for l in lotes:
        prev = variedad_por_lote.get(l["id"])
        if prev is not None and prev != l["variedad_id"]:
            raise ValueError(
                f"Regla de linaje violada: el lote {l['id']} tiene tanto "
                f"'{prev}' como '{l['variedad_id']}'. Un lote es una sola variedad."
            )
        variedad_por_lote[l["id"]] = l["variedad_id"]


# ----------------------------------------------------------------------------
# Accesores públicos
# ----------------------------------------------------------------------------
def lotes() -> list[dict]:
    return _cargar()["lotes"]


def lote(lote_id: str) -> dict | None:
    return _cargar()["lotes_por_id"].get(lote_id)


def movimientos() -> list[dict]:
    return _cargar()["movimientos"]


def catalogos() -> dict:
    return _cargar()["catalogos"]


def bloqueo_demo() -> dict:
    return _cargar()["bloqueo_demo"]


def plantadas() -> dict:
    return _cargar()["plantadas"]


def nombre_ubicacion(ubicacion_id: str) -> str:
    """'campo:santa_ana' -> 'Santa Ana' · 'planta_mdp' -> 'Planta Mar del Plata'
    · 'frigorifico:dospanca' -> 'Dospanca' · 'cliente:parmentier' -> 'Parmentier'"""
    cat = catalogos()
    if ubicacion_id.startswith("campo:"):
        cid = ubicacion_id.split(":", 1)[1]
        return next((c["nombre"] for c in cat["campos"] if c["id"] == cid), cid)
    if ubicacion_id.startswith("frigorifico:"):
        fid = ubicacion_id.split(":", 1)[1]
        return next((f["nombre"] for f in cat["frigorificos"] if f["id"] == fid), fid)
    if ubicacion_id.startswith("cliente:"):
        cid = ubicacion_id.split(":", 1)[1]
        return next((c["nombre"] for c in cat["clientes"] if c["id"] == cid), cid)
    if ubicacion_id == cat["planta"]["id"]:
        return cat["planta"]["nombre"]
    return ubicacion_id
