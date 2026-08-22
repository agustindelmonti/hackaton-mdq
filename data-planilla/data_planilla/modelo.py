"""
Reglas de identidad y de relación — código plano, sin I/O.

El LLM no entra acá. Un lote mal claveado fusiona mercadería real; un remito
sin líneas pierde el DTV; un padre de categoría inferior viola INASE.
"""
from __future__ import annotations

import re

from . import dominio as D

TIPOS_MOVIMIENTO = (
    "ingreso",
    "traslado",
    "egreso",
    "descarte",
    "reproceso",
    "retorno",
)

_NRO_LOTE = re.compile(r"^(\d+)\s*([A-Za-z])?$")


def parsear_nro_lote(raw) -> tuple[str, str | None]:
    """'16 b' → ('16','b'); 37A → ('37','a'); 301 → ('301', None)."""
    if raw is None:
        raise ValueError("nro de lote vacío")
    if isinstance(raw, float) and raw == int(raw):
        raw = int(raw)
    s = str(raw).strip()
    m = _NRO_LOTE.match(s)
    if not m:
        raise ValueError(f"nro de lote ilegible: {raw!r}")
    nro, suf = m.group(1), m.group(2)
    return nro, (suf.lower() if suf else None)


def clave_lote(chacra_id: str, variedad_id: str, nro: str | int,
               sufijo: str | None = None) -> str:
    """Clave natural. El nro corto solo no identifica nada."""
    if not (chacra_id or "").strip():
        raise ValueError("hace falta chacra")
    if not (variedad_id or "").strip():
        raise ValueError("hace falta variedad")
    nro_s, suf_from_nro = parsear_nro_lote(nro)
    suf = (sufijo or suf_from_nro)
    partes = [chacra_id.strip(), variedad_id.strip(), nro_s]
    if suf:
        partes.append(suf.lower())
    return ":".join(partes)


def linaje_valido(padre_cat: str | None, hijo_cat: str) -> bool:
    """El padre tiene que ser igual o superior (índice menor o igual)."""
    if not padre_cat:
        return True
    if hijo_cat not in D.CAT_ORDEN or padre_cat not in D.CAT_ORDEN:
        return False
    return D.CAT_ORDEN.index(padre_cat) <= D.CAT_ORDEN.index(hijo_cat)


def validar_lote(lote: dict, padre: dict | None = None) -> dict:
    """Peaje antes de persistir. No asume, no completa."""
    chacra = lote.get("chacra_id") or ""
    if chacra == "trevelin":
        if not lote.get("color_bolsa") or not lote.get("color_hilo"):
            return {"ok": False, "motivo": "falta_codigo_visual"}
    if padre is not None:
        if not linaje_valido(padre.get("categoria_id"), lote.get("categoria_id") or ""):
            return {"ok": False, "motivo": "linaje_invalido"}
    elif lote.get("lote_padre_id") and padre is None:
        # el caller pasó el id pero no el padre: no adivinamos
        pass
    if lote.get("lote_padre_id") and padre is not None:
        if not linaje_valido(padre.get("categoria_id"), lote.get("categoria_id") or ""):
            return {"ok": False, "motivo": "linaje_invalido"}
    return {"ok": True}


def _slug_numero(numero) -> str:
    n = str(numero or "").strip().lower()
    if n in ("", "s/remito", "s-remito", "sremito", "s.remito"):
        return "s-remito"
    return n.replace("/", "-").replace(" ", "")


def armar_remito(numero, fecha: str, transporte_id: str | None,
                 dtv_e: str | None, origen_id: str | None,
                 lineas: list[dict], destino_id: str | None = None) -> dict:
    """Un viaje. El DTV y el transporte viven acá, no en cada lote."""
    if not lineas:
        raise ValueError("un remito sin líneas no es un remito")
    year = (fecha or "2026")[:4]
    slug = _slug_numero(numero)
    rid = f"R-{year}-{slug}"
    if slug == "s-remito":
        rid = f"R-{year}-s-remito-{fecha}"
    kg_total = 0.0
    bolsas_total = 0.0
    limpio = []
    for ln in lineas:
        if "dtv_e" in ln:
            ln = {k: v for k, v in ln.items() if k != "dtv_e"}
        kg_total += float(ln.get("kg") or 0)
        bolsas_total += float(ln.get("bolsas") or 0)
        limpio.append(dict(ln))
    return {
        "id": rid,
        "numero": str(numero),
        "fecha": fecha,
        "transporte_id": transporte_id,
        "dtv_e": dtv_e,
        "origen_id": origen_id,
        "destino_id": destino_id,
        "sin_numero": slug == "s-remito",
        "lineas": limpio,
        "kg_total": kg_total if kg_total != int(kg_total) else int(kg_total),
        "bolsas_total": bolsas_total if bolsas_total != int(bolsas_total) else int(bolsas_total),
    }


def armar_movimiento(tipo: str, lote_id: str, kg: float,
                     origen_id: str | None, destino_id: str | None = None,
                     remito_id: str | None = None,
                     transporte_id: str | None = None,
                     dtv_e: str | None = None,
                     ubicacion_carga_id: str | None = None,
                     cliente_id: str | None = None,
                     cliente_final_id: str | None = None,
                     calibre_comercial: str | None = None,
                     envase: str | None = None,
                     bolsas: int | float | None = None,
                     kg_promedio: float | None = None,
                     color_bolsa: str | None = None,
                     color_hilo: str | None = None,
                     nota: str | None = None) -> dict:
    if tipo not in TIPOS_MOVIMIENTO:
        raise ValueError(f"tipo desconocido: {tipo}")
    mov = {
        "tipo": tipo,
        "lote_id": lote_id,
        "kg": kg,
        "origen_id": origen_id,
        "destino_id": destino_id,
        "remito_id": remito_id,
        "transporte_id": transporte_id,
        "dtv_e": dtv_e,
        "ubicacion_carga_id": ubicacion_carga_id or origen_id,
        "cliente_id": cliente_id,
        "cliente_final_id": cliente_final_id,
        "calibre_comercial": calibre_comercial,
        "envase": envase,
        "bolsas": bolsas,
        "kg_promedio": kg_promedio,
        "color_bolsa": color_bolsa,
        "color_hilo": color_hilo,
        "bolsones": None,
    }
    if nota:
        mov["nota"] = nota
    return mov


def lotes_por_nro(lotes: list[dict], nro) -> list[dict]:
    """Todos los lotes con ese número corto. NUNCA desempata."""
    nro_s, _ = parsear_nro_lote(nro)
    return [l for l in lotes if str(l.get("nro") or "") == nro_s
            or (str(l.get("id") or "").split(":")[2:3] == [nro_s])]
