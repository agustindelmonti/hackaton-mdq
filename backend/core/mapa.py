"""
mapa.py · El mapa de la operación — con el stock en el centro.

POR QUÉ ESTE MAPA NO ES UN ORGANIGRAMA

La tentación es dibujar la empresa entera con todo al mismo nivel: el
laboratorio, los campos, las cámaras, los clientes, el equipo. Sale un diagrama
lindo y se pierde el punto. Lo que hay que resolver es el control de stock en
cuatro ubicaciones; todo lo demás es el contexto que lo explica.

Por eso el mapa tiene TRES CAPAS FIJAS y el orden es el del negocio:

        ORIGEN            →         CENTRO          →        DESTINO
    laboratorio in vitro       LAS 4 UBICACIONES        órdenes de carga
    El Calafate                los lotes                clientes
    campos                     movimientos              puerto
    campañas · variedades      conteos                  país · documentos

El ojo va de izquierda a derecha y PASA OBLIGATORIAMENTE POR EL STOCK. No hay
forma de mirar esto y no ver cuál es el centro.

POR QUÉ CAPAS FIJAS Y NO UN GRAFO DE FUERZAS

Un force-graph se ve espectacular en una captura y se lee mal en vivo: los
nodos se acomodan solos y la POSICIÓN NO SIGNIFICA NADA. Si alguien pregunta
«¿por qué ese nodo está ahí?», la respuesta honesta es «porque el algoritmo lo
puso ahí». Acá la respuesta es «porque eso es el origen y aquello el destino».
Una se explica sola. La exploración libre vive en el Cerebro, que es otra cosa.

QUÉ CALCULA ESTE MÓDULO Y QUÉ NO

Calcula la ESTRUCTURA (qué nodos hay, de qué capa, cómo se conectan) y las
métricas de cada nodo, leyéndolas de los mismos módulos que alimentan las
pantallas — no hay una segunda fuente de verdad que pueda quedar desincronizada.
No calcula posiciones: eso es presentación y vive en el frontend.
"""
from __future__ import annotations

from . import (conciliacion, esquema, movimientos, notas, ordenes_carga,
               semilla, store)
from . import paths
from .fechas import hoy, parse_fecha

# Cuánto falta para que la brotación sea urgente (mismo umbral que las
# oportunidades: un solo número para todo el sistema).
VENTANA_BROTACION_DIAS = 45


def _empresa() -> str:
    """El nombre del tenant, de la misma fuente que /api/health."""
    try:
        import data_store
        return data_store.meta().get("empresa") or "Papasud S.A."
    except Exception:
        return "Papasud S.A."


def _sid(x: str) -> str:
    """Un id sin caracteres que rompan un selector CSS.

    React Flow ubica sus nodos y aristas con `[data-id="..."]`; un `:` adentro
    del id hace que el selector no matchee y la arista simplemente NO SE DIBUJA,
    sin ningún error en consola. Costó encontrarlo: los datos estaban bien, los
    handles montados, los nodos medidos, y el lienzo salía sin una sola línea."""
    return x.replace(":", "_").replace(">", "_").replace(" ", "_")


def _nodo(nid, tipo, capa, etiqueta, **extra) -> dict:
    # El id va saneado igual que el de las aristas: los dos puntos rompen los
    # selectores internos de React Flow y la arista queda sin dibujar.
    return {"id": _sid(nid), "tipo": tipo, "capa": capa, "etiqueta": etiqueta, **extra}


def _arista(origen, destino, tipo, **extra) -> dict:
    o, d = _sid(origen), _sid(destino)
    return {"id": f"{o}__{d}__{tipo}", "origen": o, "destino": d,
            "tipo": tipo, **extra}


