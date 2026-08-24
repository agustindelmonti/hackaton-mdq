"""
Arma el dataset oficial de Papasud — el libro de la planilla.

`construir()` no toca disco: lo usan los tests. `main()` escribe JSON en
`data-papasud/` (este directorio). Es el seed por defecto del backend.
"""
from __future__ import annotations

import json
import os

import dominio as D
import modelo as M

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = HERE
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
    cat_row = D.CAT_POR_ID.get(lote.get("categoria_id") or "")
    costo = (cat_row or {}).get("costo_kg")
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
        "costo_neto": round(costo / 1.105, 2) if costo else None,
        "costo_iva": costo,
        "pvp": round(costo * 1.55, 2) if costo else None,
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
        "destino": ("exportacion" if lote.get("calibre_comercial") == "exportacion"
                    else "interno"),
        "analisis_fecha": "2026-04-10",
        "analisis_estado": "aprobado",
        "analisis_metodo": D.METODO_ANALISIS,
        "analisis_laboratorio": D.LABORATORIO,
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
        _lote("santa_ana", "spunta", 305, calibre_comercial="recibo",
              ubicacion_id="pancani", stock=8400, camara="Cámara 1"),
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
        "docs_exportacion": D.DOCS_EXPORTACION,
        "meta": {
            "empresa": "Papasud S.A.",
            "hoy": HOY,
            "campania": CAMPANIA,
            "sintetico": False,
            "fuente": "Planilla de movimientos 2026.xls · modelo de linaje",
            "kg_por_bolsa": D.KG_POR_BOLSA,
            "posicion_arancelaria": D.POSICION_ARANCELARIA,
        },
    }
    data = {
        "lotes": lotes,
        "remitos": remitos,
        "movimientos": movs,
        "inventory": {"articulos": arts},
        "catalogos": catalogos,
        "filas_dep": filas_dep,
    }
    plantadas, conteos, ordenes, notas, conocimiento = plantar_demo(data)
    apartados = {
        "deposito": {"nombre": "Stock por ubicación", "filas": filas_dep},
        "movimientos": {"nombre": "Movimientos de stock", "filas": movs},
        "remitos": {"nombre": "Remitos", "filas": remitos},
        "transportes": {"nombre": "Transportes", "filas": list(D.TRANSPORTES)},
        "conteos": {"nombre": "Conteos físicos", "filas": conteos},
        "ordenes_carga": {"nombre": "Órdenes de carga", "filas": ordenes},
    }
    return {
        "lotes": lotes,
        "remitos": remitos,
        "movimientos": movs,
        "inventory": {"articulos": arts},
        "apartados": apartados,
        "catalogos": catalogos,
        "notas_equipo": {"notas": notas},
        "plantadas": plantadas,
        "conocimiento_negocio": {"piezas": conocimiento},
    }


