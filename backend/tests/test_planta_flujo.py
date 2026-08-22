"""
test_planta_flujo.py · La planta como hub y las entidades del medio.

Sale de la charla del 22/08 con Papasud: la mercadería se hace en el campo,
entra a planta (báscula + planilla de recepción), se reclasifica, y de ahí
va a cliente o a frío. El frío suele volver a planta. Un lote, una variedad.
El lote 300 vive en Cayetano Chávez.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import modelo_real as M
from core import stock_real as S
from core import mapa_real as MAPA
from core import mapa as MAPA_OP


@pytest.fixture(autouse=True)
def _reload():
    M.reload()
    yield


def test_lote_300_esta_en_cayetano_chavez():
    l = M.lote("300")
    assert l is not None
    assert l["campo_id"] == "san_cayetano"
    assert l["campo"] == "Cayetano Chávez"


def test_un_lote_una_variedad_en_el_mismo_campo():
    """'El lote 300 son peras, el 101 son manzanas' — varios lotes por campo,
    nunca dos variedades en el mismo lote."""
    por_campo: dict[str, list] = {}
    for l in M.lotes():
        por_campo.setdefault(l["campo_id"], []).append(l)
    assert "san_cayetano" in por_campo
    assert len(por_campo["santa_ana"]) > 1
    for lote in M.lotes():
        assert isinstance(lote["variedad_id"], str)
        assert lote["variedad_id"]


def test_catalogo_tiene_planta_con_tres_zonas_y_laboratorio():
    cat = M.catalogos()
    planta = cat["planta"]
    zonas = planta["zonas"]
    ids = {z["id"] for z in zonas}
    assert ids == {"recepcion", "reclasificacion", "playa"}
    assert planta["tiene_bascula"] is True
    assert cat["laboratorio"]["id"] == "lab_invitro"
    assert any(c["id"] == "san_cayetano" for c in cat["campos"])
    assert any(v["id"] == "tolva" for v in cat["tipos_vehiculo"])
    assert cat["sistema_contable"]["id"] == "albor_agro"
    assert cat["sistema_contable"]["rol"] == "no_reemplazar"


def test_cada_ingreso_tolva_tiene_orden_de_carga_y_recepcion():
    ingresos = [m for m in M.movimientos() if m["tipo"] == "ingreso_tolva"]
    assert ingresos
    ocs = {o["id"]: o for o in M.ordenes_carga()}
    recs = {r["id"]: r for r in M.recepciones()}
    for m in ingresos:
        assert m["tipo_vehiculo"] == "tolva"
        assert m["zona_planta"] == "recepcion"
        assert m["destino_id"] == M.catalogos()["planta"]["id"]
        assert m["origen_id"].startswith("campo:")
        assert m.get("peso_bascula_kg")
        oc = ocs[m["orden_carga_id"]]
        rec = recs[m["recepcion_id"]]
        assert oc["canal"] == "papel"
        assert oc["kg_estimado_pendiente_pesaje"] is True
        assert rec["zona_id"] == "recepcion"
        assert rec["peso_bascula_kg"] == pytest.approx(m["peso_bascula_kg"])


def test_reclasificacion_no_mueve_stock_vive_en_planta():
    """Granel → bolsas es una estación, no un depósito. El stock sigue en
    planta_mdp; si la reclasificación restara kilos, el ledger no cerraría."""
    rcls = M.reclasificaciones()
    assert rcls
    planta_id = M.catalogos()["planta"]["id"]
    for r in rcls:
        assert r["zona_id"] == "reclasificacion"
        assert r["kg_embolsado"] == pytest.approx(r["kg_granel"])
        # no existe un movimiento cuyo tipo sea reclasificacion
    assert all(m["tipo"] != "reclasificacion" for m in M.movimientos())
    # hay stock vivo en planta (el remanente que no se vendió todavía)
    kg_planta = sum(f["kg"] for f in S.stock_por_ubicacion()
                    if f["ubicacion_id"] == planta_id)
    assert kg_planta > 0


def test_existen_los_tres_caminos_que_ellos_describieron():
    tipos = {m["tipo"] for m in M.movimientos()}
    assert "ingreso_tolva" in tipos
    assert "envio_frio" in tipos
    assert "retiro_frio" in tipos
    assert "entrega_cliente" in tipos
    assert "campo_a_frio" in tipos
    # atajo campo → cliente
    assert any(m["tipo"] == "entrega_cliente" and m["origen_id"].startswith("campo:")
               for m in M.movimientos())
    # el circuito más común: algo vuelve de frío a planta
    planta_id = M.catalogos()["planta"]["id"]
    assert any(m["tipo"] == "retiro_frio" and m["destino_id"] == planta_id
               for m in M.movimientos())
    # la venta sale sobre todo de la planta, no del frío
    entregas = [m for m in M.movimientos() if m["tipo"] == "entrega_cliente"]
    desde_planta = sum(1 for m in entregas if m["origen_id"] == planta_id)
    assert desde_planta >= len(entregas) / 3


def test_mapa_operacion_conserva_cuatro_sitios_ordenes_clientes_y_suma_planta():
    """El mapa de la operación no tira las 4 cámaras, las órdenes ni los
    clientes: les suma la planta y el galpón nuevo."""
    d = MAPA_OP.mapa()
    assert d.get("modelo") != "real"
    tipos = {n["tipo"] for n in d["nodos"]}
    assert "ubicacion" in tipos
    assert "orden" in tipos
    assert "cliente" in tipos
    assert "planta" in tipos
    assert "galpon" in tipos
    nombres = {n["etiqueta"] for n in d["nodos"]}
    assert "Frigorífico Sierra de los Padres" in nombres
    assert "Frigorífico Ruta 226" in nombres
    assert "Frigorífico Batán" in nombres
    assert "Galpón Chapadmalal" in nombres
    assert "Planta Mar del Plata" in nombres
    assert "Galpón Mar del Plata" in nombres
    # Chapadmalal no se duplica como galpón nuevo
    galpones = [n for n in d["nodos"] if n["tipo"] == "galpon"]
    assert len(galpones) == 1
    assert galpones[0]["etiqueta"] == "Galpón Mar del Plata"
    planta = next(n for n in d["nodos"] if n["tipo"] == "planta")
    assert {z["id"] for z in planta["zonas"]} == {"recepcion", "reclasificacion", "playa"}
    assert any(n["tipo"] == "orden" for n in d["nodos"])
    assert any(n["tipo"] == "cliente" for n in d["nodos"])


def test_mapa_papasud_sigue_siendo_el_flujo_campo_planta():
    """`/api/papasud/mapa` no se toca: sigue siendo el grafo real."""
    d = MAPA.flujo()
    assert d["modelo"] == "real"
    planta = next(n for n in d["nodos"] if n["tipo"] == "planta")
    assert planta["etiqueta"] == "Planta Mar del Plata"
    assert planta["capa"] == "hub"
    assert {z["id"] for z in planta["zonas"]} == {"recepcion", "reclasificacion", "playa"}
    assert not any(n["tipo"] == "ubicacion" for n in d["nodos"])
    capas = {c["id"] for c in d["capas"]}
    assert capas == {"origen", "hub", "almacenamiento", "destino"}
    tipos = {n["tipo"] for n in d["nodos"]}
    assert "planta" in tipos
    assert "campo" in tipos
    assert "frigorifico" in tipos
    assert "laboratorio" in tipos
    assert "cliente" in tipos
    campos = [n for n in d["nodos"] if n["tipo"] == "campo"]
    assert len(campos) == 5
    assert any(n["etiqueta"] == "Cayetano Chávez" for n in campos)
    assert d["filas"]
    assert d["resumen"]["kg_en_planta"] > 0
    assert d["resumen"]["recepciones"] == len(M.recepciones())


def test_mapa_no_tiene_nodos_huerfanos_salvo_la_marca():
    d = MAPA.flujo()
    conectados = set()
    for a in d["aristas"]:
        conectados.add(a["origen"])
        conectados.add(a["destino"])
    sueltos = [n["id"] for n in d["nodos"]
               if n["id"] not in conectados and n["tipo"] not in ("marca",)]
    # el laboratorio puede quedar sin arista si ningún lote de un campo
    # declara origen_laboratorio — lo aceptamos sólo a él.
    sueltos = [s for s in sueltos if not s.startswith("lab")]
    assert not sueltos, f"nodos sin arista: {sueltos}"


def test_aristas_de_tolva_van_de_campo_a_planta():
    d = MAPA.flujo()
    planta = next(n["id"] for n in d["nodos"] if n["tipo"] == "planta")
    campos = {n["id"] for n in d["nodos"] if n["tipo"] == "campo"}
    tolvas = [a for a in d["aristas"] if a["tipo"] == "ingreso_tolva"]
    assert tolvas
    for a in tolvas:
        assert a["origen"] in campos
        assert a["destino"] == planta
        assert a["vehiculo"] == "tolva"
        assert a["kg"] > 0


def test_detalle_planta_expone_zonas_y_numeros_del_libro():
    d = S.detalle_planta()
    assert d["kg"] > 0
    assert len(d["zonas"]) == 3
    rec = next(z for z in d["zonas"] if z["id"] == "recepcion")
    assert rec["recepciones"] == len(M.recepciones())
    assert rec["kg_ingresados"] > 0
    rcl = next(z for z in d["zonas"] if z["id"] == "reclasificacion")
    assert rcl["reclasificaciones"] == len(M.reclasificaciones())
    playa = next(z for z in d["zonas"] if z["id"] == "playa")
    assert playa["kg_envio_frio"] > 0
    assert d["flujos"]["ingreso_tolva_kg"] == rec["kg_ingresados"]


def test_resumen_sitios_separa_planta_de_frigorificos():
    r = S.resumen_sitios()
    assert r["planta"] is not None
    assert r["planta"]["tipo"] == "planta"
    assert r["frigorificos"]
    assert all(f["tipo"] == "frigorifico" for f in r["frigorificos"])
    assert r["kg_total"] == pytest.approx(
        r["planta"]["kg"] + sum(f["kg"] for f in r["frigorificos"]))