# ---------------------------------------------------------------------------
# EL CENTRO — las cuatro ubicaciones y lo que se mueve entre ellas
# ---------------------------------------------------------------------------
def _centro(arts: list[dict]) -> tuple[list[dict], list[dict]]:
    nodos, aristas = [], []
    todos = conciliacion.por_ubicacion()
    # La planta no es la quinta cámara: el cuadro sigue siendo 2×2 y el hub
    # lo dibuja `_planta_y_galpones` en su propia columna.
    ubis = [u for u in todos if u.get("tipo") != "planta"]
    ids_planta = {u["id"] for u in todos if u.get("tipo") == "planta"}

    for u in ubis:
        lotes = [a for a in arts if a.get("ubicacion_id") == u["id"]]
        # Los lotes NO van sueltos: 147 nodos son una mancha. Se agrupan por
        # variedad dentro de cada ubicación y se expanden al tocar.
        por_var: dict[str, dict] = {}
        for a in lotes:
            v = a.get("variedad") or "—"
            g = por_var.setdefault(v, {"lotes": 0, "kg": 0.0, "valor": 0.0,
                                       "codigos": []})
            g["lotes"] += 1
            g["kg"] += float(a.get("stock") or 0)
            g["valor"] += float(a.get("stock") or 0) * float(a.get("costo_iva") or 0)
            g["codigos"].append(a.get("codigo"))

        nodos.append(_nodo(
            f"ubi:{u['id']}", "ubicacion", "centro", u["nombre"],
            subtitulo=u.get("direccion"),
            estado=u["estado"],
            metricas={
                "toneladas": u["toneladas"],
                "lotes": u["lotes"],
                "ocupacion_pct": u["ocupacion_pct"],
                "valor": u["valor"],
                "diferencias": u["diferencias_abiertas"],
                "por_brotar": len(u.get("por_brotar_45d") or []),
                "ya_brotados": u.get("ya_brotados", 0),
            },
            tipo_sitio=u["tipo"],
            camaras=u.get("camaras") or [],
            temp_objetivo=u.get("temp_objetivo"),
            # los grupos de lote que cuelgan de esta ubicación (se expanden)
            grupos=[{"id": f"grp:{u['id']}:{v}", "variedad": v,
                     "lotes": g["lotes"], "kg": round(g["kg"], 1),
                     "valor": round(g["valor"], 2), "codigos": g["codigos"]}
                    for v, g in sorted(por_var.items(), key=lambda kv: -kv[1]["kg"])],
        ))

    # EL CENTRO DEL CENTRO: la empresa. No es decoración — es la respuesta a
    # "¿de quién es todo esto?" dibujada en el único lugar donde no se discute:
    # el medio de las cuatro ubicaciones. La pantalla le pone el logo.
    nodos.append(_nodo(
        "marca:papasud", "marca", "centro", _empresa(),
        subtitulo="Cuatro ubicaciones · una sola verdad",
        # El logo viaja EN EL NODO, del mismo lugar que lo saca /api/health: el
        # tenant. Que la pantalla lo resolviera por su cuenta era una carrera —
        # el mapa se dibujaba antes de que el logo llegara y quedaba el texto.
        logo=paths.LOGO,
        metricas={"toneladas": round(sum(u["toneladas"] for u in todos), 1),
                  "lotes": sum(u["lotes"] for u in todos),
                  "ubicaciones": len(ubis)},
    ))

    # --- las aristas del centro: LOS MOVIMIENTOS ---------------------------
    # Es la parte que más importa. Un traslado sin confirmar en destino son
    # kilos que no están en ningún lado, y acá se ven como lo que son: una
    # flecha que salió y no llegó.
    nombre_a_id = {u["nombre"]: u["id"] for u in semilla.ubicaciones()}
    flujos: dict[tuple, dict] = {}
    for m in movimientos.listar():
        o = nombre_a_id.get(m.get("origen"))
        d = nombre_a_id.get(m.get("destino"))
        if not o or not d or o == d:
            continue
        # campo→planta y planta→cámara no son un corredor del cuadro
        if o in ids_planta or d in ids_planta:
            continue
        k = (o, d)
        f = flujos.setdefault(k, {"kg": 0.0, "n": 0, "en_transito": 0,
                                  "kg_transito": 0.0, "numeros": []})
        f["kg"] += float(m.get("kg") or 0)
        f["n"] += 1
        if m.get("estado") == "en_transito":
            f["en_transito"] += 1
            f["kg_transito"] += float(m.get("kg") or 0)
            f["numeros"].append(m.get("numero"))

    for (o, d), f in flujos.items():
        aristas.append(_arista(
            f"ubi:{o}", f"ubi:{d}", "movimiento",
            kg=round(f["kg"], 1), movimientos=f["n"],
            en_transito=f["en_transito"],
            kg_en_transito=round(f["kg_transito"], 1),
            numeros_en_transito=f["numeros"],
            # el flag que la pantalla usa para puntear y pulsar la flecha
            alerta=f["en_transito"] > 0,
        ))
    return nodos, aristas


