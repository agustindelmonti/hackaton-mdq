"""
El modelo que sale de la planilla real — no del seed sintético.

Estos tests defienden las relaciones que la Planilla de movimientos 2026.xls
tiene y que data-papasud aplana: lote namespaced, remito con líneas, DTV del
viaje, código visual bolsa+hilo, frío de terceros, calibre comercial, envase
de ~50 kg, reproceso/retorno, y lote_padre_id de verdad.

No tocan data-papasud/. Leen el paquete data-planilla.
"""
from __future__ import annotations

import os
import sys

import pytest

TENANT_PAPASUD = True

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PLANILLA = os.path.join(_RAIZ, "data-planilla")
if _PLANILLA not in sys.path:
    sys.path.insert(0, _PLANILLA)

from data_planilla import dominio as D  # noqa: E402
from data_planilla import modelo as M  # noqa: E402


# ---------------------------------------------------------------------------
# Identidad del lote: el nro corto NO es único
# ---------------------------------------------------------------------------
class TestClaveLote:
    def test_el_mismo_numero_en_dos_chacras_son_lotes_distintos(self):
        a = M.clave_lote("santa_ana", "spunta", "50")
        b = M.clave_lote("trevelin", "beo", "50")
        assert a != b
        assert a == "santa_ana:spunta:50"
        assert b == "trevelin:beo:50"

    def test_el_sufijo_a_b_parte_el_lote(self):
        a = M.clave_lote("santa_ana", "spunta", "34", "a")
        b = M.clave_lote("santa_ana", "spunta", "34", "b")
        assert a != b
        assert a.endswith(":34:a")
        assert b.endswith(":34:b")

    def test_parsea_nros_como_los_escribe_la_planilla(self):
        assert M.parsear_nro_lote(301) == ("301", None)
        assert M.parsear_nro_lote("16 b") == ("16", "b")
        assert M.parsear_nro_lote("37A") == ("37", "a")
        assert M.parsear_nro_lote("1 b") == ("1", "b")
        assert M.parsear_nro_lote("71 A") == ("71", "a")

    def test_rechaza_una_clave_sin_chacra(self):
        with pytest.raises(ValueError):
            M.clave_lote("", "spunta", "301")


# ---------------------------------------------------------------------------
# Linaje INASE
# ---------------------------------------------------------------------------
class TestLinaje:
    def test_inicial_1_puede_ser_padre_de_inicial_2(self):
        assert M.linaje_valido("inicial_1", "inicial_2") is True

    def test_inicial_3_no_puede_ser_padre_de_inicial_1(self):
        assert M.linaje_valido("inicial_3", "inicial_1") is False

    def test_sin_padre_es_valido_para_material_de_punta(self):
        assert M.linaje_valido(None, "inicial_1") is True

    def test_lote_con_padre_invalido_no_se_puede_persistir(self):
        hijo = {
            "id": "santa_ana:spunta:301",
            "categoria_id": "inicial_1",
            "lote_padre_id": "santa_ana:spunta:310",
        }
        padre = {"id": "santa_ana:spunta:310", "categoria_id": "inicial_3"}
        r = M.validar_lote(hijo, padre=padre)
        assert r["ok"] is False
        assert r["motivo"] == "linaje_invalido"


# ---------------------------------------------------------------------------
# Remito = documento; las filas son líneas
# ---------------------------------------------------------------------------
class TestRemito:
    def test_un_remito_agrupa_lineas_y_el_dtv_cuelga_del_viaje(self):
        remito = M.armar_remito(
            numero="1009",
            fecha="2026-03-29",
            transporte_id="camillo_gaston",
            dtv_e="13534780-9",
            origen_id="campo_santa_ana",
            lineas=[
                {"lote_id": "santa_ana:spunta:300", "kg": 10200, "bolsas": 204,
                 "destino_id": "galpon_mdp", "calibre_comercial": "sin_tamanar"},
                {"lote_id": "santa_ana:asterix:811", "kg": 25000, "bolsas": 500,
                 "destino_id": "galpon_mdp", "calibre_comercial": "sin_tamanar"},
            ],
        )
        assert remito["id"] == "R-2026-1009"
        assert remito["dtv_e"] == "13534780-9"
        assert remito["transporte_id"] == "camillo_gaston"
        assert len(remito["lineas"]) == 2
        assert {ln["lote_id"] for ln in remito["lineas"]} == {
            "santa_ana:spunta:300", "santa_ana:asterix:811",
        }
        assert remito["kg_total"] == 35200
        assert all("dtv_e" not in ln for ln in remito["lineas"])

    def test_remito_trevelin_36_acepta_once_variedades_en_un_viaje(self):
        lineas = [
            {"lote_id": f"trevelin:{vid}:{nro}", "kg": kg, "bolsas": 1,
             "destino_id": "planta_santa_ana", "calibre_comercial": "recibo"}
            for vid, nro, kg in [
                ("agata", "2", 5983), ("spunta", "3", 12397),
                ("king_russet", "10", 3880), ("ludmilla", "6", 1132),
                ("alverstone", "42", 2425), ("markies", "4", 1725),
                ("daifla", "5", 3072), ("seven_four_7", "7", 754),
                ("ikarus", "51", 2857), ("edison", "9", 1994),
                ("atlantic", "1", 53.9),
            ]
        ]
        remito = M.armar_remito(
            numero="36", fecha="2026-04-01", transporte_id="el_salvador",
            dtv_e=None, origen_id="campo_trevelin", lineas=lineas,
        )
        assert len(remito["lineas"]) == 11
        assert len({ln["lote_id"].split(":")[1] for ln in remito["lineas"]}) == 11

    def test_s_remito_es_un_viaje_legitimo(self):
        remito = M.armar_remito(
            numero="s/remito", fecha="2026-06-04",
            transporte_id="camillo_mario", dtv_e=None,
            origen_id="belmonte",
            lineas=[{"lote_id": "santa_ana:spunta:50", "kg": 38200,
                     "bolsas": 764, "destino_id": "planta_santa_ana",
                     "calibre_comercial": "granel"}],
        )
        assert remito["id"].startswith("R-2026-s-remito")
        assert remito["sin_numero"] is True


