"""
Arma el dataset del libro real.

`construir()` no toca disco: lo usan los tests. `main()` escribe JSON en
`data-planilla/` para que el backend pueda apuntar POLPILOT_DATA_DIR acá
sin pisar `data-papasud/`.
"""
from __future__ import annotations

import json
import os

from . import dominio as D
from . import modelo as M

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(HERE, ".."))
CAMPANIA = "2025/26"
HOY = "2026-08-22"


def _lote(chacra_id: str, variedad_id: str, nro, *,
          categoria_id: str | None = None, sufijo: str | None = None,
          color_bolsa: str | None = None, color_hilo: str | None = None,
          lote_padre_id: str | None = None,
          calibre_comercial: str | None = None,
          ubicacion_id: str | None = None, stock: float = 0.0,
          camara: str | None = None) -> dict:
    nro_s, suf = M.parsear_nro_lote(nro)
    suf = sufijo or suf
    lid = M.clave_lote(chacra_id, variedad_id, nro_s, suf)
    var = D.VAR_POR_ID[variedad_id]
    cat = D.CAT_POR_ID.get(categoria_id) if categoria_id else None
    chacra = D.CHACRA_POR_ID[chacra_id]
    ubi = D.UBIC_POR_ID.get(ubicacion_id) if ubicacion_id else None
    lote = {
        "id": lid,
        "chacra_id": chacra_id,
        "variedad_id": variedad_id,
        "variedad": var["nombre"],
        "nro": nro_s,
        "sufijo": suf,
        "categoria_id": categoria_id,
        "categoria_semilla": cat["nombre"] if cat else None,
        "clase": cat["clase"] if cat else None,
        "color_bolsa": color_bolsa,
        "color_hilo": color_hilo,
        "lote_padre_id": lote_padre_id,
        "calibre_comercial": calibre_comercial,
        "campania": CAMPANIA,
        "campo_origen": chacra["nombre"],
        "zona_origen": chacra["zona"],
        "ubicacion_id": ubicacion_id,
        "ubicacion": ubi["nombre"] if ubi else None,
        "camara": camara,
        "stock": float(stock),
        "estado": "activo",
    }
    padre = None
    # validar contra el padre se hace al final, cuando el dict está completo
    r = M.validar_lote(lote, padre=padre)
    if not r["ok"] and r["motivo"] == "falta_codigo_visual":
        raise ValueError(f"{lid}: {r['motivo']}")
    return lote


def _art(lote: dict, codigo: int) -> dict:
    """Proyección al shape que ya come store.raw_actual(), sin perder la clave."""
    cat = lote.get("categoria_semilla") or "sin categoría"
    desc = (f"{lote['variedad'].upper()} · {cat} · "
            f"Lote {lote['nro']} · {lote['chacra_id']}")
    return {
        "codigo": codigo,
        "descripcion": desc,
        "estado": lote.get("estado") or "activo",
        "tipo": lote["variedad"],
        "proveedor": lote.get("campo_origen"),
        "um": "kg",
        "stock": lote.get("stock") or 0.0,
        "costo_neto": None,
        "costo_iva": None,
        "pvp": None,
        "lote": lote["id"],
        "lote_id": lote["id"],
        "lote_padre_id": lote.get("lote_padre_id"),
        "chacra_id": lote["chacra_id"],
        "nro_lote": lote["nro"],
        "sufijo": lote.get("sufijo"),
        "color_bolsa": lote.get("color_bolsa"),
        "color_hilo": lote.get("color_hilo"),
        "variedad": lote["variedad"],
        "variedad_id": lote["variedad_id"],
        "categoria_semilla": lote.get("categoria_semilla"),
        "categoria_id": lote.get("categoria_id"),
        "clase": lote.get("clase"),
        "campania": lote.get("campania"),
        "campo_origen": lote.get("campo_origen"),
        "zona_origen": lote.get("zona_origen"),
        "calibre_comercial": lote.get("calibre_comercial"),
        "ubicacion_id": lote.get("ubicacion_id"),
        "ubicacion": lote.get("ubicacion"),
        "camara": lote.get("camara"),
        "destino": "interno",
    }