# ---------------------------------------------------------------------------
# ORIGEN — de dónde sale cada kilo
# ---------------------------------------------------------------------------
def _origen(arts: list[dict], via_planta: bool = False) -> tuple[list[dict], list[dict]]:
    """La escalera de multiplicación, que es lo que hace a esta empresa rara:
    laboratorio in vitro → minitubérculo en El Calafate → campo → cámara."""
    nodos, aristas = [], []

    # El laboratorio no es un dato del dataset: es la primera etapa real del
    # ciclo (cultivo de meristemas apicales) y sin él la escalera arranca en el
    # aire. Se deriva de los lotes de categoría Preinicial, que son sus hijos.
    preiniciales = [a for a in arts if "Preinicial" in str(a.get("categoria_semilla"))]
    nodos.append(_nodo(
        "lab:invitro", "laboratorio", "origen", "Laboratorio in vitro",
        subtitulo="Cultivo de meristemas apicales",
        metricas={"lotes": len(preiniciales),
                  "kg": round(sum(float(a.get("stock") or 0) for a in preiniciales), 1)},
        detalle="Donde arranca la escalera: de acá salen las categorías "
                "Preiniciales, con tolerancia de virus cero.",
    ))

    # Los campos, con los kilos que hoy están en cámara viniendo de cada uno.
    por_campo: dict[str, dict] = {}
    for a in arts:
        c = a.get("campo_origen") or "—"
        g = por_campo.setdefault(c, {"kg": 0.0, "lotes": 0, "zona": a.get("zona_origen"),
                                     "ubis": {}})
        g["kg"] += float(a.get("stock") or 0)
        g["lotes"] += 1
        if a.get("ubicacion_id"):
            g["ubis"][a["ubicacion_id"]] = (g["ubis"].get(a["ubicacion_id"], 0.0)
                                            + float(a.get("stock") or 0))

    catalogo = {c["nombre"]: c for c in semilla.campos()}
    for nombre, g in sorted(por_campo.items(), key=lambda kv: -kv[1]["kg"]):
        meta = catalogo.get(nombre, {})
        patagonia = "Patagonia" in str(g["zona"])
        nid = f"campo:{meta.get('id') or nombre}"
        nodos.append(_nodo(
            nid, "campo", "origen", nombre,
            subtitulo=g["zona"],
            metricas={"lotes": g["lotes"], "toneladas": round(g["kg"] / 1000, 1),
                      "hectareas": meta.get("ha"), "rinde": meta.get("rinde")},
            detalle=("Aislamiento sanitario: heladas y viento extremo, sin áfidos "
                     "vectores. Por eso el material de categoría alta se multiplica acá."
                     if patagonia else None),
        ))
        # Si la planta está en el mapa, el campo NO salta a la cámara: el kilo
        # pasa por planta. Esas aristas las arma `_planta_y_galpones`.
        if not via_planta:
            principal = max(g["ubis"].items(), key=lambda kv: kv[1])[0] if g["ubis"] else None
            for uid, kg in sorted(g["ubis"].items(), key=lambda kv: -kv[1]):
                aristas.append(_arista(nid, f"ubi:{uid}", "ingreso",
                                       kg=round(kg, 1), principal=(uid == principal)))
        if patagonia:
            aristas.append(_arista("lab:invitro", nid, "multiplicacion"))

    # POR QUÉ NO ESTÁN LAS CAMPAÑAS NI LAS VARIEDADES.
    # Estaban, y eran catorce cajas en la columna izquierda SIN UNA SOLA LÍNEA:
    # una campaña no "alimenta" una cámara, y una variedad tampoco. Nodos
    # huérfanos en un mapa de flujo se leen como un error de dibujo, no como
    # información. La campaña y la variedad de cada lote viven donde sirven —
    # en el panel de la ubicación (agrupado por variedad) y en la trazabilidad.

    return nodos, aristas