# ---------------------------------------------------------------------------
# Catálogos reales
# ---------------------------------------------------------------------------
class TestCatalogos:
    def test_hay_frio_de_terceros(self):
        tipos = {u["tipo"] for u in D.UBICACIONES}
        assert "frio_tercero" in tipos
        ids = {u["id"] for u in D.UBICACIONES}
        for uid in ("pancani", "cecive", "sasula", "belmonte", "frigopap"):
            assert uid in ids

    def test_hay_planta_y_chacras_propias(self):
        ids = {u["id"] for u in D.UBICACIONES}
        assert "planta_santa_ana" in ids
        assert "galpon_mdp" in ids
        chacras = {c["id"] for c in D.CHACRAS}
        assert "santa_ana" in chacras
        assert "trevelin" in chacras

    def test_variedades_cubren_la_planilla_no_el_seed_viejo(self):
        ids = {v["id"] for v in D.VARIEDADES}
        for vid in ("agata", "daifla", "sagitta", "ludmilla", "seven_four_7",
                    "spunta", "atlantic", "asterix"):
            assert vid in ids
        # Innovator no está en la planilla 2026; no lo inventamos acá.
        assert "innovator" not in ids

    def test_calibre_comercial_no_es_el_grado_inase_en_mm(self):
        ids = {c["id"] for c in D.CALIBRES_COMERCIALES}
        assert ids >= {"recibo", "exportacion", "sin_chicas", "granel",
                       "desc_paraguay", "sin_tamanar"}
        assert 1 not in ids and 2 not in ids

    def test_la_bolsa_pesa_cerca_de_50_kg_no_1000(self):
        assert D.KG_POR_BOLSA == 50
        assert D.envase("bolsa")["kg_nominal"] == 50
        assert D.envase("bolson")["kg_nominal"] == 700
        assert D.envase("granel")["kg_nominal"] is None


# ---------------------------------------------------------------------------
# Movimientos: tipos y campos que la planilla usa
# ---------------------------------------------------------------------------
class TestMovimiento:
    def test_reproceso_y_retorno_existen(self):
        assert "reproceso" in M.TIPOS_MOVIMIENTO
        assert "retorno" in M.TIPOS_MOVIMIENTO
        assert set(M.TIPOS_MOVIMIENTO) >= {
            "ingreso", "traslado", "egreso", "descarte", "reproceso", "retorno",
        }

    def test_un_movimiento_apunta_al_remito_no_al_reves(self):
        mov = M.armar_movimiento(
            tipo="traslado",
            lote_id="santa_ana:spunta:301",
            kg=32760,
            origen_id="planta_santa_ana",
            destino_id="pancani",
            remito_id="R-2026-0910",
            transporte_id="delcasagro",
            ubicacion_carga_id="planta_santa_ana",
            calibre_comercial="recibo",
            envase="bolsa",
            bolsas=660,
            kg_promedio=49.63,
        )
        assert mov["remito_id"] == "R-2026-0910"
        assert mov["transporte_id"] == "delcasagro"
        assert mov["ubicacion_carga_id"] == "planta_santa_ana"
        assert mov["bolsas"] == 660
        assert mov["kg_promedio"] == pytest.approx(49.63)
        assert "bolsones" not in mov or mov["bolsones"] is None

    def test_egreso_distingue_broker_de_cliente_final(self):
        mov = M.armar_movimiento(
            tipo="egreso",
            lote_id="santa_ana:spunta:301",
            kg=29400,
            origen_id="planta_santa_ana",
            destino_id=None,
            cliente_id="delcaso",
            cliente_final_id="romero_m",
            remito_id="R-2026-0916",
        )
        assert mov["cliente_id"] == "delcaso"
        assert mov["cliente_final_id"] == "romero_m"


