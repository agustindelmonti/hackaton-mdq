"""
Esquema adaptativo — el grafo de relaciones del negocio.

Cuando llega un tipo de dato que el sistema nunca tuvo, Ángela: (1) identifica
el tipo por sus columnas, (2) detecta cómo se relaciona con lo que ya existe,
(3) crea el apartado y las relaciones. Un dato nuevo no vive solo: se conecta.

Acá vive el conocimiento del rubro: qué tipos hay, qué columnas los identifican,
con qué se relacionan y qué se ACTIVA cuando se conectan.
"""
from __future__ import annotations

import json
import os
import unicodedata

from . import paths
from . import store

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = paths.DATA_DIR  # por-tenant: env POLPILOT_DATA_DIR o data/ (ver core/paths.py)
APARTADOS_JSON = os.path.join(DATA_DIR, "apartados.json")

# El grafo: cada tipo, sus señales de columna, con qué se relaciona y qué activa.
TIPOS = {
    "producto": {
        "nombre": "Lotes de semilla",
        "senales": ["lote", "variedad", "categoria", "campania", "calibre", "kilos",
                    "stock", "semilla", "bolsones"],
        "relaciona_con": [],
        "activa": [],
    },
    # LA VISTA ÚNICA (N02): dónde está cada lote, en qué cámara y cuántos kilos
    # dice la planilla que hay. Es el apartado que unifica las cuatro ubicaciones.
    "deposito": {
        "nombre": "Stock por ubicación",
        "senales": ["ubicacion", "camara", "frigorifico", "galpon", "lote",
                    "bolsones", "kilos", "fisico"],
        "relaciona_con": ["producto"],
        "activa": ["vista única del stock en las cuatro ubicaciones",
                   "alertas de brotación próxima por lote",
                   "diferencias entre lo declarado y lo contado"],
    },
    # N01: cada movimiento es una transacción, no una fila de planilla.
    "movimientos": {
        "nombre": "Movimientos de stock",
        "senales": ["movimiento", "traslado", "origen", "destino", "egreso",
                    "ingreso", "salida", "entrada", "bolsones"],
        "relaciona_con": ["producto", "deposito"],
        "activa": ["registro por voz o texto con validación de disponibilidad",
                   "traslados sin confirmar en destino",
                   "trazabilidad de lote punta a punta"],
    },
    # La otra fuente de verdad: lo que alguien contó parado adentro de la cámara.
    "conteos": {
        "nombre": "Conteos físicos",
        "senales": ["conteo", "contado", "recuento", "inventario fisico",
                    "diferencia", "declarado"],
        "relaciona_con": ["producto", "deposito", "movimientos"],
        "activa": ["conciliación entre lo declarado y lo contado",
                   "hipótesis sobre la causa de cada diferencia"],
    },
    # Lo que se le prometió a un cliente. Compromete stock antes de moverlo.
    "ordenes_carga": {
        "nombre": "Órdenes de carga",
        "senales": ["orden de carga", "remito", "despacho", "cliente", "embarque",
                    "contenedor", "incoterm"],
        "relaciona_con": ["producto", "deposito", "movimientos"],
        "activa": ["bloqueo de emisión sin stock real verificado",
                   "documentación de exportación pre-completada por lote"],
    },
    # Compras de insumo (bolsones, tratamientos, servicios de frío).
    "ordenes_compra": {
        "nombre": "Órdenes de compra",
        "senales": ["orden de compra", "nota de pedido", "oc "],
        "relaciona_con": ["proveedor", "producto"],
        "activa": ["control remito ↔ orden de compra al recibir insumos"],
    },
    "recepciones": {
        "nombre": "Recepciones",
        "senales": ["recepcion", "remito", "recibido", "ingreso deposito"],
        "relaciona_con": ["proveedor", "producto", "ordenes_compra"],
        "activa": ["ingreso de cosecha y de insumos con control contra lo pedido"],
    },
    "compras": {
        "nombre": "Compras",
        "senales": ["factura", "cuit", "iva", "neto gravado", "comprobante compra"],
        "relaciona_con": ["proveedor", "recepciones"],
        "activa": ["cuenta corriente del proveedor (cuánto le debés y cuándo vence)"],
    },
    "logistica": {
        "nombre": "Despachos",
        "senales": ["entrega", "envio", "despacho", "destino", "transporte",
                    "camion", "chofer", "fecha prevista", "remito", "puerto"],
        "relaciona_con": ["cliente", "ordenes_carga"],
        "activa": ["estado de cada despacho", "alertas de embarque atrasado"],
    },
    # Libro real (data-planilla): el remito es el viaje, las filas son líneas.
    "remitos": {
        "nombre": "Remitos",
        "senales": ["remito", "dtv", "lineas", "bolsas", "kg.prom"],
        "relaciona_con": ["producto", "movimientos", "transportes"],
        "activa": ["un viaje con varios lotes", "DTV colgado del documento"],
    },
    "transportes": {
        "nombre": "Transportes",
        "senales": ["transporte", "chofer", "camion", "fletero"],
        "relaciona_con": ["remitos", "movimientos"],
        "activa": ["empresa y chofer de cada viaje"],
    },
}

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def detectar_tipo(headers: list[str]) -> dict:
    """Identifica el tipo de dato por sus columnas. Devuelve {tipo, confianza, ambiguo}."""
    h = " ".join(_norm(x) for x in headers)
    puntajes = {}
    for tipo, d in TIPOS.items():
        puntajes[tipo] = sum(1 for s in d["senales"] if s in h)
    mejor = max(puntajes, key=puntajes.get)
    top = puntajes[mejor]
    segundo = sorted(puntajes.values(), reverse=True)[1] if len(puntajes) > 1 else 0
    return {
        "tipo": mejor if top > 0 else "producto",
        "confianza": top,
        "ambiguo": top > 0 and top == segundo,
    }


