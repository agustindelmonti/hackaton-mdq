"""
test_modelo_real.py · Track B (feat/modelo-real) — el modelo real de Papasud.

Cubre: la regla dura de linaje (un lote, una variedad), que el stock es una
vista derivada correcta del libro de movimientos, el motor de
bloqueo-con-alternativa, el detector de inconsistencias sobre las cinco
plantadas, la liquidación a transportistas/frigoríficos, y el importador
tolerante contra una planilla sintética con las columnas reales documentadas.
"""
from __future__ import annotations

import io
import os
import sys

import openpyxl
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import modelo_real as M           # noqa: E402
from core import stock_real as S             # noqa: E402
from core import inconsistencias_papasud as I  # noqa: E402
from core import liquidacion as L            # noqa: E402
from core import importer_papasud as IMP     # noqa: E402


@pytest.fixture(autouse=True)
def _reload_modelo():
    M.reload()
    yield


# ----------------------------------------------------------------------------
# Regla dura de linaje
# ----------------------------------------------------------------------------
def test_cada_lote_tiene_una_sola_variedad():
    variedad_por_lote: dict[str, set] = {}
    for l in M.lotes():
        variedad_por_lote.setdefault(l["id"], set()).add(l["variedad_id"])
    multivariedad = {k: v for k, v in variedad_por_lote.items() if len(v) > 1}
    assert not multivariedad, f"lotes con más de una variedad: {multivariedad}"


def test_validar_regla_linaje_rechaza_lote_con_dos_variedades():
    lotes_corrompidos = [
        {"id": "300", "variedad_id": "agata"},
        {"id": "300", "variedad_id": "spunta"},
    ]
    with pytest.raises(ValueError):
        M.validar_regla_linaje(lotes_corrompidos)


def test_codigos_de_lote_son_los_reales_provistos_por_papasud():
    ids = {l["id"] for l in M.lotes()}
    for esperado in ("14", "18", "222", "223", "224", "241", "300", "810", "811", "910"):
        assert esperado in ids
    assert "L30" in ids and "L79" in ids


# ----------------------------------------------------------------------------
# Stock como vista derivada
# ----------------------------------------------------------------------------
def test_stock_nunca_negativo_en_ubicaciones_de_inventario():
    saldo = S.stock_por_lote_ubicacion()
    negativos = [(k, v) for k, v in saldo.items() if v < -1.0 and not k[1].startswith("campo:")]
    # Una de las cinco inconsistencias plantadas ROMPE el cierre en un
    # frigorífico a propósito: eso es justo lo que el detector de abajo
    # tiene que encontrar, así que lo aceptamos acá y lo verificamos aparte.
    assert len(negativos) <= 1, negativos


def test_disponibilidad_por_variedad_solo_devuelve_esa_variedad():
    filas = S.disponibilidad_por_variedad("spunta")
    assert filas
    assert all(f["variedad_id"] == "spunta" for f in filas)


# ----------------------------------------------------------------------------
# Bloqueo con alternativa
# ----------------------------------------------------------------------------
def test_bloqueo_con_alternativa_del_dataset_plantado():
    caso = M.bloqueo_demo()
    r = S.verificar_pedido(caso["variedad_id"], caso["kg_pedido"],
                           caso["lote_pedido_id"], caso["ubicacion_pedido_id"])
    assert r["bloqueado"] is True
    assert r["alternativas"], "el bloqueo tiene que traer al menos una alternativa"
    # nunca sugiere el mismo lote/ubicación que ya rechazó
    for alt in r["alternativas"]:
        assert not (alt["lote_id"] == caso["lote_pedido_id"]
                    and alt["ubicacion_id"] == caso["ubicacion_pedido_id"])


def test_pedido_que_entra_perfecto_no_bloquea():
    filas = S.disponibilidad_por_variedad("agata")
    assert filas, "necesito al menos un lote de agata con stock para este test"
    f = filas[0]
    r = S.verificar_pedido("agata", f["kg"] * 0.5, f["lote_id"], f["ubicacion_id"])
    assert r["bloqueado"] is False


def test_bloqueo_no_sugiere_calibre_incompatible_con_exportacion():
    # Cualquier alternativa devuelta cuando se pide calibre_requerido tiene
    # que respetar ese calibre (nunca sugerir granel para un pedido de
    # exportación).
    filas = S.disponibilidad_por_variedad("spunta", calibre_id="exportacion")
    if not filas:
        pytest.skip("no hay stock de spunta calibre exportación en este dataset")
    r = S.verificar_pedido("spunta", 10**9, calibre_requerido="exportacion")
    for alt in r["alternativas"]:
        assert alt["calibre"] == "Exportación" or alt.get("calibre_id") == "exportacion" \
            or True  # el campo expuesto es 'calibre' (nombre); validamos abajo por id
    todas = S.disponibilidad_por_variedad("spunta")
    ids_exportacion = {f["lote_id"] for f in todas if f["calibre_id"] == "exportacion"}
    for alt in r["alternativas"]:
        assert alt["lote_id"] in ids_exportacion


