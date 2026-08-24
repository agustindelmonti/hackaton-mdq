"""
La suite que defiende la demo — Vertical 3 punta a punta.

QUÉ PRUEBA Y POR QUÉ ESTE ARCHIVO EXISTE.

La suite heredada está escrita contra otro tenant (Supermercados Horizonte) y
contra módulos que esta rama no tiene (cuentas corrientes, cobranzas). Corre lo
que es núcleo compartido y saltea el resto. Lo que NO había era una sola prueba
de la vertical que este equipo vino a resolver.

Acá están, en el orden del brief:

  N01 · el lenguaje libre se vuelve transacción, y el borde RECHAZA cuando los
        kilos no están. No advierte: rechaza.
  N02 · la diferencia entre lo declarado y lo contado llega con una hipótesis
        que trae EVIDENCIA, y el remito no se emite sin stock verificado.
  N03 · los seis papeles salen pre-completados desde la trazabilidad, con su
        número correlativo y el control cruzado entre ellos.

Y lo que se construyó encima: el reparto de tareas por rol y ubicación, los
objetivos medidos contra el dato vivo, los detectores de lo que quedó mal de
antes, el Excel que entra como Excel, y el mapa y el cerebro.

REGLA DE ESTA SUITE: ningún test hardcodea un número que la app calcula. Se
verifica la RELACIÓN (que el objetivo diga lo mismo que la pantalla, que el
documento diga lo mismo que la orden), no el valor — así el dataset puede
regenerarse sin dejar la suite en rojo por una diferencia de un kilo.
"""
from __future__ import annotations

import pytest

# Este módulo SÍ es de esta instancia: el guard de conftest lo deja pasar.
TENANT_PAPASUD = True

from core import (anomalias, cerebro, conciliacion, exportacion, importer,
                  mapa, movimientos, ordenes_carga, recordatorios, store, tareas)


# ---------------------------------------------------------------------------
# N01 · MOVIMIENTOS POR TEXTO LIBRE
# ---------------------------------------------------------------------------
class TestN01Movimientos:
    def test_el_interprete_saca_lote_cantidad_origen_y_destino(self):
        from core import movimientos_nl
        r = movimientos_nl.interpretar(
            "pasé dieciocho bolsones de Spunta de Pancani al galpón")
        i = r["interpretacion"]
        assert i["tipo"] == "traslado"
        # el número EN LETRAS es el caso real: adentro de una cámara nadie
        # escribe "18", lo dice
        assert i["cantidad"] == 18 and i["unidad"] == "bolsones"
        assert i["kg_calculado"] == 18000.0
        assert "pancani" in i["origen_texto"].lower()
        assert "galp" in (i["destino_texto"] or "").lower()

    def test_si_hay_varios_lotes_candidatos_elige_una_persona(self):
        """El sistema nunca desempata solo: mover el lote equivocado son
        bolsones reales en una cámara real."""
        from core import movimientos_nl
        r = movimientos_nl.interpretar(
            "pasé dieciocho bolsones de Spunta de Pancani al galpón")
        assert len(r["candidatos"]) > 1
        assert "lote" not in r["interpretacion"],             "el intérprete propone candidatos, no elige el lote"

    def test_el_estado_en_transito_existe_y_es_lo_que_no_tiene_la_planilla(self):
        sin_confirmar = movimientos.sin_confirmar()
        assert sin_confirmar, "el dataset tiene que traer traslados sin confirmar"
        for m in sin_confirmar:
            assert m["estado"] == "en_transito"
            assert m["origen"] != m["destino"]
            assert (m.get("dias_en_transito") or 0) >= 0

    def test_los_kilos_en_el_aire_no_estan_en_ninguna_ubicacion(self):
        """El punto entero del estado `en_transito`: esos kilos ya salieron del
        origen y todavía no entraron al destino."""
        r = conciliacion.resumen()
        en_aire = r["kg_en_transito"]
        assert en_aire > 0
        assert en_aire == pytest.approx(
            sum(float(m.get("kg") or 0) for m in movimientos.sin_confirmar()))

    def test_rechaza_cuando_el_origen_no_tiene_los_kilos(self):
        """El borde no advierte: RECHAZA. «Dieciocho» y «ochenta» suenan
        parecido adentro de una cámara con el motor andando."""
        arts = [a for a in store.raw_actual() if float(a.get("stock") or 0) > 0]
        a = arts[0]
        with pytest.raises(Exception):
            movimientos.registrar(
                lote=a["lote"], kg=float(a["stock"]) * 10 + 1_000_000,
                origen=a["ubicacion"], destino="Galpón Mar del Plata",
                usuario="marcos")