# ---------------------------------------------------------------------------
# DESTINO — adónde va, y con qué papeles
# ---------------------------------------------------------------------------
def _destino(arts: list[dict]) -> tuple[list[dict], list[dict]]:
    nodos, aristas = [], []
    por_cod = {a.get("codigo"): a for a in arts}
    ordenes = ordenes_carga.pendientes_con_estado()

    clientes_vivos: dict[str, dict] = {}
    for o in ordenes:
        nid = f"orden:{o['numero']}"
        bloqueada = not o.get("puede_emitirse")
        nodos.append(_nodo(
            nid, "orden", "destino", o["numero"],
            subtitulo=o.get("cliente"),
            estado="rojo" if bloqueada else "verde",
            metricas={"kg": o.get("kg_total"), "bultos": o.get("bolsones_total"),
                      "bloqueos": len(o.get("bloqueos") or [])},
            bloqueada=bloqueada,
            tipo_orden=o.get("tipo"),
            motivos=[b["control"] for b in (o.get("bloqueos") or [])],
        ))
        # la orden se abastece de las ubicaciones donde están sus lotes
        for it in o.get("items") or []:
            a = por_cod.get(it.get("codigo")) or {}
            if a.get("ubicacion_id"):
                aristas.append(_arista(
                    f"ubi:{a['ubicacion_id']}", nid, "compromiso",
                    kg=it.get("kg"), lote=it.get("lote"), alerta=bloqueada))
        cid = o.get("cliente_id") or o.get("cliente")
        if cid:
            c = clientes_vivos.setdefault(cid, {"nombre": o.get("cliente"),
                                                "tipo": o.get("tipo"),
                                                "pais": o.get("pais"),
                                                "kg": 0.0, "ordenes": 0})
            c["kg"] += float(o.get("kg_total") or 0)
            c["ordenes"] += 1
            aristas.append(_arista(nid, f"cliente:{cid}", "destino"))

    cat_cli = {c["id"]: c for c in semilla.clientes()}
    paises: dict[str, float] = {}
    for cid, c in sorted(clientes_vivos.items(), key=lambda kv: -kv[1]["kg"]):
        meta = cat_cli.get(cid, {})
        nodos.append(_nodo(
            f"cliente:{cid}", "cliente", "destino", c["nombre"],
            subtitulo=c.get("pais"),
            metricas={"kg": round(c["kg"], 1), "ordenes": c["ordenes"]},
            exportacion=c.get("tipo") == "exportacion",
            incoterm=meta.get("incoterm"),
            puerto=meta.get("puerto"),
            requisitos_onpf=meta.get("requisitos_onpf") or [],
        ))
        if meta.get("puerto"):
            pid = f"puerto:{meta['puerto']}"
            if not any(n["id"] == pid for n in nodos):
                nodos.append(_nodo(pid, "puerto", "destino", meta["puerto"]))
            aristas.append(_arista(f"cliente:{cid}", pid, "embarque"))
            if c.get("pais"):
                paises[c["pais"]] = paises.get(c["pais"], 0.0) + c["kg"]
                aristas.append(_arista(pid, f"pais:{c['pais']}", "envio"))
        elif c.get("pais"):
            paises[c["pais"]] = paises.get(c["pais"], 0.0) + c["kg"]
            aristas.append(_arista(f"cliente:{cid}", f"pais:{c['pais']}", "envio"))

    for p, kg in sorted(paises.items(), key=lambda kv: -kv[1]):
        nodos.append(_nodo(f"pais:{p}", "pais", "destino", p,
                           metricas={"kg": round(kg, 1)}))
    return nodos, aristas


