"""
ubicaciones.py · CRUD de las ubicaciones del mapa de operación (N02).

Las ubicaciones nacieron como una constante fija (los cuatro sitios de
Papasud), sembradas una vez en catalogos.json — un archivo que SE VERSIONA
(ver .gitignore: es el seed reproducible del demo, no estado de runtime).
Por eso las mutaciones de este módulo NO tocan catalogos.json: viven en un
JSON propio y gitignoreado (ubicaciones_overrides.json, mismo directorio de
datos por-tenant), igual que organizacion.json/perfiles.json. semilla.py
mergea seed + overrides en `ubicaciones()`, así que todo el resto del
backend (mapa.py, conciliacion.py, deposito.py, movimientos_nl.py, los
endpoints de main.py) sigue leyendo por ese único punto sin saber que existe
esta capa — ninguno de esos módulos cambia.

Quién puede llamar esto lo decide el endpoint (Depends(require_feature(...))
en main.py) o la tool del agente (TOOL_FEATURE en angela.py); este módulo no
conoce roles.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata

from . import paths, semilla

OVERRIDES_JSON = os.path.join(paths.DATA_DIR, "ubicaciones_overrides.json")

# Catálogo cerrado a propósito: cada tipo nuevo necesita su ícono en el
# frontend (Ubicaciones.jsx, MapaOperacion.jsx) antes de tener sentido acá.
TIPOS_VALIDOS = {"frigorifico", "galpon", "campo", "laboratorio", "planta", "otro"}

CAMPOS_EDITABLES = {
    "nombre", "tipo", "camaras", "capacidad_kg",
    "temp_objetivo", "temp_tolerancia", "direccion",
}


def _slug(nombre: str) -> str:
    s = unicodedata.normalize("NFKD", nombre or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s or "ubicacion"


def _id_libre(nombre: str, existentes: set[str]) -> str:
    base = _slug(nombre)
    if base not in existentes:
        return base
    i = 2
    while f"{base}_{i}" in existentes:
        i += 1
    return f"{base}_{i}"


def _overrides() -> dict:
    try:
        with open(OVERRIDES_JSON, encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        d = {}
    d.setdefault("creadas", {})
    d.setdefault("editadas", {})
    d.setdefault("eliminadas", [])
    return d


def _guardar_overrides(d: dict) -> None:
    os.makedirs(os.path.dirname(OVERRIDES_JSON), exist_ok=True)
    with open(OVERRIDES_JSON, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def aplicar(base: list[dict]) -> list[dict]:
    """El seed + lo creado − lo eliminado, con las ediciones encima. La llama
    ÚNICAMENTE semilla.ubicaciones() — acá vive la lógica de merge para que
    esa función siga siendo, como dice su docstring, sólo el diccionario."""
    ov = _overrides()
    eliminadas = set(ov["eliminadas"])
    out = {u["id"]: dict(u) for u in base if u["id"] not in eliminadas}
    for uid, u in ov["creadas"].items():
        if uid not in eliminadas:
            out[uid] = dict(u)
    for uid, cambios in ov["editadas"].items():
        if uid in out:
            out[uid].update(cambios)
    return list(out.values())


def _audit(actor: str, accion: str, antes=None, despues=None) -> None:
    from . import store  # perezoso: store importa medio mundo (mismo patrón que perfiles.py)
    store.audit.record(actor=actor, accion=accion, antes=antes, despues=despues)


def _tiene_stock(uid: str) -> bool:
    from . import store
    return any(float(a.get("stock") or 0) > 0
               for a in store.raw_actual() if a.get("ubicacion_id") == uid)


def resolver(texto: str) -> list[dict]:
    """Candidatos que matchean `texto` contra id o nombre — fuzzy simple y
    determinístico, sin IA: el modelo NUNCA elige la ubicación por su cuenta
    (regla de arquitectura #3, la misma que rige la resolución de lotes en
    movimientos_nl.py). Esto arma la lista ranqueada; quien confirma es la
    persona, por chat o por la UI.

    Exacto (id o nombre completo, sin distinguir mayúsculas) devuelve un único
    candidato. Si no hay exacto, substring sobre el nombre o el id."""
    t = (texto or "").strip().lower()
    if not t:
        return []
    todas = semilla.ubicaciones()
    exacto = next((u for u in todas if u["id"] == t or u["nombre"].lower() == t), None)
    if exacto:
        return [exacto]
    return [u for u in todas if t in u["nombre"].lower() or t in u["id"]]


def crear(nombre: str, tipo: str, *, capacidad_kg: float | None = None,
         temp_objetivo: float | None = None, temp_tolerancia: float | None = None,
         direccion: str | None = None, camaras: list[str] | None = None,
         actor: str) -> dict:
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre no puede estar vacío.")
    if tipo not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido: {tipo!r} (válidos: {', '.join(sorted(TIPOS_VALIDOS))})")
    existentes = {u["id"] for u in semilla.ubicaciones()}
    uid = _id_libre(nombre, existentes)
    u = {
        "id": uid, "nombre": nombre, "tipo": tipo,
        "camaras": list(camaras or []),
        "capacidad_kg": capacidad_kg,
        "temp_objetivo": temp_objetivo,
        "temp_tolerancia": temp_tolerancia,
        "direccion": (direccion or "").strip() or None,
    }
    ov = _overrides()
    ov["creadas"][uid] = u
    _guardar_overrides(ov)
    _audit(actor, "crear_ubicacion", despues=u)
    return u


def editar(uid: str, cambios: dict, *, actor: str) -> dict:
    actual = semilla.ubicacion(uid)
    if not actual:
        raise KeyError(f"ubicación inexistente: {uid}")
    extra = set(cambios) - CAMPOS_EDITABLES
    if extra:
        raise ValueError(f"Campos no editables: {', '.join(sorted(extra))}")
    if "tipo" in cambios and cambios["tipo"] not in TIPOS_VALIDOS:
        raise ValueError(f"Tipo inválido: {cambios['tipo']!r}")
    if "nombre" in cambios and not str(cambios["nombre"] or "").strip():
        raise ValueError("El nombre no puede estar vacío.")
    ov = _overrides()
    if uid in ov["creadas"]:
        # Nacida en esta misma capa de overrides: se edita in-place, no hace
        # falta un segundo registro de "editada" sobre algo que no es seed.
        ov["creadas"][uid].update(cambios)
    else:
        ov["editadas"].setdefault(uid, {}).update(cambios)
    _guardar_overrides(ov)
    despues = dict(actual, **cambios)
    _audit(actor, "editar_ubicacion", antes=actual, despues=despues)
    return despues


def eliminar(uid: str, *, actor: str) -> dict:
    actual = semilla.ubicacion(uid)
    if not actual:
        raise KeyError(f"ubicación inexistente: {uid}")
    if _tiene_stock(uid):
        raise ValueError(
            "No se puede eliminar: todavía tiene stock. Trasladá o descargá el "
            "saldo antes de borrar la ubicación.")
    ov = _overrides()
    if uid in ov["creadas"]:
        del ov["creadas"][uid]  # nunca existió en el seed: no hace falta marcarla eliminada
    else:
        ov["editadas"].pop(uid, None)
        if uid not in ov["eliminadas"]:
            ov["eliminadas"].append(uid)
    _guardar_overrides(ov)
    _audit(actor, "eliminar_ubicacion", antes=actual)
    return {"ok": True, "id": uid}