# ---------------------------------------------------------------------------
# N02 · VISTA ÚNICA, HIPÓTESIS CON EVIDENCIA, Y EL FRENO DEL REMITO
# ---------------------------------------------------------------------------
class TestN02Conciliacion:
    def test_las_ubicaciones_reales_estan_y_suman_el_total(self):
        ubis = conciliacion.por_ubicacion()
        ids = {u["id"] for u in ubis}
        assert {"planta_santa_ana", "galpon_mdp", "pancani"} <= ids
        r = conciliacion.resumen()
        assert sum(u["toneladas"] for u in ubis) == pytest.approx(
            r["toneladas_total"], abs=0.2)

    def test_cada_hipotesis_viaja_con_su_evidencia(self):
        """Sería fácil pasarle la diferencia a un LLM y pedirle que especule.
        En una empresa que audita cada lote, una causa inventada es peor que
        ningún dato: por eso cada hipótesis trae su clase y su respaldo."""
        abiertas = conciliacion.abiertas()
        assert abiertas, "el dataset tiene diferencias plantadas a propósito"
        clases = set()
        for d in abiertas:
            h = d["hipotesis"]
            assert h["clase"], "toda hipótesis declara de qué clase es"
            assert h["texto"], "y la explica en castellano"
            clases.add(h["clase"])
            if h["clase"] == "movimiento_sin_confirmar":
                ev = h.get("evidencia", {}).get("movimiento")
                assert ev and ev.get("numero"), \
                    "la hipótesis del movimiento cita el movimiento"
        assert "sin_explicacion" in clases or len(clases) >= 2, \
            "las hipótesis no son todas la misma"

    def test_hay_una_diferencia_que_el_sistema_NO_explica(self):
        """La honestidad del módulo: cuando no hay nada en los datos que lo
        explique, lo dice — no inventa una causa."""
        clases = {d["hipotesis"]["clase"] for d in conciliacion.abiertas()}
        assert "sin_explicacion" in clases

    def test_una_orden_frenada_no_se_puede_emitir_y_dice_por_que(self):
        frenadas = [o for o in ordenes_carga.pendientes_con_estado()
                    if not o.get("puede_emitirse")]
        assert frenadas, "el dataset trae al menos una orden frenada"
        for o in frenadas:
            assert o["bloqueos"], "una orden frenada declara SUS motivos"
            for b in o["bloqueos"]:
                assert b["control"], "cada bloqueo nombra el control que lo frenó"

    def test_el_freno_vive_en_el_core_y_no_en_la_pantalla(self):
        """No hay puerta de atrás: emitir una orden bloqueada tiene que fallar
        del lado del servidor, no estar sólo escondido el botón."""
        frenada = next(o for o in ordenes_carga.pendientes_con_estado()
                       if not o.get("puede_emitirse"))
        with pytest.raises(Exception):
            ordenes_carga.emitir(frenada["numero"], usuario="cecilia")