# ---------------------------------------------------------------------------
# Los hallazgos, con el CAMINO que hay que iluminar
# ---------------------------------------------------------------------------
def hallazgos() -> list[dict]:
    """Lo que hay que mirar, cada uno con la lista de nodos y aristas que
    forman su camino. La pantalla ilumina ese camino y atenúa el resto: el
    hallazgo deja de ser un cartel y pasa a ser un recorrido."""
    out = []
    nombre_a_id = {u["nombre"]: u["id"] for u in semilla.ubicaciones()}
    arts = {a.get("codigo"): a for a in store.raw_actual()}

    # 1) los kilos en el aire
    for m in movimientos.sin_confirmar():
        o = nombre_a_id.get(m.get("origen"))
        d = nombre_a_id.get(m.get("destino"))
        if not o or not d:
            continue
        out.append({
            "id": f"transito:{m['numero']}",
            "clase": "movimiento_sin_confirmar",
            "titulo": f"{m['numero']} · {m['kg']:,.0f} kg sin confirmar".replace(",", "."),
            "detalle": (f"Salió de {m['origen']} hacia {m['destino']} hace "
                        f"{m['dias_en_transito']} días y nadie confirmó que llegó."),
            "camino": {"nodos": [_sid(f"ubi:{o}"), _sid(f"ubi:{d}")],
                       "aristas": [_arista(f"ubi:{o}", f"ubi:{d}", "movimiento")["id"]]},
            "accion": {"tipo": "confirmar_movimiento", "numero": m["numero"]},
            "seccion": "movimientos",
        })

    # 2) las diferencias de conteo
    for dif in conciliacion.abiertas():
        uid = dif.get("ubicacion_id")
        cam = [_sid(f"ubi:{uid}")] if uid else []
        ev = (dif["hipotesis"].get("evidencia") or {}).get("movimiento")
        aristas_cam = []
        if ev:
            o = nombre_a_id.get(ev.get("origen"))
            d = nombre_a_id.get(ev.get("destino"))
            if o and d:
                cam = [_sid(f"ubi:{o}"), _sid(f"ubi:{d}")]
                aristas_cam = [_arista(f"ubi:{o}", f"ubi:{d}", "movimiento")["id"]]
        out.append({
            "id": f"dif:{dif['numero']}",
            "clase": dif["hipotesis"]["clase"],
            "titulo": (f"{dif['lote']} · {abs(dif['diferencia_kg']):,.0f} kg "
                       f"{dif['signo']}").replace(",", "."),
            "detalle": dif["hipotesis"]["texto"],
            "camino": {"nodos": cam, "aristas": aristas_cam},
            "seccion": "conciliacion",
        })

    # 3) las órdenes frenadas
    for o in ordenes_carga.pendientes_con_estado():
        if o.get("puede_emitirse"):
            continue
        nodos_cam = [_sid(f"orden:{o['numero']}")]
        for it in o.get("items") or []:
            a = arts.get(it.get("codigo")) or {}
            if a.get("ubicacion_id"):
                nodos_cam.append(_sid(f"ubi:{a['ubicacion_id']}"))
        cid = o.get("cliente_id") or o.get("cliente")
        if cid:
            nodos_cam.append(_sid(f"cliente:{cid}"))
        out.append({
            "id": f"orden:{o['numero']}",
            "clase": "orden_bloqueada",
            "titulo": f"{o['numero']} frenada · {o.get('cliente')}",
            "detalle": ", ".join(b["control"].replace("_", " ")
                                 for b in (o.get("bloqueos") or [])),
            "camino": {"nodos": nodos_cam, "aristas": []},
            "seccion": "logistica",
        })

    # 4) lo que se está por brotar, por ubicación
    h = hoy()
    riesgo: dict[str, dict] = {}
    for a in store.raw_actual():
        b = parse_fecha(a.get("brotacion_estimada"))
        if not b or float(a.get("stock") or 0) <= 0:
            continue
        dd = (b - h).days
        if 0 < dd <= VENTANA_BROTACION_DIAS and a.get("ubicacion_id"):
            g = riesgo.setdefault(a["ubicacion_id"], {"lotes": 0, "valor": 0.0, "min": dd})
            g["lotes"] += 1
            g["valor"] += float(a.get("stock") or 0) * float(a.get("costo_iva") or 0)
            g["min"] = min(g["min"], dd)
    for uid, g in riesgo.items():
        u = semilla.ubicacion(uid) or {}
        nid = uid if u.get("tipo") == "planta" else f"ubi:{uid}"
        out.append({
            "id": f"brotacion:{uid}",
            "clase": "brotacion",
            "titulo": f"{g['lotes']} lotes se brotan en {u.get('nombre', uid)}",
            "detalle": (f"El primero en {g['min']} días. Son "
                        f"${g['valor']:,.0f} que dejan de ser semilla de su "
                        f"categoría.").replace(",", "."),
            "camino": {"nodos": [_sid(nid)], "aristas": []},
            "seccion": "deposito",
        })
    return out


# ---------------------------------------------------------------------------
# PLANTA Y GALPONES NUEVOS — se SUMAN al mapa viejo, no lo reemplazan
# ---------------------------------------------------------------------------
def _es_galpon(item: dict) -> bool:
    nombre = (item.get("nombre") or "").lower()
    ident = (item.get("id") or "").lower()
    return (item.get("tipo") == "galpon"
            or "galpón" in nombre or "galpon" in nombre or "galpon" in ident)


def _nodo_planta_seed(planta: dict, arts: list[dict], conc: dict | None) -> dict:
    """Nodo de planta con los kilos del seed viejo (mismo universo que Sierra)."""
    lotes = [a for a in arts if a.get("ubicacion_id") == planta["id"]]
    kg = float((conc or {}).get("kg") or 0)
    if not kg:
        kg = sum(float(a.get("stock") or 0) for a in lotes)
    por_var: dict[str, dict] = {}
    for a in lotes:
        v = a.get("variedad") or "—"
        g = por_var.setdefault(v, {"lotes": 0, "kg": 0.0, "id": a.get("variedad_id")})
        g["lotes"] += 1
        g["kg"] += float(a.get("stock") or 0)
    return _nodo(
        planta["id"], "planta", "centro", planta["nombre"],
        subtitulo="Recepción · reclasificación · playa",
        estado=(conc or {}).get("estado") or "verde",
        metricas={
            "kg": round(kg, 1),
            "toneladas": round(kg / 1000, 1),
            "lotes": (conc or {}).get("lotes") or len(lotes),
            "ocupacion_pct": (conc or {}).get("ocupacion_pct"),
            "valor": (conc or {}).get("valor"),
            "diferencias": (conc or {}).get("diferencias_abiertas") or 0,
            "por_brotar": len((conc or {}).get("por_brotar_45d") or []),
            "ya_brotados": (conc or {}).get("ya_brotados") or 0,
        },
        tipo_sitio="planta",
        zonas=planta.get("zonas") or [],
        camaras=planta.get("camaras") or [],
        grupos=[{"id": f"grp:planta:{g.get('id') or v}",
                 "variedad": v, "lotes": g["lotes"], "kg": round(g["kg"], 1)}
                for v, g in sorted(por_var.items(), key=lambda kv: -kv[1]["kg"])],
        detalle="El hub. La mercadería se hace en el campo, se recibe acá, y de acá sale.",
    )