def plantar_demo(data: dict) -> tuple[dict, list, list, list, list]:
    """Los tres beats de la demo, sobre sitios reales."""
    lotes = {l["id"]: l for l in data["lotes"]}
    arts = {a["lote_id"]: a for a in data["inventory"]["articulos"]}
    movs = data["movimientos"]

    def _codigo(lid):
        return arts[lid]["codigo"]

    lote_aire = lotes["santa_ana:spunta:302"]
    mov_sin = {
        "numero": "MOV-2026-0912",
        "fecha": "2026-08-12",
        "tipo": "traslado",
        "lote_id": lote_aire["id"],
        "lote": lote_aire["id"],
        "codigo": _codigo(lote_aire["id"]),
        "variedad": lote_aire["variedad"],
        "kg": 18_000.0,
        "bolsas": 360,
        "origen_id": "pancani",
        "destino_id": "galpon_mdp",
        "origen": D.ubicacion_nombre("pancani"),
        "destino": D.ubicacion_nombre("galpon_mdp"),
        "registrado_por": "marcos",
        "estado": "en_transito",
        "confirmado_en_destino": False,
        "canal": "voz",
        "nota": "Salió de Pancani hacia el galpón. Nadie confirmó la llegada.",
    }
    movs.append(mov_sin)

    lote_merma = lotes["santa_ana:agata:224"]
    merma = {
        "lote": lote_merma["id"],
        "codigo": _codigo(lote_merma["id"]),
        "variedad": lote_merma["variedad"],
        "ubicacion_id": "pancani",
        "camara": "Cámara 1",
        "kg": 3_100.0,
        "motivo": "brotación",
    }

    linaje = {
        "hijo_id": "santa_ana:spunta:999",
        "hijo_categoria": "inicial_1",
        "padre_id": "santa_ana:spunta:310",
        "padre_categoria": "inicial_3",
        "motivo": "linaje_invalido",
    }

    lote_x = lotes["santa_ana:spunta:50"]
    conteos = [
        {
            "numero": "CNT-2026-001",
            "fecha": "2026-08-18",
            "codigo": merma["codigo"],
            "lote": merma["lote"],
            "producto": arts[lote_merma["id"]]["descripcion"],
            "ubicacion": D.ubicacion_nombre("pancani"),
            "ubicacion_id": "pancani",
            "camara": "Cámara 1",
            "declarado_kg": float(lote_merma["stock"]),
            "fisico_kg": float(lote_merma["stock"]) - merma["kg"],
            "diferencia_kg": -merma["kg"],
            "contado_por": "marcos",
            "metodo": "bolsas",
            "nota": "Bolsones del fondo con brotación avanzada",
        },
        {
            "numero": "CNT-2026-002",
            "fecha": "2026-08-19",
            "codigo": _codigo(lote_aire["id"]),
            "lote": lote_aire["id"],
            "producto": arts[lote_aire["id"]]["descripcion"],
            "ubicacion": D.ubicacion_nombre("pancani"),
            "ubicacion_id": "pancani",
            "camara": lote_aire.get("camara"),
            "declarado_kg": float(lote_aire["stock"]),
            "fisico_kg": float(lote_aire["stock"]) - mov_sin["kg"],
            "diferencia_kg": -mov_sin["kg"],
            "contado_por": "marcos",
            "metodo": "bolsas",
            "nota": "Contado bolsa por bolsa, dos veces",
        },
        {
            "numero": "CNT-2026-003",
            "fecha": "2026-08-20",
            "codigo": _codigo(lote_x["id"]),
            "lote": lote_x["id"],
            "producto": arts[lote_x["id"]]["descripcion"],
            "ubicacion": D.ubicacion_nombre("sasula"),
            "ubicacion_id": "sasula",
            "camara": None,
            "declarado_kg": float(lote_x["stock"]),
            "fisico_kg": float(lote_x["stock"]) - 2_400,
            "diferencia_kg": -2_400.0,
            "contado_por": "nestor",
            "metodo": "bolsas",
        },
    ]

    cli = D.CLI_POR_ID["lamb_weston"]
    item = {
        "codigo": _codigo(lote_aire["id"]),
        "lote": lote_aire["id"],
        "producto": arts[lote_aire["id"]]["descripcion"],
        "variedad": lote_aire["variedad"],
        "categoria_semilla": lote_aire.get("categoria_semilla"),
        "kg": 24_000.0,
        "bolsas": 480,
        "ubicacion": D.ubicacion_nombre("pancani"),
        "camara": lote_aire.get("camara"),
    }
    ordenes = [{
        "numero": "OC-2026-2461",
        "fecha": "2026-08-21",
        "cliente_id": "lamb_weston",
        "cliente": cli["nombre"],
        "tipo": "exportacion",
        "pais": cli.get("pais"),
        "estado": "pendiente",
        "items": [item],
        "kg_total": 24_000.0,
        "ubicacion_carga": D.ubicacion_nombre("pancani"),
        "incoterm": cli.get("incoterm"),
        "moneda": cli.get("moneda"),
        "puerto": cli.get("puerto"),
        "destino_puerto": cli.get("destino_puerto"),
        "nota": "Pide 24 t de un lote cuyos 18 t están en el aire entre Pancani y el galpón.",
    }]

    plantadas = {
        "movimiento_sin_confirmar": mov_sin,
        "merma_no_registrada": merma,
        "linaje_invalido": linaje,
    }
    notas = [
        {"id": "NOTA-001", "fecha": "2026-08-16", "autor": "marcos",
         "rol": "operario", "canal": "voz", "tipo": "observacion",
         "texto": "El martes cargué Spunta en Pancani para el galpón. No sé si alguien lo descargó.",
         "texto_en": "On Tuesday I loaded Spunta at Pancani for the shed. I don't know if anyone unloaded it."},
        {"id": "NOTA-002", "fecha": "2026-08-18", "autor": "dalia",
         "rol": "agrónoma", "canal": "texto", "tipo": "observacion",
         "texto": f"El lote de {merma['variedad']} de la Cámara 1 de Pancani está brotando antes de tiempo.",
         "texto_en": f"The {merma['variedad']} lot in Pancani Cámara 1 is sprouting ahead of schedule."},
    ]
    conocimiento = [
        {"id": "K-001", "nodo": "deposito", "efecto": "suprime_alerta",
         "titulo": "Una bolsa nunca pesa 50 justo",
         "texto": "Diferencias de menos del 0,5% en un conteo de bolsas son de tara, no de faltante.",
         "texto_en": "Differences under 0.5% in a bag count are tare, not shrinkage.",
         "params": {"umbral_pct": 0.5}, "autor": "ruben",
         "fecha": "2026-03-12", "activa": True},
        {"id": "K-003", "nodo": "despachos", "efecto": "requiere_aprobacion",
         "titulo": "Exportación no sale sin análisis vigente",
         "texto": "Ninguna carga de exportación se emite si el análisis sanitario tiene más de 180 días.",
         "texto_en": "No export load goes out if the sanitary analysis is older than 180 days.",
         "params": {"dias_analisis": 180}, "autor": "dalia",
         "fecha": "2026-02-04", "activa": True},
    ]
    return plantadas, conteos, ordenes, notas, conocimiento


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
    print("Generando data-papasud (libro oficial de la planilla)\n")
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