# ---------------------------------------------------------------------------
# N03 · LA CARPETA DE EXPORTACIÓN
# ---------------------------------------------------------------------------
class TestN03Exportacion:
    @pytest.fixture()
    def orden(self):
        e = exportacion.embarques()
        assert e, "el dataset trae embarques"
        return e[0]["numero"]

    def test_la_carpeta_trae_los_seis_papeles(self, orden):
        c = exportacion.carpeta(orden)
        assert len(c["documentos"]) == 6
        organismos = {d["organismo"] for d in c["documentos"]}
        # los tres organismos del circuito real: la empresa, el INASE y el SENASA
        assert any("INASE" in o for o in organismos)
        assert any("SENASA" in o for o in organismos)

    def test_cada_campo_dice_de_donde_salio(self, orden):
        """La decisión que sostiene la pantalla: un campo pre-completado sin
        fuente es un campo en el que nadie confía."""
        d = exportacion.documento(orden, "factura_proforma")
        completos = [c for s in d["secciones"] for c in s["campos"]
                     if c.get("valor") not in (None, "")]
        assert completos
        assert all(c.get("fuente") for c in completos)

    def test_el_numero_correlativo_es_estable(self, orden):
        """Dos veces el mismo documento tiene que dar el mismo número: si no,
        la factura y el packing list dejan de referenciarse."""
        a = exportacion.documento(orden, "packing_list")["numero"]
        b = exportacion.documento(orden, "packing_list")["numero"]
        assert a == b and a.startswith("PS-PKL-")

    def test_lo_que_falta_se_declara(self, orden):
        d = exportacion.documento(orden, "factura_proforma")
        comp = d["completitud"]
        estados = [c["estado"] for s in d["secciones"] for c in s["campos"]]
        # `total` cuenta TODOS los campos; `faltan` sólo los OBLIGATORIOS que
        # están vacíos. Un campo opcional en blanco no es algo que falte — si
        # entrara en la cuenta, ninguna carpeta llegaría nunca al 100%.
        assert comp["total"] == len(estados)
        assert comp["faltan"] == estados.count("falta")
        assert comp["completos"] == estados.count("completo")
        assert len(comp["que_falta"]) == comp["faltan"]

    def test_el_control_cruzado_compara_los_tres_documentos(self, orden):
        """El descuadre entre factura, packing list y solicitud del INASE es la
        causa número uno de demora en aduana, y es trivial de verificar cuando
        los tres salen de la misma fuente."""
        c = exportacion.carpeta(orden)
        cc = c["control_cruzado"]
        assert cc, "la carpeta declara su control cruzado"
        assert all("ok" in x or "estado" in x for x in cc.get("checks", cc)
                   if isinstance(x, dict))


# ---------------------------------------------------------------------------
# EL TRABAJO REPARTIDO
# ---------------------------------------------------------------------------
class TestTareas:
    def test_cada_sugerencia_tiene_persona_y_evidencia(self):
        s = tareas.sugeridas()
        assert s, "con traslados sin confirmar y órdenes frenadas hay trabajo"
        for x in s:
            assert x["para"]["username"], "toda tarea propuesta tiene dueño"
            assert x["titulo"] and x["detalle"]
            assert x["evidencia"], "y trae con qué verificarla"
            assert x["prioridad"] in tareas.PRIORIDAD

    def test_el_traslado_lo_confirma_quien_esta_en_el_destino(self):
        """El ruteo sale del ROL y de las UBICACIONES del perfil, no de una
        lista de usernames: una persona nueva con el mismo rol hereda las
        tareas sin tocar código."""
        confirmar = [x for x in tareas.sugeridas()
                     if x["clase"] == "traslado_sin_confirmar"]
        assert confirmar
        for x in confirmar:
            destino = x["evidencia"]["destino"]
            u = x["para"]
            if "Galpón" in destino:
                assert "galpón" in (u["rol"] or "").lower() or \
                       "encargado" in (u["rol"] or "").lower()

    def test_el_operario_le_gana_al_encargado_en_su_propia_ubicacion(self):
        """El encargado responde por las cuatro ubicaciones: sin preferencia se
        llevaría todas las tareas de piso y el que tiene los bolsones delante
        no se enteraría de ninguna."""
        u = tareas._operario_de("galpon_mdp")
        assert u and "operario" in (u.get("rol") or "").lower()

    def test_asignar_le_da_la_tarea_a_esa_persona_y_no_la_vuelve_a_ofrecer(self):
        antes = tareas.sugeridas()
        s = antes[0]
        tareas.asignar(s["titulo"], para=s["para"]["username"],
                       creado_por="ernesto", origen=s["id"],
                       seccion=s.get("seccion"), prioridad=s["prioridad"])
        mias = [r["texto"] for r in tareas.de_usuario(s["para"]["username"])]
        assert s["titulo"] in mias
        assert s["id"] not in {x["id"] for x in tareas.sugeridas()}, \
            "una sugerencia ya asignada no se vuelve a proponer"

    def test_marcarla_hecha_la_saca_de_lo_pendiente_y_el_panorama_lo_ve(self):
        r = tareas.asignar("Contar la Cámara 3 del Batán", para="marcos",
                           creado_por="ruben")
        assert any(x["id"] == r["id"] for x in tareas.de_usuario("marcos"))
        recordatorios.completar(r["id"])
        assert not any(x["id"] == r["id"] for x in tareas.de_usuario("marcos"))
        pan = tareas.panorama()
        assert pan["hechas"] >= 1

    def test_solo_el_dueno_y_el_encargado_reparten_trabajo(self):
        assert tareas.puede_asignar({"es_admin": True, "rol": "Dueño"})
        assert tareas.puede_asignar({"es_admin": False, "rol": "Encargado de depósito"})
        assert not tareas.puede_asignar({"es_admin": False, "rol": "Operario de frigorífico"})