# ---------------------------------------------------------------------------
# Código visual: cómo se reconoce un bulto en el piso
# ---------------------------------------------------------------------------
class TestCodigoVisual:
    def test_trevelin_exige_bolsa_e_hilo(self):
        lote = {
            "id": "trevelin:spunta:14",
            "chacra_id": "trevelin",
            "variedad_id": "spunta",
            "nro": "14",
            "categoria_id": "inicial_3",
        }
        r = M.validar_lote(lote)
        assert r["ok"] is False
        assert r["motivo"] == "falta_codigo_visual"

    def test_con_bolsa_e_hilo_pasa(self):
        lote = {
            "id": "trevelin:spunta:14",
            "chacra_id": "trevelin",
            "variedad_id": "spunta",
            "nro": "14",
            "categoria_id": "inicial_3",
            "color_bolsa": "blanca",
            "color_hilo": "verde",
        }
        r = M.validar_lote(lote)
        assert r["ok"] is True


# ---------------------------------------------------------------------------
# Dataset generado: las relaciones sobreviven a la escritura
# ---------------------------------------------------------------------------
class TestDataset:
    @pytest.fixture
    def data(self):
        from data_planilla import generar
        return generar.construir()

    def test_ningun_par_de_lotes_comparte_clave(self, data):
        ids = [l["id"] for l in data["lotes"]]
        assert len(ids) == len(set(ids))
        assert len(ids) >= 8

    def test_lote_50_existe_en_santa_ana_y_en_trevelin(self, data):
        ids = {l["id"] for l in data["lotes"]}
        assert "santa_ana:spunta:50" in ids
        assert "trevelin:beo:50" in ids

    def test_hay_lote_padre_y_el_linaje_cierra(self, data):
        por_id = {l["id"]: l for l in data["lotes"]}
        con_padre = [l for l in data["lotes"] if l.get("lote_padre_id")]
        assert con_padre, "el seed tiene que traer al menos un lote con padre"
        for l in con_padre:
            padre = por_id[l["lote_padre_id"]]
            assert M.linaje_valido(padre["categoria_id"], l["categoria_id"])

    def test_remitos_tienen_lineas_y_dtv_en_la_cabecera(self, data):
        r1009 = next(r for r in data["remitos"] if r["numero"] == "1009")
        assert len(r1009["lineas"]) >= 2
        assert r1009.get("dtv_e") or r1009.get("transporte_id")
        lotes = {ln["lote_id"] for ln in r1009["lineas"]}
        assert len(lotes) >= 2

    def test_proyeccion_inventory_no_pierde_la_clave_real(self, data):
        arts = data["inventory"]["articulos"]
        assert arts
        for a in arts:
            assert a["lote"] == a["lote_id"]
            assert ":" in a["lote"]
            assert a.get("chacra_id")
            assert a.get("nro_lote")

    def test_apartados_exponen_remitos_y_transportes(self, data):
        ap = data["apartados"]
        assert "remitos" in ap
        assert "transportes" in ap
        assert ap["remitos"]["filas"]
        assert ap["movimientos"]["filas"]
        tipos = {m["tipo"] for m in ap["movimientos"]["filas"]}
        assert "reproceso" in tipos or "retorno" in tipos

    def test_nro_50_no_desempata_solo(self, data):
        hits = M.lotes_por_nro(data["lotes"], 50)
        assert len(hits) >= 2


class TestImportar:
    def test_extrae_dtv_de_la_observacion(self):
        from data_planilla.importar import extraer_dtv
        assert extraer_dtv("b.blanca-dtv 13451462-0") == "13451462-0"
        assert extraer_dtv("dtv 13354667-7") == "13354667-7"

    def test_dospanca_resuelve_a_pancani(self):
        from data_planilla.importar import fila_a_linea
        ln = fila_a_linea(
            {"Variedad": "spunta", "Lote": 301, "Kgs.": 100, "Destino": "dospanca"},
            hoja="Env a Frio",
        )
        assert ln["destino_id"] == "pancani"
        assert ln["lote_id"] == "santa_ana:spunta:301"

    def test_trevelin_usa_chacra_trevelin(self):
        from data_planilla.importar import fila_a_linea
        ln = fila_a_linea(
            {"Variedad": "beo", "Lote": 50, "Kgs": 1264,
             "Color bolsa": "amarilla", "Color hilo": "naranja",
             "categoria": "inicial 1"},
            hoja="Ingreso  Trevelin",
        )
        assert ln["lote_id"] == "trevelin:beo:50"
        assert ln["categoria_id"] == "inicial_1"
        assert ln["color_bolsa"] == "amarilla"


class TestBackendNoRompeElDemo:
    def test_movimientos_conoce_reproceso_y_retorno(self):
        from core import movimientos
        assert "reproceso" in movimientos.TIPOS
        assert "retorno" in movimientos.TIPOS

    def test_esquema_conoce_remitos(self):
        from core import esquema
        assert "remitos" in esquema.TIPOS
        assert "transportes" in esquema.TIPOS

    def test_semilla_no_revienta_sin_calibres_comerciales(self):
        from core import semilla
        assert isinstance(semilla.calibres_comerciales(), list)
        assert isinstance(semilla.chacras(), list)

    def test_planilla_inactiva_sobre_el_seed_sintetico(self):
        from core import planilla
        assert planilla.activo() is False
        assert planilla.remitos() == []