# --- Apartados activos (qué secciones de datos existen en el tenant) ---

def _load() -> dict:
    try:
        return json.load(open(APARTADOS_JSON, encoding="utf-8"))
    except Exception:
        return {}


def _save(d: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    json.dump(d, open(APARTADOS_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    # P11·B4: cualquier escritura de apartados (recepciones, compras, ventas,
    # staging integrado) invalida los análisis cacheados.
    from . import analisis_cache
    analisis_cache.datos_cambiaron()


def apartados_activos() -> list[str]:
    """Qué tipos de dato ya existen. 'producto' siempre (es el inventario base)."""
    return sorted({"producto", *_load().keys()})


def existe(tipo: str) -> bool:
    return tipo in apartados_activos()


def filas(tipo: str) -> list[dict]:
    """Las filas guardadas de un apartado (lista vacía si no existe)."""
    d = _load().get(tipo)
    return list(d.get("filas", [])) if d else []


def plan_integracion(tipo: str, lang: str | None = None) -> dict:
    """Qué va a pasar al integrar este tipo: apartado nuevo + relaciones + qué se activa.
    `lang` traduce lo VISIBLE (nombre, lista de qué activa); el tipo y las
    relaciones son IDs y no cambian. ES byte-igual a TIPOS (la fuente histórica)."""
    import i18n
    tkey = tipo if tipo in TIPOS else "producto"
    d = TIPOS[tkey]
    activos = apartados_activos()
    relaciones = [r for r in d["relaciona_con"] if r in activos]
    activa = ([i18n.t(f"core.esquema.activa_{tkey}_{i}", lang)
               for i in range(len(d["activa"]))]
              if relaciones or not d["relaciona_con"] else [])
    return {
        "tipo": tipo,
        "nombre": i18n.t(f"core.esquema.{tkey}", lang),
        "apartado_nuevo": tipo not in activos,
        "relaciona_con": relaciones,
        "activa": activa,
    }


def reemplazar_filas(tipo: str, filas: list[dict]) -> dict:
    """Pisa las filas de un apartado (no mergea). La usan los módulos que EDITAN
    una fila existente — confirmar un movimiento en destino, cerrar una orden de
    carga — donde agregar una copia sería exactamente el error de versión que
    este sistema vino a matar."""
    data = _load()
    data[tipo] = {"nombre": data.get(tipo, {}).get("nombre")
                  or TIPOS.get(tipo, {}).get("nombre", tipo), "filas": list(filas)}
    _save(data)
    return {"tipo": tipo, "total": len(filas)}


def crear_apartado(tipo: str, filas: list[dict]) -> dict:
    """Crea (o mergea) el apartado y guarda sus filas. El sistema se expande solo."""
    data = _load()
    previas = data.get(tipo, {}).get("filas", [])
    data[tipo] = {"nombre": TIPOS.get(tipo, {}).get("nombre", tipo), "filas": previas + filas}
    _save(data)
    return {"tipo": tipo, "total": len(data[tipo]["filas"]), "nuevas": len(filas)}


def validar_referencias_producto(filas: list[dict]) -> dict:
    """Integridad referencial: cada fila debe referenciar un producto que exista
    (por código o por nombre). Las huérfanas se marcan (no se integran ciegas).
    Aplica a ventas, depósito y cualquier tipo que se relacione con producto."""
    codigos = {d.get("codigo") for d in store.raw_actual()}
    nombres = {_norm(d.get("descripcion")) for d in store.raw_actual()}
    huerfanas = []
    for i, f in enumerate(filas):
        cod = f.get("codigo")
        nom = _norm(f.get("producto") or f.get("descripcion"))
        if cod is not None and cod in codigos:
            continue
        if nom and nom in nombres:
            continue
        huerfanas.append(i)
    return {"huerfanas": huerfanas, "ok": len(filas) - len(huerfanas)}


# Nombre histórico (los primeros llamadores eran sólo de ventas).
validar_integridad_ventas = validar_referencias_producto