# ---------------------------------------------------------------------------
# ARREGLAR EL PASADO
# ---------------------------------------------------------------------------
class TestAnomaliasPapasud:
    def test_los_detectores_son_del_rubro(self):
        tipos = {a["tipo"] for a in anomalias.analizar_existentes()}
        # el detector de "más de 10.000 unidades" no puede volver: acá la unidad
        # es el kilo y lo cumple el 94% del catálogo
        assert "stock_outlier" not in tipos
        assert tipos & {"categoria_perdida", "sin_analisis", "traslado_huerfano",
                        "trazabilidad_incompleta", "conteo_sin_cerrar", "duplicado"}

    def test_ninguna_anomalia_marca_casi_todo_el_catalogo(self):
        """Una alerta que se dispara siempre no es una alerta: es ruido que
        entrena a la gente a ignorar la pantalla."""
        total = len([a for a in store.raw_actual() if float(a.get("stock") or 0) > 0])
        for a in anomalias.analizar_existentes():
            assert a["items"] <= total * 0.6, \
                f"{a['tipo']} marca el {a['items'] / total:.0%} del catálogo"

    def test_van_ordenadas_por_impacto(self):
        impactos = [a["impacto_pesos"] for a in anomalias.analizar_existentes()]
        assert impactos == sorted(impactos, reverse=True)

    def test_ninguna_se_corrige_sola_salvo_la_que_tiene_correccion_declarada(self):
        with pytest.raises(ValueError):
            anomalias.aplicar("categoria_perdida", "recategorizar", {})


# ---------------------------------------------------------------------------
# EL EXCEL QUE ENTRA COMO EXCEL
# ---------------------------------------------------------------------------
class TestImportarPlanilla:
    HEADERS = ["Lote", "Variedad", "Categoria", "Campania", "Ubicacion",
               "Camara", "Bolsones", "Kg", "Calibre"]

    def _filas(self):
        return [
            ["PS-A", "Spunta", "Fundación", "2025/26", "Frigorifico Batan", "C1", 10, 10000, "Grado 1"],
            ["PS-A", "Spunta", "Fundación", "2025/26", "Frigorifico Batan", "C1", 10, 10000, "Grado 1"],
            ["PS-B", "Innovator", "", "2025/26", "Galpon Chapadmalal", "", 12, 14000, ""],
            ["PS-C", "Asterix", "Certificada", "2025/26", "Frigorifico Ruta 226", "C2", 9, "aprox 9000", ""],
        ]

    def test_el_vocabulario_del_semillero_mapea_solo(self):
        info = importer.inferir_mapeo(self.HEADERS, "stock_semilla")
        m = info["mapeo"]
        for campo in ("lote", "variedad", "categoria", "campania", "ubicacion",
                      "camara", "bolsones", "kilos", "calibre"):
            assert m.get(campo), f"no mapeó {campo}"
        assert not info["sin_mapear"]

    def test_la_camara_no_se_come_la_ubicacion(self):
        """`camara` estaba como sinónimo de `ubicacion`: se llevaba la columna
        Cámara y la ubicación quedaba sin mapear."""
        m = importer.inferir_mapeo(self.HEADERS, "stock_semilla")["mapeo"]
        assert m["ubicacion"] == "Ubicacion" and m["camara"] == "Camara"

    def test_dice_que_esta_roto_adentro_y_con_que_fila(self):
        info = importer.previsualizar_filas(self.HEADERS, self._filas(), "stock_semilla")
        clases = {p["clase"] for p in info["problemas"]}
        assert {"duplicado", "campo_vacio", "no_numerico"} <= clases
        for p in info["problemas"]:
            assert p["filas"], "cada problema dice en qué fila está"
            # fila 2 = la primera de datos (la 1 son los encabezados)
            assert min(p["filas"]) >= 2

    def test_lo_que_esta_bien_no_se_marca(self):
        sanas = [self._filas()[0]]
        info = importer.previsualizar_filas(self.HEADERS, sanas, "stock_semilla")
        assert not info["problemas"]