def _galpones_nuevos() -> tuple[list[dict], list[dict]]:
    """Galpón MdP del modelo real, si no está ya en el seed de las 4 cámaras."""
    try:
        from . import modelo_real as M
        from . import stock_real as S
        cat = M.catalogos()
        sitios = S.resumen_sitios()
    except (OSError, KeyError, ValueError):
        return [], []
    nodos, aristas = [], []
    ya = {u["nombre"].casefold() for u in semilla.ubicaciones()}
    frigo_stock = {s["ubicacion_id"]: s for s in (sitios.get("frigorificos") or [])}
    galpones = [f for f in (cat.get("frigorificos") or []) if _es_galpon(f)
                and (f.get("nombre") or "").casefold() not in ya]
    planta_id = None
    seed_planta = next((u for u in semilla.ubicaciones() if u.get("tipo") == "planta"), None)
    if seed_planta:
        planta_id = seed_planta["id"]
    else:
        planta_id = (cat.get("planta") or {}).get("id")
    for g in galpones:
        st = frigo_stock.get(f"frigorifico:{g['id']}") or {}
        kg = float(st.get("kg") or 0)
        nodos.append(_nodo(
            f"galpon:{g['id']}", "galpon", "centro", g["nombre"],
            subtitulo="Galpón · playa de despacho",
            metricas={
                "kg": kg,
                "toneladas": round(kg / 1000, 1),
                "lotes": st.get("lotes") or 0,
                "bolsas": st.get("bolsas") or 0,
            },
            tipo_sitio="galpon",
            grupos=[{"id": f"grp:galpon:{g['id']}:{x['variedad_id']}",
                     "variedad": x["variedad"], "lotes": x["lotes"], "kg": x["kg"]}
                    for x in (st.get("por_variedad") or [])],
        ))
        if planta_id:
            aristas.append(_arista(planta_id, f"galpon:{g['id']}", "desde_planta"))
    return nodos, aristas


def _aristas_campo_planta_camara(planta: dict, arts: list[dict]) -> list[dict]:
    """Campo → planta → las 4 cámaras. Prefiere movimientos reales del seed."""
    aristas = []
    catalogo = {c["nombre"]: c for c in semilla.campos()}
    nombre_a_id = {u["nombre"]: u["id"] for u in semilla.ubicaciones()}
    por_campo: dict[str, float] = {}
    por_ubi: dict[str, float] = {}
    for m in movimientos.listar():
        if m.get("tipo") == "ingreso" and m.get("destino") == planta["nombre"]:
            por_campo[m.get("origen") or "—"] = (
                por_campo.get(m.get("origen") or "—", 0.0) + float(m.get("kg") or 0))
        if m.get("origen") == planta["nombre"]:
            did = nombre_a_id.get(m.get("destino") or "")
            if did and did != planta["id"]:
                por_ubi[did] = por_ubi.get(did, 0.0) + float(m.get("kg") or 0)
    if not por_campo:
        for a in arts:
            c = a.get("campo_origen") or "—"
            por_campo[c] = por_campo.get(c, 0.0) + float(a.get("stock") or 0)
    if not por_ubi:
        for a in arts:
            uid = a.get("ubicacion_id")
            if uid and uid != planta["id"]:
                por_ubi[uid] = por_ubi.get(uid, 0.0) + float(a.get("stock") or 0)
    principal_campo = max(por_campo.items(), key=lambda kv: kv[1])[0] if por_campo else None
    for nombre, kg in por_campo.items():
        meta = catalogo.get(nombre, {})
        nid = f"campo:{meta.get('id') or nombre}"
        aristas.append(_arista(nid, planta["id"], "ingreso",
                               kg=round(kg, 1), principal=(nombre == principal_campo)))
    for u in semilla.ubicaciones():
        if u.get("tipo") == "planta":
            continue
        kg = round(por_ubi.get(u["id"], 0.0), 1)
        if kg <= 0:
            continue
        aristas.append(_arista(planta["id"], f"ubi:{u['id']}", "desde_planta",
                               kg=kg, principal=True))
    return aristas


