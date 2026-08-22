from __future__ import annotations

import datetime
import json
import os
import statistics
from functools import lru_cache

from .audit import AuditLog
from .models import Articulo
from .versioning import VersionStore
from . import paths
from . import quality
from . import valorizacion

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = paths.DATA_DIR  # por-tenant: env POLPILOT_DATA_DIR o data/ (ver core/paths.py)
INVENTORY_JSON = os.path.join(DATA_DIR, "inventory.json")
# Copia viva sobre la que se aplican las correcciones (saneamiento).
# Arranca del inventory.json original y queda restaurable vía VersionStore.
WORKING_JSON = os.path.join(DATA_DIR, "inventory_actual.json")

versiones = VersionStore(DATA_DIR)
audit = AuditLog(DATA_DIR)


@lru_cache(maxsize=1)
def _cache_raw() -> tuple:
    """Lista cruda de artículos (dicts). Usa la copia de trabajo si existe."""
    fuente = WORKING_JSON if os.path.exists(WORKING_JSON) else INVENTORY_JSON
    with open(fuente, encoding="utf-8") as f:
        data = json.load(f)
    # tuple para que sea hasheable bajo lru_cache; se reconvierte a list al leer.
    return tuple(json.dumps(d) for d in data["articulos"])


def raw_actual() -> list[dict]:
    return [json.loads(s) for s in _cache_raw()]


def articulos() -> list[Articulo]:
    return [Articulo.from_dict(d) for d in raw_actual()]


_panorama_cache: dict | None = None


def guardar(raw: list[dict]) -> None:
    """Persiste la copia de trabajo y refresca los caches."""
    global _panorama_cache
    with open(WORKING_JSON, "w", encoding="utf-8") as f:
        json.dump({"articulos": raw}, f, ensure_ascii=False)
    _cache_raw.cache_clear()
    _panorama_cache = None
    from . import analisis_cache
    analisis_cache.datos_cambiaron()


def resetear_actual() -> None:
    """Descarta las correcciones y vuelve al inventory.json original."""
    global _panorama_cache
    if os.path.exists(WORKING_JSON):
        os.remove(WORKING_JSON)
    _cache_raw.cache_clear()
    _panorama_cache = None
    from . import analisis_cache
    analisis_cache.datos_cambiaron()


def libro_triado(lang: str | None = None) -> dict:
    return quality.libro_triado(articulos(), lang)


def reload() -> None:
    global _panorama_cache
    _cache_raw.cache_clear()
    _panorama_cache = None
    from . import analisis_cache
    analisis_cache.datos_cambiaron()
    _cache_raw()


# ---------------------------------------------------------------------------
# Panorama: el payload completo (resumen + alertas + top + grupos) recomputado
# desde la copia de trabajo. Es la fuente única que unifica el seam: cuando el
# saneamiento corrige algo, todo el sistema lo refleja (no sólo /api/calidad).
# ---------------------------------------------------------------------------

def _stat(grupo: list[dict]) -> dict:
    return {
        "cantidad": len(grupo),
        "impacto_pesos": round(sum(d.get("inmovilizado") or 0 for d in grupo), 2),
        "unidades": round(sum(d.get("stock") or 0 for d in grupo), 0),
    }


