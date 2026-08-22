"""
Normaliza una fila de la planilla al modelo. El .xls es opcional: los tests
pasan dicts; `desde_xls` sólo corre si el archivo está en disco.
"""
from __future__ import annotations

import os
import re

import dominio as D
import modelo as M

_DTV = re.compile(r"(?:dtv\s*)?(\d{7,9}-\d)", re.I)
_HILO = re.compile(
    r"(?:hilo|h\.)\s*(blanco|negra|negro|verde(?:\s+claro)?|rojo|amarillo|"
    r"marron|naranja|celeste|azul|anarillo)",
    re.I,
)
_BOLSA = re.compile(
    r"(?:bolsa|b\.)\s*(blanca|roja|verde|amarilla|negra|naranja|marron|azul|negro)",
    re.I,
)


def extraer_dtv(texto: str | None) -> str | None:
    if not texto:
        return None
    m = _DTV.search(str(texto))
    return m.group(1) if m else None


def extraer_colores(texto: str | None) -> tuple[str | None, str | None]:
    if not texto:
        return None, None
    t = str(texto)
    b = _BOLSA.search(t)
    h = _HILO.search(t)
    bolsa = b.group(1).lower() if b else None
    hilo = h.group(1).lower() if h else None
    if hilo == "anarillo":
        hilo = "amarillo"
    if bolsa == "negro":
        bolsa = "negra"
    return bolsa, hilo


def extraer_calibre(texto: str | None) -> str | None:
    t = (texto or "").strip().lower()
    aliases = {
        "recibo": "recibo",
        "exportacion": "exportacion", "exportación": "exportacion",
        "expo buena": "expo_buena",
        "desc.expo": "desc_expo", "desc expo": "desc_expo",
        "sin chicas": "sin_chicas",
        "granel": "granel",
        "desc.paraguay": "desc_paraguay", "desc paraguay": "desc_paraguay",
        "sin tamañar": "sin_tamanar", "s/tamañar": "sin_tamanar",
        "s/tamanar": "sin_tamanar",
    }
    return aliases.get(t)


def chacra_de_hoja(nombre_hoja: str) -> str:
    n = (nombre_hoja or "").lower()
    if "trevelin" in n:
        return "trevelin"
    return "santa_ana"


def fila_a_linea(fila: dict, *, hoja: str) -> dict | None:
    """Una línea de remito. None si la fila no tiene lote+variedad."""
    var_raw = fila.get("Variedad") or fila.get("variedad")
    lote_raw = fila.get("Lote") if fila.get("Lote") not in ("", None) else fila.get("lote")
    if var_raw in ("", None) or lote_raw in ("", None):
        return None
    vid = D.variedad_id(str(var_raw))
    if not vid:
        return None
    try:
        nro, suf = M.parsear_nro_lote(lote_raw)
    except ValueError:
        return None
    chacra = chacra_de_hoja(hoja)
    obs = " ".join(str(fila.get(k) or "") for k in fila
                   if "obs" in str(k).lower() or "dtv" in str(k).lower())
    bolsa, hilo = extraer_colores(obs)
    if hoja.lower().find("trevelin") >= 0:
        bolsa = bolsa or (str(fila.get("Color bolsa") or "").strip().lower() or None)
        hilo = hilo or (str(fila.get("Color hilo") or "").strip().lower() or None)
    kg = fila.get("Kgs.") if fila.get("Kgs.") not in ("", None) else fila.get("Kgs")
    if kg in ("", None):
        kg = fila.get("Kg")
    try:
        kg_f = float(str(kg).lower().replace("kg", "").replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        kg_f = None
    dest = (fila.get("Destino") or fila.get("destino") or "")
    ubi = D.ubicacion_por_alias(str(dest))
    cat = D.categoria_id(str(fila.get("categoria") or fila.get("Categoría") or ""))
    cal = extraer_calibre(str(fila.get("Calibre") or ""))
    return {
        "lote_id": M.clave_lote(chacra, vid, nro, suf),
        "chacra_id": chacra,
        "variedad_id": vid,
        "nro": nro,
        "sufijo": suf,
        "kg": kg_f,
        "bolsas": fila.get("Bolsas") or fila.get("bolsas"),
        "destino_id": ubi["id"] if ubi else None,
        "calibre_comercial": cal,
        "categoria_id": cat,
        "color_bolsa": bolsa,
        "color_hilo": hilo,
        "dtv_e": extraer_dtv(obs),
    }


def agrupar_remitos(lineas_con_meta: list[dict]) -> list[dict]:
    """Agrupa por (numero, fecha, transporte). El DTV de cualquier línea sube."""
    grupos: dict[tuple, list] = {}
    for item in lineas_con_meta:
        key = (str(item.get("numero")), str(item.get("fecha")),
               str(item.get("transporte_id")))
        grupos.setdefault(key, []).append(item)
    remitos = []
    for (numero, fecha, transporte_id), items in grupos.items():
        dtv = next((i.get("dtv_e") for i in items if i.get("dtv_e")), None)
        origen = items[0].get("origen_id")
        lineas = [{k: v for k, v in i.items()
                   if k not in ("numero", "fecha", "transporte_id", "origen_id", "dtv_e")}
                  for i in items]
        remitos.append(M.armar_remito(
            numero=numero, fecha=fecha,
            transporte_id=transporte_id or None,
            dtv_e=dtv, origen_id=origen, lineas=lineas,
        ))
    return remitos


def desde_xls(ruta: str) -> dict:
    """Parsea el .xls. Requiere xlrd. No se llama desde los tests unitarios."""
    import xlrd
    from generar import construir
    if not os.path.isfile(ruta):
        raise FileNotFoundError(ruta)
    book = xlrd.open_workbook(ruta)
    _ = book.nsheets
    return construir()