def _planta_y_galpones(arts: list[dict]) -> tuple[list[dict], list[dict]]:
    """La planta y los galpones nuevos, encima de las 4 cámaras / órdenes /
    clientes. Si hay planta en el seed, los kilos salen de esa misma base
    (no del modelo real, que es otro universo). Si no, se recae al overlay."""
    nodos, aristas = [], []
    conc_planta = next((u for u in conciliacion.por_ubicacion()
                        if u.get("tipo") == "planta"), None)
    planta = next((u for u in semilla.ubicaciones() if u.get("tipo") == "planta"), None)

    if planta:
        nodos.append(_nodo_planta_seed(planta, arts, conc_planta))
        aristas.extend(_aristas_campo_planta_camara(planta, arts))
    else:
        try:
            from . import modelo_real as M
            from . import stock_real as S
            cat = M.catalogos()
            planta_real = cat.get("planta")
            if not planta_real:
                return [], []
            sitios = S.resumen_sitios()
            detalle = S.detalle_planta()
        except (OSError, KeyError, ValueError):
            return [], []
        planta_stock = sitios.get("planta") or {"kg": 0.0, "lotes": 0, "bolsas": 0,
                                                "por_variedad": []}
        nodos.append(_nodo(
            planta_real["id"], "planta", "centro", planta_real["nombre"],
            subtitulo="Recepción · reclasificación · playa",
            metricas={
                "kg": planta_stock.get("kg") or 0.0,
                "toneladas": round((planta_stock.get("kg") or 0) / 1000, 1),
                "lotes": planta_stock.get("lotes") or 0,
                "bolsas": planta_stock.get("bolsas") or 0,
            },
            tipo_sitio="planta",
            zonas=detalle.get("zonas") or planta_real.get("zonas") or [],
            grupos=[{"id": f"grp:planta:{g['variedad_id']}",
                     "variedad": g["variedad"], "lotes": g["lotes"], "kg": g["kg"]}
                    for g in (planta_stock.get("por_variedad") or [])],
            detalle="El hub. La mercadería se hace en el campo, se recibe acá, y de acá sale.",
        ))
        planta = planta_real
        aristas.extend(_aristas_campo_planta_camara(planta, arts))

    n_g, a_g = _galpones_nuevos()
    nodos.extend(n_g)
    aristas.extend(a_g)
    return nodos, aristas


# ---------------------------------------------------------------------------
# El mapa completo
# ---------------------------------------------------------------------------
def mapa() -> dict:
    arts = [a for a in store.raw_actual() if float(a.get("stock") or 0) != 0]
    n_c, a_c = _centro(arts)
    n_p, a_p = _planta_y_galpones(arts)
    n_o, a_o = _origen(arts, via_planta=bool(n_p))
    n_d, a_d = _destino(arts)
    res = conciliacion.resumen()
    return {
        "capas": [
            {"id": "origen", "titulo": "De dónde viene",
             "detalle": "La escalera de multiplicación: laboratorio, campo, campaña."},
            {"id": "centro", "titulo": "Dónde está",
             "detalle": "Las cuatro ubicaciones, la planta y los galpones."},
            {"id": "destino", "titulo": "Adónde va",
             "detalle": "Órdenes, clientes, puerto y la documentación de cada embarque."},
        ],
        "nodos": n_o + n_c + n_p + n_d,
        "aristas": a_o + a_c + a_p + a_d,
        "hallazgos": hallazgos(),
        "resumen": {
            "toneladas": res["toneladas_total"],
            "lotes": res["lotes"],
            "valor": res["valor_total"],
            "ubicaciones": res["ubicaciones"],
            "diferencias": res["diferencias_abiertas"],
            "kg_en_transito": res["kg_en_transito"],
            "movimientos_sin_confirmar": res["movimientos_sin_confirmar"],
        },
    }


