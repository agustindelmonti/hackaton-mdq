"""
Los tests que defienden la consulta que abre la demo.

Ninguno hardcodea un número que la app calcula: verifican la RELACIÓN. Si
mañana se reimporta la planilla y un kilo cambia, la suite no se pone en rojo
por eso — se pone en rojo si el sistema empieza a mentir.

Lo que se protege, en orden de cuánto dolería que se rompa en la sala:
  1. que no cuente dos veces la misma papa
  2. que no ofrezca un lote que no sirve para ese pedido
  3. que todo número se pueda abrir hasta la fila del Excel
  4. que lo que vino a granel no se informe en bolsas
"""
from __future__ import annotations

import pytest

from core import comercial, consulta_nl, disponibilidad as disp, papasud_real as real

pytestmark = pytest.mark.skipif(
    not real.hay_datos_reales(),
    reason="la planilla real no está importada (python data-papasud/planilla_real.py)")


# --- el libro ---------------------------------------------------------------
def test_ninguna_partida_queda_en_negativo():
    """Stock negativo es un número que no existe. Lo que el libro no explica se
    declara como saldo anterior, no se deja en menos."""
    assert all(p["kg"] >= 0 for p in disp.libro()["partidas"])


def test_el_saldo_anterior_dice_por_que_existe():
    for s in disp.libro()["saldos_anteriores"]:
        assert s["motivo"] and s["kg"] > 0
        assert s["movimiento"], "un saldo anterior sin el movimiento que lo reveló"


def test_toda_partida_se_puede_abrir_hasta_el_excel():
    """«Cada número verificable» no es una consigna: es un assert."""
    for p in disp.libro()["partidas"]:
        if p["saldo_anterior"]:
            continue
        f = p.get("fuente") or {}
        assert f.get("solapa") and f.get("fila_excel"), p["id"]


def test_los_kilos_del_libro_son_los_de_la_planilla():
    """Lo que entró menos lo que salió tiene que cerrar contra los movimientos."""
    entradas = sum(m["kg"] for m in real.movimientos()
                   if m.get("kg") and real.es_nodo_de_stock(m.get("destino"))
                   and not m.get("reingresa"))
    en_stock = sum(p["kg"] for p in disp.libro()["partidas"])
    assert en_stock <= entradas, "hay más stock que kilos ingresados"


# --- la regla dura ----------------------------------------------------------
def test_un_lote_una_variedad_o_esta_marcado():
    """La regla que nos dictaron los dueños. Si un lote la rompe, tiene que
    estar en la lista de hallazgos — no puede pasar de largo."""
    por_lote: dict[str, set] = {}
    for m in real.movimientos():
        if m.get("lote") and m.get("variedad"):
            por_lote.setdefault(m["lote"], set()).add(m["variedad"])
    conflictivos = {l for l, vs in por_lote.items() if len(vs) > 1}
    marcados = {a["valor"] for a in real.anomalias() if a["id"] == "lote_multivariedad"}
    assert conflictivos, "la planilla real tiene lotes con más de una variedad"
    for lote in conflictivos:
        vs = por_lote[lote]
        assert vs & marcados, f"el lote {lote} rompe la regla y nadie lo marcó"


def test_los_hallazgos_traen_la_fila_del_excel():
    sin_fila = [a for a in real.anomalias()
                if a["id"] != "lote_sin_campo"
                and not (a.get("fuente") or {}).get("fila_excel")]
    assert not sin_fila, f"{len(sin_fila)} hallazgos sin fila del Excel"


def test_lo_que_la_planilla_explica_no_es_un_error():
    """El remito 829 declara 25 kg por bolsa y la observación dice «bolsa
    papasud x 25kg». Es otra bolsa, no un error de carga. Marcarlo pierde a la
    primera al que conoce la operación."""
    explicados = [m for m in real.movimientos() if m.get("kg_prom_explicado")]
    assert explicados, "nadie está leyendo las observaciones antes de marcar"
    for m in explicados:
        assert "kg_prom_imposible" not in (m.get("anomalias") or [])


# --- la consulta ------------------------------------------------------------
def test_lo_libre_nunca_supera_lo_que_hay():
    r = disp.consultar(variedad="spunta")
    assert r["libre"] <= r["hay"]
    assert r["libre"] == max(0, r["hay"] - r["comprometido"])


def test_el_granel_no_se_informa_en_bolsas():
    """Lo que llegó en tolva, suelto y con tierra, no está embolsado. Contarlo
    en bolsas es el error que un encargado ve en dos segundos."""
    for p in disp.libro()["partidas"]:
        if p.get("granel"):
            assert disp._bolsas_de(p) == 0


def test_las_bolsas_usan_el_promedio_real_del_lote():
    """Nunca un 50 fijo: el kilo por bolsa va de 46,66 a 54,59 y es del lote."""
    con_prom = [l for l in real.lotes() if l.get("kg_prom")]
    assert con_prom
    for l in con_prom[:20]:
        kb, fuente = disp.kg_por_bolsa(lote=l["id"])
        assert kb == l["kg_prom"]
        assert str(l["id"]) in fuente


def test_un_pedido_de_lote_no_carga_compromisos_ajenos():
    """Un pedido de king russet no compromete al lote 300 de spunta."""
    r = disp.consultar(lote="300")
    for p in r["pedidos_abiertos"]:
        assert "300" in (p.get("lotes") or [])


