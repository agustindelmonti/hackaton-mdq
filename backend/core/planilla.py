"""
Fachada del libro oficial (remitos, claves namespaced) sobre el store.

El seed de `data-papasud/` es este libro. Si un data dir no tiene remitos ni
claves namespaced, las funciones devuelven vacío.
"""
from __future__ import annotations

from . import esquema, semilla, store


def activo() -> bool:
    """Hay un libro de remitos (el subtree nuevo), no sólo movimientos sueltos."""
    return bool(esquema.filas("remitos")) or any(
        ":" in str(a.get("lote") or "") for a in store.raw_actual()[:8]
    )


def remitos() -> list[dict]:
    return list(esquema.filas("remitos"))


def remito(rid: str) -> dict | None:
    rid = (rid or "").strip()
    for r in remitos():
        if r.get("id") == rid or str(r.get("numero")) == rid:
            return dict(r)
    return None


def lotes() -> list[dict]:
    return list(store.raw_actual())


def lote_por_clave(clave: str) -> dict | None:
    t = (clave or "").strip()
    if not t:
        return None
    for a in lotes():
        if a.get("lote_id") == t or a.get("lote") == t:
            return dict(a)
    return None


def buscar_por_nro(nro) -> list[dict]:
    """Todos los lotes con ese número corto. Nunca elige uno solo."""
    n = str(nro).strip()
    if not n:
        return []
    hits = []
    for a in lotes():
        if str(a.get("nro_lote") or "") == n:
            hits.append(dict(a))
            continue
        lid = str(a.get("lote_id") or a.get("lote") or "")
        partes = lid.split(":")
        if len(partes) >= 3 and partes[2] == n:
            hits.append(dict(a))
    return hits


def modelo() -> dict:
    """Catálogos que el front necesita para no hablar el dialecto sintético."""
    return {
        "activo": activo(),
        "ubicaciones": semilla.ubicaciones(),
        "chacras": semilla.chacras(),
        "variedades": semilla.variedades(),
        "calibres_comerciales": semilla.calibres_comerciales(),
        "envases": semilla.envases(),
        "transportes": semilla.transportes(),
        "clientes": semilla.clientes(),
        "kg_por_bolsa": (semilla.meta() or {}).get("kg_por_bolsa"),
    }