def _compute_panorama() -> dict:
    raw = raw_actual()
    grupos = {k: [] for k in ("fantasmas", "negativos", "sin_pvp", "calibre", "costo_viejo")}
    plural = {
        "fantasma": "fantasmas", "negativo": "negativos", "sin_precio": "sin_pvp",
        "calibre": "calibre", "costo_viejo": "costo_viejo",
    }
    for d in raw:
        for issue in quality.clasificar(Articulo.from_dict(d)):
            grupos[plural[issue.categoria.value]].append(d)

    activos = [d for d in raw if d.get("estado", "activo") != "anulado"]
    anulados = [d for d in raw if d.get("estado") == "anulado"]
    con_stock_pos = [d for d in raw if (d.get("stock") or 0) > 0]
    inmovilizado_total = round(sum(d.get("inmovilizado") or 0 for d in raw), 2)
    antig = [d["antiguedad_costo_dias"] for d in activos if d.get("antiguedad_costo_dias") is not None]

    # Orden de cada grupo (igual que data_store): por unidades o por plata.
    grupos["fantasmas"].sort(key=lambda d: d.get("stock") or 0, reverse=True)
    grupos["negativos"].sort(key=lambda d: d.get("stock") or 0)
    for k in ("sin_pvp", "calibre", "costo_viejo"):
        grupos[k].sort(key=lambda d: d.get("inmovilizado") or 0, reverse=True)

    # P38·A — "Datos a corregir" cuenta REGISTROS, no incidencias: un producto
    # con dos problemas es un producto a corregir, no dos. Este número es la
    # fuente única del badge del sidebar, del filtro de la tabla de stock y del
    # contador del Inicio — antes cada pantalla lo sumaba a mano y el costo
    # viejo quedaba afuera del badge pero adentro de la sección.
    a_corregir = len({d.get("codigo") for k in
                      ("fantasmas", "negativos", "sin_pvp", "calibre", "costo_viejo")
                      for d in grupos[k]})

    problemas = sum(len(grupos[k]) for k in ("fantasmas", "negativos", "sin_pvp", "calibre"))
    if problemas > 300:
        salud = {"nivel": "requiere_accion", "label": "Requiere acción urgente"}
    elif problemas > 100:
        salud = {"nivel": "atencion", "label": "Atención requerida"}
    else:
        salud = {"nivel": "en_orden", "label": "En orden"}

    top = sorted(con_stock_pos, key=lambda d: d.get("inmovilizado") or 0, reverse=True)[:25]
    negativos_stat = _stat(grupos["negativos"])

    return {
        "meta": {
            "empresa": paths.EMPRESA,   # por tenant: piloto o demo (ver core/paths.py)
            "fuente": paths.FUENTE,
            "generado": datetime.datetime.now().isoformat(timespec="seconds"),
            "total_articulos": len(raw),
        },
        "resumen": {
            "inmovilizado_total": inmovilizado_total,
            "total_articulos": len(raw),
            "activos": len(activos),
            "anulados": len(anulados),
            "con_costo": len([d for d in activos if d.get("costo_iva")]),
            "stock_positivo": len(con_stock_pos),
            "stock_cero": len([d for d in raw if (d.get("stock") or 0) == 0]),
            "stock_negativo": len(grupos["negativos"]),
            "unidades_stock_positivo": round(sum(d.get("stock") or 0 for d in con_stock_pos), 0),
            "antiguedad_mediana_costo_dias": round(statistics.median(antig), 0) if antig else None,
            "a_corregir": a_corregir,
            "salud": salud,
        },
        "alertas": {
            "fantasmas": _stat(grupos["fantasmas"]),
            "negativos": negativos_stat,
            "sin_pvp": _stat(grupos["sin_pvp"]),
            "calibre": _stat(grupos["calibre"]),
            "costo_viejo": _stat(grupos["costo_viejo"]),
        },
        "top_inmovilizado": top,
        "grupos": grupos,
        "articulos": raw,
    }


def panorama() -> dict:
    """Payload completo recomputado desde la copia de trabajo (cacheado)."""
    global _panorama_cache
    if _panorama_cache is None:
        _panorama_cache = _compute_panorama()
    return _panorama_cache


# Prioridad para elegir el "estado de calidad" principal de un artículo (peor primero).
_ESTADO_PRIORIDAD = ["negativo", "fantasma", "calibre", "sin_precio", "costo_viejo"]


def articulos_con_estado() -> list[dict]:
    """Todos los artículos con su estado de calidad principal, para la tabla
    'ver todo' del inventario. estado_calidad ∈ {ok, fantasma, negativo,
    sin_precio, calibre, costo_viejo}."""
    out = []
    for d in raw_actual():
        cats = {i.categoria.value for i in quality.clasificar(Articulo.from_dict(d))}
        estado_cal = next((c for c in _ESTADO_PRIORIDAD if c in cats), "ok")
        out.append({
            "codigo": d.get("codigo"),
            "descripcion": d.get("descripcion"),
            "estado": d.get("estado", "activo"),
            "stock": d.get("stock") or 0,
            "costo_iva": d.get("costo_iva"),
            "pvp": d.get("pvp"),
            "inmovilizado": d.get("inmovilizado") or 0,
            "estado_calidad": estado_cal,
            # En semilla todo se mide en kilos; el operario además cuenta bolsones.
            "unidad_pricing": valorizacion.unidad(d),
            "label_precio": valorizacion.label_precio(d),
            "margen_pct": valorizacion.margen_pct(d),
            "bolsones": valorizacion.bolsones_de(d),
        })
    return out


