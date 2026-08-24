"""
semilla.py · El catálogo del rubro — la base que comparten los demás módulos.

Lee `catalogos.json` del data dir: las cuatro ubicaciones con su capacidad y su
temperatura objetivo, las variedades, las categorías INASE con su costo por kilo
y su tolerancia sanitaria, los calibres por grado en milímetros, los campos de
producción, los clientes (internos y de exportación con sus requisitos de
destino) y los documentos que exige cada organismo.

No calcula nada del negocio: es el diccionario. Quién lo usa decide qué hacer.
"""
from __future__ import annotations

import json
import os

from . import paths

CATALOGOS_JSON = os.path.join(paths.DATA_DIR, "catalogos.json")

_cache: dict | None = None


def _cargar() -> dict:
    global _cache
    if _cache is None:
        try:
            with open(CATALOGOS_JSON, encoding="utf-8") as f:
                _cache = json.load(f)
        except (OSError, ValueError):
            _cache = {}
    return _cache


def recargar() -> None:
    """Invalida la cache. La usan los tests y la carga de datos nueva."""
    global _cache
    _cache = None


def hay_datos() -> bool:
    return bool(_cargar().get("ubicaciones"))


# --- Ubicaciones -----------------------------------------------------------
def ubicaciones() -> list[dict]:
    # El seed (arriba) + lo que se creó/editó/eliminó en runtime (ver
    # core/ubicaciones.py — CRUD de N02). El seed nunca se reescribe: es un
    # archivo versionado, no estado; el merge vive en un solo lugar para que
    # el resto del backend (mapa, conciliación, depósito, NL de movimientos)
    # siga leyendo por acá sin saber que la capa de overrides existe.
    from . import ubicaciones as _ubicaciones_overrides
    return _ubicaciones_overrides.aplicar(list(_cargar().get("ubicaciones") or []))


def ubicacion(uid: str) -> dict | None:
    return next((u for u in ubicaciones() if u["id"] == uid), None)


def ubicacion_por_nombre(nombre: str) -> dict | None:
    n = (nombre or "").strip().lower()
    return next((u for u in ubicaciones() if u["nombre"].lower() == n), None)


def capacidad_total_kg() -> float:
    return float(sum(u.get("capacidad_kg") or 0 for u in ubicaciones()))


# --- Variedades, categorías, calibres --------------------------------------
def variedades() -> list[dict]:
    return list(_cargar().get("variedades") or [])


def categorias() -> list[dict]:
    return list(_cargar().get("categorias") or [])


def categoria(cid: str) -> dict | None:
    return next((c for c in categorias() if c["id"] == cid), None)


def calibres() -> dict:
    """{grado(int): {min_mm, max_mm, label}} — Res. INASE 171/2000, art. 25."""
    return {int(k): v for k, v in (_cargar().get("calibres") or {}).items()}


def rango_calibre(grado: int) -> dict | None:
    return calibres().get(int(grado))


# --- Campos y clientes -----------------------------------------------------
def campos() -> list[dict]:
    return list(_cargar().get("campos") or [])


def clientes() -> list[dict]:
    return list(_cargar().get("clientes") or [])


def cliente(cid: str) -> dict | None:
    return next((c for c in clientes() if c["id"] == cid), None)


def buscar_cliente(texto: str) -> dict | None:
    """Por id o por nombre parcial — así lo nombra una persona, no un sistema."""
    t = (texto or "").strip().lower()
    if not t:
        return None
    exacto = cliente(t)
    if exacto:
        return exacto
    return next((c for c in clientes() if t in c["nombre"].lower()), None)


def clientes_exportacion() -> list[dict]:
    return [c for c in clientes() if c.get("tipo") == "exportacion"]


# --- Documentación de exportación ------------------------------------------
def documentos_exportacion() -> list[dict]:
    return list(_cargar().get("docs_exportacion") or [])


def documento_exportacion(did: str) -> dict | None:
    return next((d for d in documentos_exportacion() if d["id"] == did), None)


# --- Meta ------------------------------------------------------------------
def meta() -> dict:
    return dict(_cargar().get("meta") or {})


def calibres_comerciales() -> list[dict]:
    return list(_cargar().get("calibres_comerciales") or [])


def envases() -> list[dict]:
    return list(_cargar().get("envases") or [])


def chacras() -> list[dict]:
    return list(_cargar().get("chacras") or _cargar().get("campos") or [])


def transportes() -> list[dict]:
    return list(_cargar().get("transportes") or [])