# --- el bloqueo con alternativa --------------------------------------------
def test_el_bloqueo_explica_y_propone():
    ev = disp.evaluar_pedido(variedad="asterix", cantidad=6000, unidad="kg",
                             calibre="exportacion", ubicacion="planta_mdp")
    assert ev["resultado"] == "bloqueado"
    assert ev["motivo"]["texto"]
    assert ev["alternativas"], "frenar sin proponer es una traba, no una ayuda"


def test_nunca_ofrece_un_calibre_que_no_sirve():
    """Mandar granel donde piden exportación es el contenedor que vuelve."""
    ev = disp.evaluar_pedido(variedad="asterix", cantidad=6000, unidad="kg",
                             calibre="exportacion", ubicacion="planta_mdp")
    for a in ev["alternativas"]:
        if not a["listo"]:
            continue                     # las que hay que clasificar se avisan
        for c in a["compatibilidad"]["calibres"]:
            assert disp._nivel(c) >= disp._nivel("exportacion"), c


def test_lo_sin_clasificar_no_se_ofrece_como_listo():
    ev = disp.evaluar_pedido(variedad="spunta", cantidad=500, unidad="bolsas",
                             calibre="exportacion")
    for a in ev["alternativas"]:
        if a["compatibilidad"].get("sin_clasificar_kg"):
            assert not a["listo"]
            assert a["preparacion"] == "clasificar"


def test_no_cuenta_dos_veces_la_misma_papa():
    """Sin ubicación pedida, el stock listo ya entró en la cuenta: ofrecerlo
    como alternativa sería sumar dos veces los mismos kilos."""
    ev = disp.evaluar_pedido(variedad="spunta", cantidad=500, unidad="bolsas",
                             calibre="exportacion")
    assert all(not a["listo"] for a in ev["alternativas"])


def test_traer_de_un_frigorifico_lleva_dias():
    ev = disp.evaluar_pedido(variedad="asterix", cantidad=6000, unidad="kg",
                             calibre="exportacion", ubicacion="planta_mdp")
    for a in ev["alternativas"]:
        if a["tipo"] == "frigorifico" and a["listo"]:
            assert a["dias"] >= 1 and "camión" in a["movimiento"]


def test_comprometer_pasa_por_la_misma_evaluacion(tmp_path, monkeypatch):
    """No hay puerta de atrás: si no se puede, no se compromete."""
    monkeypatch.setattr(disp, "PEDIDOS_JSON", str(tmp_path / "pedidos.json"))
    r = disp.comprometer(variedad="spunta", cantidad=50_000, unidad="kg",
                         calibre="exportacion", cliente="parmentier")
    assert r["ok"] is False
    assert r["evaluacion"]["resultado"] == "bloqueado"


# --- el lenguaje ------------------------------------------------------------
@pytest.mark.parametrize("texto,campo,valor", [
    ("¿tengo 1.200 bolsas de Spunta?", "cantidad", 1200),
    ("¿tengo 1.200 bolsas de Spunta?", "unidad", "bolsas"),
    ("¿cuánta agata me queda en el galpón?", "ubicacion", "galpon_mdp"),
    ("necesito 6.000 kilos de asterix para exportación", "calibre", "exportacion"),
    ("¿qué hay en dospanca?", "ubicacion", "dospanca"),
    ("tengo 3 toneladas de atlantic", "cantidad", 3000),
    ("que queda del lote 300", "lote", "300"),
])
def test_entiende_como_hablan(texto, campo, valor):
    assert consulta_nl.interpretar(texto)[campo] == valor


def test_no_desempata_solo():
    """Si la pregunta nombra dos variedades, se muestran las dos y elige una
    persona. Mover el lote equivocado son bolsones reales en una cámara real."""
    p = consulta_nl.interpretar("tengo spunta o agata en el galpon?")
    assert p["variedad"] is None
    assert set(p["ambiguo"]["variedad"]) == {"spunta", "agata"}


def test_avisa_cuando_el_lote_no_es_de_esa_variedad():
    lote = next(l for l in real.lotes() if l.get("variedad") == "agata")
    p = consulta_nl.interpretar(f"cuanta spunta hay en el lote {lote['id']}")
    if p["lote"]:
        assert "lote_variedad" in p["ambiguo"]


# --- lo comercial -----------------------------------------------------------
def test_el_camion_es_la_unidad_y_el_lote_el_detalle():
    """Un remito tiene varias filas: el remito 807 llevó lote 224 y lote 223."""
    todos = comercial.remitos(real.movimientos())
    multi = [r for r in todos if r["lotes"] > 1]
    assert multi, "la planilla real tiene remitos con más de un lote"
    for r in multi:
        assert r["kg"] == sum(l["kg"] for l in r["lineas"])


def test_el_total_de_un_cliente_es_la_suma_de_sus_camiones():
    c = comercial.clientes()[0]
    v = comercial.ventas(cliente=c["id"])
    assert v["kg"] == c["kg"]
    assert v["kg"] == sum(r["kg"] for r in v["camion_por_camion"])
    assert v["camiones"] == len(v["camion_por_camion"])


def test_los_kilos_por_transportista_salen_del_mismo_libro():
    """Un solo dato mirado de dos maneras: el stock y lo que hay que pagar."""
    total_libro = sum(m["kg"] for m in real.movimientos()
                      if m.get("kg") and m.get("transporte"))
    assert sum(t["kg"] for t in comercial.transportistas()) == total_libro