def construir() -> dict:
    """El grafo mínimo que cubre cada relación de la planilla."""
    padre_spunta = _lote(
        "trevelin", "spunta", 3, categoria_id="inicial_1",
        color_bolsa="blanca", color_hilo="rojo",
        calibre_comercial="recibo",
        ubicacion_id="planta_santa_ana", stock=12397,
    )
    hijo_301 = _lote(
        "santa_ana", "spunta", 301, categoria_id="inicial_2",
        lote_padre_id=padre_spunta["id"],
        calibre_comercial="recibo",
        ubicacion_id="planta_santa_ana", stock=32760, camara=None,
    )
    assert M.linaje_valido(padre_spunta["categoria_id"], hijo_301["categoria_id"])

    lotes = [
        padre_spunta,
        hijo_301,
        _lote("santa_ana", "spunta", 50, calibre_comercial="granel",
              ubicacion_id="sasula", stock=18000),
        _lote("trevelin", "beo", 50, categoria_id="inicial_1",
              color_bolsa="amarilla", color_hilo="naranja",
              calibre_comercial="recibo",
              ubicacion_id="planta_santa_ana", stock=1264),
        _lote("trevelin", "spunta", 14, categoria_id="inicial_3",
              color_bolsa="blanca", color_hilo="verde",
              calibre_comercial="recibo",
              ubicacion_id="planta_santa_ana", stock=36000),
        _lote("santa_ana", "spunta", 300, calibre_comercial="sin_tamanar",
              ubicacion_id="galpon_mdp", stock=10200),
        _lote("santa_ana", "asterix", 811, calibre_comercial="sin_tamanar",
              ubicacion_id="galpon_mdp", stock=25000),
        _lote("santa_ana", "agata", 224, calibre_comercial="exportacion",
              ubicacion_id="pancani", stock=29120, camara="Cámara 1"),
        _lote("santa_ana", "spunta", 310, categoria_id="inicial_3",
              calibre_comercial="granel",
              ubicacion_id="campo_santa_ana", stock=33620),
        _lote("santa_ana", "spunta", 302, calibre_comercial="recibo",
              ubicacion_id="pancani", stock=31920, camara="Cámara 2"),
    ]

    trevelin_36 = [
        ("agata", 2, 5983, "naranja", "amarillo"),
        ("king_russet", 10, 3880, "amarilla", "marron"),
        ("ludmilla", 6, 1132, "amarilla", "rojo"),
        ("alverstone", 42, 2425, "naranja", "marron"),
        ("markies", 4, 1725, "amarilla", "blanco"),
        ("daifla", 5, 3072, "negra", "verde"),
        ("seven_four_7", 7, 754, "amarilla", "negro"),
        ("ikarus", 51, 2857, "negra", "celeste"),
        ("edison", 9, 1994, "blanca", "amarillo"),
        ("atlantic", 1, 53.9, "roja", "azul"),
    ]
    for vid, nro, kg, bolsa, hilo in trevelin_36:
        lotes.append(_lote(
            "trevelin", vid, nro, categoria_id="inicial_1",
            color_bolsa=bolsa, color_hilo=hilo, calibre_comercial="recibo",
            ubicacion_id="planta_santa_ana", stock=kg,
        ))

    por_id = {l["id"]: l for l in lotes}
    for l in lotes:
        if l.get("lote_padre_id"):
            r = M.validar_lote(l, padre=por_id[l["lote_padre_id"]])
            if not r["ok"]:
                raise ValueError(f"{l['id']}: {r['motivo']}")

    remito_1009 = M.armar_remito(
        numero="1009", fecha="2026-03-29",
        transporte_id="camillo_gaston", dtv_e="13534780-9",
        origen_id="campo_santa_ana",
        lineas=[
            {"lote_id": "santa_ana:spunta:300", "kg": 10200, "bolsas": 204,
             "destino_id": "galpon_mdp", "calibre_comercial": "sin_tamanar",
             "envase": "bolsa"},
            {"lote_id": "santa_ana:asterix:811", "kg": 25000, "bolsas": 500,
             "destino_id": "galpon_mdp", "calibre_comercial": "sin_tamanar",
             "envase": "bolsa"},
        ],
    )
    remito_36 = M.armar_remito(
        numero="36", fecha="2026-04-01",
        transporte_id="el_salvador", dtv_e=None,
        origen_id="campo_trevelin", destino_id="planta_santa_ana",
        lineas=[
            {"lote_id": padre_spunta["id"], "kg": 12397, "bolsas": 230,
             "destino_id": "planta_santa_ana", "calibre_comercial": "recibo",
             "envase": "bolsa", "color_bolsa": "blanca", "color_hilo": "rojo"},
        ] + [
            {"lote_id": M.clave_lote("trevelin", vid, nro), "kg": kg, "bolsas": 1,
             "destino_id": "planta_santa_ana", "calibre_comercial": "recibo",
             "envase": "bolsa", "color_bolsa": bolsa, "color_hilo": hilo}
            for vid, nro, kg, bolsa, hilo in trevelin_36
        ],
    )
    remito_910 = M.armar_remito(
        numero="910", fecha="2026-06-30",
        transporte_id="delcasagro", dtv_e=None,
        origen_id="planta_santa_ana",
        lineas=[{
            "lote_id": "santa_ana:spunta:301", "kg": 32760, "bolsas": 660,
            "destino_id": None, "calibre_comercial": "recibo", "envase": "bolsa",
            "kg_promedio": 49.63, "cliente_id": "delcaso",
            "cliente_final_id": "romero_m",
        }],
    )
    remito_retorno = M.armar_remito(
        numero="1139", fecha="2026-07-03",
        transporte_id="camillo_jaimez", dtv_e=None,
        origen_id="pancani", destino_id="planta_santa_ana",
        lineas=[{
            "lote_id": "santa_ana:spunta:302", "kg": 15200, "bolsas": 317,
            "destino_id": "planta_santa_ana", "calibre_comercial": "recibo",
            "envase": "bolsa", "nota": "a planta para trabajar",
        }],
    )
    remitos = [remito_1009, remito_36, remito_910, remito_retorno]

    def _mov(tipo, lote_id, kg, origen_id, destino_id=None, remito=None, **kw):
        m = M.armar_movimiento(
            tipo=tipo, lote_id=lote_id, kg=kg,
            origen_id=origen_id, destino_id=destino_id,
            remito_id=remito["id"] if remito else None,
            transporte_id=(remito or {}).get("transporte_id"),
            dtv_e=(remito or {}).get("dtv_e"),
            **kw,
        )
        m["fecha"] = (remito or {}).get("fecha") or HOY
        m["numero"] = f"MOV-2026-{len(movs)+1:04d}"
        m["estado"] = "confirmado"
        m["confirmado_en_destino"] = True
        m["canal"] = "planilla"
        lote = por_id[lote_id]
        m["codigo"] = None  # se completa al proyectar
        m["variedad"] = lote["variedad"]
        m["lote"] = lote_id
        m["origen"] = D.UBIC_POR_ID[origen_id]["nombre"] if origen_id else None
        m["destino"] = (D.UBIC_POR_ID[destino_id]["nombre"]
                        if destino_id and destino_id in D.UBIC_POR_ID else destino_id)
        return m

    movs = []
    movs.append(_mov("ingreso", padre_spunta["id"], 12397,
                     "campo_trevelin", "planta_santa_ana", remito_36,
                     envase="bolsa", bolsas=230, calibre_comercial="recibo"))
    movs.append(_mov("traslado", "santa_ana:spunta:300", 10200,
                     "campo_santa_ana", "galpon_mdp", remito_1009,
                     envase="bolsa", bolsas=204, calibre_comercial="sin_tamanar"))
    movs.append(_mov("traslado", "santa_ana:asterix:811", 25000,
                     "campo_santa_ana", "galpon_mdp", remito_1009,
                     envase="bolsa", bolsas=500, calibre_comercial="sin_tamanar"))
    movs.append(_mov("egreso", "santa_ana:spunta:301", 32760,
                     "planta_santa_ana", None, remito_910,
                     ubicacion_carga_id="planta_santa_ana",
                     cliente_id="delcaso", cliente_final_id="romero_m",
                     envase="bolsa", bolsas=660, kg_promedio=49.63,
                     calibre_comercial="recibo"))
    movs.append(_mov("reproceso", "santa_ana:spunta:302", 15200,
                     "pancani", "planta_santa_ana", remito_retorno,
                     envase="bolsa", bolsas=317, calibre_comercial="recibo",
                     nota="a planta para trabajar"))
    movs.append(_mov("retorno", "santa_ana:agata:224", 4543,
                     "pancani", "planta_santa_ana",
                     envase="bolsa", bolsas=88, calibre_comercial="exportacion",
                     nota="vuelve al galpón p/Brasil — reencaminado a planta"))

    arts = [_art(l, 26001 + i) for i, l in enumerate(lotes)]
    codigo_por_lote = {a["lote_id"]: a["codigo"] for a in arts}
    for m in movs:
        m["codigo"] = codigo_por_lote[m["lote_id"]]

    filas_dep = [{
        "codigo": a["codigo"],
        "producto": a["descripcion"],
        "lote": a["lote"],
        "variedad": a["variedad"],
        "categoria_semilla": a.get("categoria_semilla"),
        "campania": a.get("campania"),
        "ubicacion": a.get("ubicacion"),
        "ubicacion_id": a.get("ubicacion_id"),
        "camara": a.get("camara"),
        "cantidad": a.get("stock"),
        "calibre_comercial": a.get("calibre_comercial"),
        "color_bolsa": a.get("color_bolsa"),
        "color_hilo": a.get("color_hilo"),
    } for a in arts]

    catalogos = {
        "ubicaciones": D.UBICACIONES,
        "chacras": D.CHACRAS,
        "variedades": D.VARIEDADES,
        "categorias": D.CATEGORIAS,
        "calibres": {str(k): v for k, v in D.CALIBRES_INASE.items()},
        "calibres_comerciales": D.CALIBRES_COMERCIALES,
        "envases": D.ENVASES,
        "campos": D.CHACRAS,
        "clientes": D.CLIENTES,
        "transportes": D.TRANSPORTES,
        "meta": {
            "empresa": "Papasud S.A.",
            "hoy": HOY,
            "campania": CAMPANIA,
            "sintetico": False,
            "fuente": "Planilla de movimientos 2026.xls · modelo de linaje",
            "kg_por_bolsa": D.KG_POR_BOLSA,
        },
    }
    apartados = {
        "deposito": {"nombre": "Stock por ubicación", "filas": filas_dep},
        "movimientos": {"nombre": "Movimientos de stock", "filas": movs},
        "remitos": {"nombre": "Remitos", "filas": remitos},
        "transportes": {"nombre": "Transportes", "filas": list(D.TRANSPORTES)},
        "conteos": {"nombre": "Conteos físicos", "filas": []},
        "ordenes_carga": {"nombre": "Órdenes de carga", "filas": []},
    }
    return {
        "lotes": lotes,
        "remitos": remitos,
        "movimientos": movs,
        "inventory": {"articulos": arts},
        "apartados": apartados,
        "catalogos": catalogos,
        "notas_equipo": {"notas": []},
        "plantadas": {},
        "conocimiento_negocio": {"piezas": []},
    }


def escribir(data: dict | None = None) -> None:
    data = data or construir()
    os.makedirs(DATA_DIR, exist_ok=True)
    pares = [
        ("inventory.json", data["inventory"]),
        ("catalogos.json", data["catalogos"]),
        ("apartados.json", data["apartados"]),
        ("lotes.json", {"lotes": data["lotes"]}),
        ("remitos.json", {"remitos": data["remitos"]}),
        ("notas_equipo.json", data["notas_equipo"]),
        ("plantadas.json", data["plantadas"]),
        ("conocimiento_negocio.json", data["conocimiento_negocio"]),
    ]
    for nombre, payload in pares:
        ruta = os.path.join(DATA_DIR, nombre)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=1)
        print(f"  {nombre:<28} {os.path.getsize(ruta)/1024:>8.1f} KB")


def main() -> None:
    print("Generando data-planilla (libro real)\n")
    data = construir()
    escribir(data)
    print(f"""
  Lotes           {len(data['lotes'])}
  Remitos         {len(data['remitos'])}
  Movimientos     {len(data['movimientos'])}
  Variedades      {len(D.VARIEDADES)}
  Ubicaciones     {len(D.UBICACIONES)}
""".rstrip())


if __name__ == "__main__":
    main()