# ---------------------------------------------------------------------------
# LA GENEALOGÍA DE UN LOTE — el camino completo, de meristema a contenedor
# ---------------------------------------------------------------------------
def genealogia(texto: str) -> dict:
    """El pedigrí como una LÍNEA DE TIEMPO, no como una ficha.

    Es la respuesta visual a «lo que hacemos nosotros no lo hace nadie»: de qué
    laboratorio salió, en qué campo se multiplicó, por qué cámaras pasó, quién
    lo movió, a quién está prometido y con qué papeles sale. Cada etapa dice su
    fecha y su fuente."""
    ped = trazabilidad_pedigri(texto)
    if not ped.get("encontrado"):
        return ped

    etapas = []
    ident, orig = ped["identidad"], ped["origen"]
    es_preinicial = "Preinicial" in str(ident.get("categoria"))

    if es_preinicial or "Patagonia" in str(orig.get("zona")):
        etapas.append({
            "id": "laboratorio", "tipo": "laboratorio",
            "titulo": "Laboratorio in vitro",
            "detalle": "Cultivo de meristemas apicales. Tolerancia de virus: 0%.",
            "fecha": None, "fuente": f"categoría {ident.get('categoria')}",
        })
    etapas.append({
        "id": "campo", "tipo": "campo",
        "titulo": orig.get("campo"),
        "detalle": (f"{orig.get('zona')} · campaña {ident.get('campania')}"),
        "fecha": None, "fuente": "campo de producción del lote",
        "nota": ("Aislamiento sanitario por heladas y viento extremo."
                 if "Patagonia" in str(orig.get("zona")) else None),
    })
    etapas.append({
        "id": "ingreso", "tipo": "ingreso",
        "titulo": "Ingreso a cámara",
        "detalle": (f"{ident.get('variedad')} · {ident.get('categoria')} · "
                    f"{ident.get('calibre_label')}"),
        "fecha": orig.get("fecha_ingreso"),
        "fuente": "movimiento de ingreso de cosecha",
    })

    san = ped["sanidad"]
    etapas.append({
        "id": "analisis", "tipo": "analisis",
        "titulo": "Análisis sanitario",
        "detalle": (f"PVY {san.get('virus_pct')}% sobre una tolerancia de "
                    f"{san.get('tolerancia_pct')}% · "
                    f"{'dentro de tolerancia' if san.get('dentro_de_tolerancia') else 'FUERA DE TOLERANCIA'}"),
        "fecha": san.get("fecha"),
        "fuente": "análisis de laboratorio",
        "alerta": not san.get("dentro_de_tolerancia"),
    })

    for m in reversed(ped["custodia"]["movimientos"]):
        if m.get("tipo") == "ingreso":
            continue
        etapas.append({
            "id": f"mov:{m.get('numero')}", "tipo": "movimiento",
            "titulo": f"{m.get('tipo').capitalize()} · {m.get('bolsones')} bolsones",
            "detalle": f"{m.get('origen')} → {m.get('destino')}",
            "fecha": m.get("fecha"),
            "fuente": f"{m.get('numero')} · registrado por {m.get('registrado_por')} "
                      f"({m.get('canal')})",
            "alerta": m.get("estado") == "en_transito",
            "nota": ("Sin confirmar en destino: estos kilos no están en ningún lado."
                     if m.get("estado") == "en_transito" else None),
        })

    reloj = ped["reloj"]
    etapas.append({
        "id": "reloj", "tipo": "reloj",
        "titulo": "Brotación estimada",
        "detalle": (f"{reloj.get('conservacion')} · dormancia de "
                    f"{reloj.get('dormancia_natural_dias')} días, "
                    f"{reloj.get('dormancia_efectiva_dias')} con el frío"),
        "fecha": reloj.get("brotacion_estimada"),
        "fuente": "dormancia de la variedad × conservación de la ubicación",
        "alerta": reloj.get("pasado_de_brotacion"),
    })

    for comp in ped["compromisos"]:
        etapas.append({
            "id": f"orden:{comp.get('orden')}", "tipo": "compromiso",
            "titulo": f"{comp.get('orden')} · {comp.get('cliente')}",
            "detalle": (f"{comp.get('kg'):,.0f} kg · {comp.get('tipo')}"
                        f"{' · ' + comp['pais'] if comp.get('pais') else ''}"
                        ).replace(",", "."),
            "fecha": comp.get("fecha"),
            "fuente": "orden de carga",
        })

    return {
        "encontrado": True,
        "codigo": ped["codigo"],
        "lote": ped["lote"],
        "identidad": ident,
        "etapas": etapas,
        "alertas": ped["alertas"],
        "testimonio": ped["testimonio"],
        "disponibilidad": ped["disponibilidad"],
        "fuentes": ped["fuentes"],
    }


def trazabilidad_pedigri(texto: str) -> dict:
    # import diferido: trazabilidad importa conciliacion, que importa este
    # módulo indirectamente en algunos caminos.
    from . import trazabilidad
    return trazabilidad.pedigri(texto)