# ---------------------------------------------------------------------------
# EL MAPA Y EL CEREBRO
# ---------------------------------------------------------------------------
class TestMapaYCerebro:
    def test_el_mapa_tiene_las_ubicaciones_con_stock_y_la_marca_en_el_centro(self):
        d = mapa.mapa()
        centro = [n for n in d["nodos"] if n["capa"] == "centro"]
        ubis = [n for n in centro if n["tipo"] == "ubicacion"]
        assert len(ubis) >= 3
        ids = " ".join(n["id"] for n in ubis).lower()
        assert "pancani" in ids or "galpon" in ids
        marca = [n for n in centro if n["tipo"] == "marca"]
        assert len(marca) == 1 and marca[0].get("logo")

    def test_el_mapa_no_tiene_nodos_huerfanos(self):
        """Una caja sin una sola línea en un mapa de flujo se lee como un error
        de dibujo, no como información."""
        d = mapa.mapa()
        conectados = set()
        for a in d["aristas"]:
            conectados.add(a["origen"])
            conectados.add(a["destino"])
        sueltos = [n["id"] for n in d["nodos"]
                   if n["id"] not in conectados and n["tipo"] != "marca"]
        assert not sueltos, f"nodos sin ninguna arista: {sueltos}"

    def test_cada_hallazgo_del_mapa_ilumina_un_camino_real(self):
        d = mapa.mapa()
        ids = {n["id"] for n in d["nodos"]}
        assert d["hallazgos"]
        for h in d["hallazgos"]:
            assert h["titulo"] and h["detalle"]
            for nid in h["camino"]["nodos"]:
                assert nid in ids, f"{h['id']} ilumina un nodo que no existe"

    def test_el_cerebro_no_infiere_ninguna_arista(self):
        """Toda relación tiene que ser un campo declarado del lote o un renglón
        de una orden. Si aparece una relación 'inferida', hay que decirlo en la
        pantalla — y hoy la pantalla dice que no hay ninguna."""
        d = cerebro.completo()
        rels = {a["rel"] for a in d["aristas"]}
        assert rels <= {"variedad", "categoria_semilla", "campo_origen",
                        "campania", "esta_en", "comprometido", "para",
                        "destino", "traslado"}
        assert "no se infiere" in d["meta"]["fuente"].lower()

    def test_el_cerebro_y_el_mapa_cuentan_los_mismos_lotes(self):
        """Dos vistas del mismo negocio no pueden decir cosas distintas."""
        d = cerebro.completo()
        lotes_cerebro = d["resumen"]["por_tipo"]["lote"]
        vivos = len([a for a in store.raw_actual() if float(a.get("stock") or 0) != 0])
        assert lotes_cerebro == vivos

    def test_las_ubicaciones_con_stock_son_las_anclas_del_cerebro(self):
        d = cerebro.completo()
        ubis = [n for n in d["nodos"] if n["tipo"] == "ubicacion" and n["kg"] > 0]
        assert len(ubis) >= 3
        ids = " ".join(n["id"] for n in ubis).lower()
        assert "pancani" in ids or "planta" in ids


# ---------------------------------------------------------------------------
# LOS OBJETIVOS DICEN LO MISMO QUE LA PANTALLA
# ---------------------------------------------------------------------------
class TestObjetivos:
    def test_los_responsables_existen_en_esta_empresa(self):
        from core import objetivos_medidos
        import usuarios_papasud
        for oid, d in objetivos_medidos.DEFS.items():
            assert d["responsable"] in usuarios_papasud.USUARIOS, \
                f"{oid} se lo asignaron a alguien que no trabaja acá"

    def test_cada_objetivo_apunta_a_una_seccion_que_existe(self):
        from core import objetivos_medidos
        secciones = {"movimientos", "conciliacion", "logistica", "trazabilidad",
                     "deposito", "saneamiento", "inventario", "exportacion"}
        for oid, d in objetivos_medidos.DEFS.items():
            assert d["seccion"] in secciones, f"{oid} apunta a {d['seccion']}"

    def test_el_progreso_se_calcula_y_no_se_hardcodea(self):
        from core import objetivos_medidos
        objs = objetivos_medidos.construir(
            {"traslados_confirmados": 0}, "2026-08-22")
        o = objs[0]
        assert o["progreso"] == 1.0 and o["estado"] == "cumplido"
        objs = objetivos_medidos.construir(
            {"traslados_confirmados": objetivos_medidos.DEFS["traslados_confirmados"]["baseline"]},
            "2026-08-22")
        assert objs[0]["progreso"] == 0.0