# ----------------------------------------------------------------------------
# Inconsistencias
# ----------------------------------------------------------------------------
def test_detector_encuentra_las_cinco_plantadas():
    hallazgos = I.detectar()
    tipos = {h["tipo"] for h in hallazgos}
    for esperado in ("remito_duplicado", "sin_dtv", "fecha_incoherente",
                     "tarjeta_cruzada", "kilos_no_cierran"):
        assert esperado in tipos, f"no se detectó: {esperado}"


def test_cada_hallazgo_cita_movimientos_concretos():
    hallazgos = I.detectar()
    con_evidencia = [h for h in hallazgos if h["tipo"] != "linaje_multivariedad"]
    for h in con_evidencia:
        assert isinstance(h["movimientos"], list)
        if h["tipo"] != "linaje_multivariedad":
            assert h["movimientos"], f"hallazgo sin evidencia: {h}"


# ----------------------------------------------------------------------------
# Liquidación
# ----------------------------------------------------------------------------
def test_liquidacion_transportistas_suma_todos_los_viajes():
    filas = L.liquidacion_transportistas()
    assert filas
    total_movs_liq = sum(f["viajes"] for f in filas)
    total_movs_con_transporte = sum(1 for m in M.movimientos() if m.get("transportista_id"))
    assert total_movs_liq == total_movs_con_transporte
    for f in filas:
        assert f["a_pagar"] >= 0
        assert f["kg_movidos"] >= 0


def test_liquidacion_frigorificos_por_periodo_filtra_fechas():
    todas = L.liquidacion_frigorificos()
    filtradas = L.liquidacion_frigorificos(desde="2099-01-01")
    assert sum(f["kg_ingresados"] for f in filtradas) == 0
    assert sum(f["kg_ingresados"] for f in todas) > 0


# ----------------------------------------------------------------------------
# Importador — planilla sintética con las columnas REALES documentadas
# ----------------------------------------------------------------------------
def _wb_bytes(nombre_solapa: str, encabezados: list[str], filas: list[list]) -> str:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = nombre_solapa
    ws.append(encabezados)
    for fila in filas:
        ws.append(fila)
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    wb.save(tmp.name)
    return tmp.name


def test_importer_reconoce_ingreso_tolvas_y_parsea_filas():
    ruta = _wb_bytes(
        "Ingreso Tolvas Santa Ana",
        ["Remito", "Fecha", "Transporte", "Variedad", "Lote", "Kgs", "Bolsas",
         "Observaciones", "Valor Flete/DTV"],
        [["R-1001", "03/06/2026", "Camillo", "Agata", "L45", 12500, None, "a granel", 45000]],
    )
    try:
        r = IMP.importar(ruta)
        assert "ingreso_tolva" in r["solapas"]
        fila = r["solapas"]["ingreso_tolva"]["filas"][0]
        assert fila["lote"] == "L45"
        assert fila["variedad"] == "Agata"
        assert fila["kg"] == 12500.0
        assert fila["fecha"] == "2026-06-03"
    finally:
        os.unlink(ruta)


def test_importer_marca_fila_dudosa_si_falta_lote():
    ruta = _wb_bytes(
        "Env a Frio",
        ["Remito", "Fecha", "Variedad", "Lote", "Categoria", "Calibre", "Bolsas",
         "Kgs", "Transporte", "Destino", "Kg.Prom", "Observaciones", "Cliente"],
        [["R-2002", "2026-06-10", "Spunta", None, "Inicial 2", "Granel", 20,
          9500, "Arenas", "Dospanca", 475, None, None]],
    )
    try:
        r = IMP.importar(ruta)
        fila = r["solapas"]["envio_frio"]["filas"][0]
        assert fila["confianza"] == "dudosa"
        assert fila["lote"] is None  # nunca inventa el dato ausente
        assert r["resumen"]["filas_con_dudas"] == 1
    finally:
        os.unlink(ruta)


def test_importer_solapa_no_reconocida_queda_declarada_no_perdida():
    ruta = _wb_bytes("Notas varias sueltas", ["algo"], [["x"]])
    try:
        r = IMP.importar(ruta)
        assert "Notas varias sueltas" in r["solapas_no_reconocidas"]
    finally:
        os.unlink(ruta)
