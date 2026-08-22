"""
trazabilidad.py · El pedigrí de un lote, de la cosecha al contenedor.

Trazabilidad es la palabra que aparece en el título de la vertical y es la que
más pesa para quien audita. Un lote de semilla no es un número de stock: es un
material con un origen, una genealogía de multiplicación, un estado sanitario
firmado por alguien, un domicilio que cambió varias veces y un destino.

Este módulo arma esa historia completa en una sola lectura y de una sola fuente:
todo lo que devuelve sale de los datos, no de un resumen guardado aparte que
pueda quedar desincronizado. Si un movimiento se corrige, el pedigrí cambia solo.

QUÉ RESPONDE, EN EL ORDEN EN QUE LO PREGUNTA UN AUDITOR:

  · IDENTIDAD    — qué es: variedad, categoría INASE y clase, campaña, calibre
                   declarado y el rango en milímetros que le corresponde.
  · ORIGEN       — de qué campo salió y en qué zona se multiplicó.
  · SANIDAD      — el análisis, su fecha, el resultado y contra qué tolerancia
                   se lo mide. Si está observado, lo dice.
  · CUSTODIA     — dónde está hoy y dónde estuvo: la cadena completa de
                   movimientos, quién registró cada uno y por qué canal.
  · DISPONIBLE   — cuántos kilos hay de verdad (descontando tránsito y compromisos).
  · RELOJ        — cuándo se estima que brota y cuánto tiempo queda.
  · COMPROMISOS  — a qué cliente está prometido y en qué orden de carga.
  · TESTIMONIO   — qué dijo el equipo sobre este lote (la capa no estructurada).
  · ALERTAS      — qué hay que mirar: rótulo inconsistente, análisis vencido,
                   brotación encima, diferencias de conteo abiertas.

CADA BLOQUE DECLARA SU FUENTE. No es decorativo: es lo que convierte una
pantalla linda en un documento defendible frente a alguien que pregunta de dónde
sale cada dato.
"""
from __future__ import annotations

from . import conciliacion, esquema, movimientos, notas, semilla, store
from .fechas import hoy, parse_fecha


def _art(texto: str) -> dict | None:
    """El lote, buscado como lo nombraría una persona. Si es ambiguo, None."""
    cands = movimientos.buscar_lote(texto)
    if len(cands) == 1:
        return cands[0]
    # con varios candidatos, sólo resuelve si uno matchea el rótulo exacto
    t = (texto or "").strip().upper()
    exacto = [c for c in cands if str(c.get("lote", "")).upper() == t]
    return exacto[0] if exacto else None


def pedigri(texto: str) -> dict:
    """La historia completa del lote. `fuentes` dice de dónde sale cada bloque."""
    art = _art(texto)
    if not art:
        cands = movimientos.buscar_lote(texto)
        return {
            "encontrado": False,
            "buscado": texto,
            "candidatos": [{"codigo": c.get("codigo"), "lote": c.get("lote"),
                            "descripcion": c.get("descripcion"),
                            "ubicacion": c.get("ubicacion")} for c in cands[:8]],
        }

    codigo = art["codigo"]
    h = hoy()
    disp = movimientos.disponible(codigo)
    movs = movimientos.listar(lote=art.get("lote"))
    rango = semilla.rango_calibre(art.get("calibre_grado") or 4) or {}

    # --- sanidad ------------------------------------------------------------
    f_an = parse_fecha(art.get("analisis_fecha"))
    dias_an = (h - f_an).days if f_an else None
    virus = art.get("virus_pct")
    virus_max = art.get("virus_max_pct")
    sanidad = {
        "estado": art.get("analisis_estado"),
        "fecha": art.get("analisis_fecha"),
        "dias_desde_analisis": dias_an,
        "virus_pct": virus,
        "tolerancia_pct": virus_max,
        "dentro_de_tolerancia": (virus is not None and virus_max is not None
                                 and virus <= virus_max),
    }

    # --- reloj de brotación -------------------------------------------------
    f_brot = parse_fecha(art.get("brotacion_estimada"))
    dias_brot = (f_brot - h).days if f_brot else None
    reloj = {
        "conservacion": art.get("conservacion"),
        "dormancia_natural_dias": art.get("dormancia_dias"),
        "dormancia_efectiva_dias": art.get("dormancia_efectiva_dias"),
        "brotacion_estimada": art.get("brotacion_estimada"),
        "dias_hasta_brotacion": dias_brot,
        "pasado_de_brotacion": bool(dias_brot is not None and dias_brot <= 0),
    }

    # --- compromisos --------------------------------------------------------
    compromisos = []
    for o in esquema.filas("ordenes_carga"):
        for it in o.get("items") or []:
            if it.get("codigo") == codigo:
                compromisos.append({
                    "orden": o.get("numero"), "cliente": o.get("cliente"),
                    "tipo": o.get("tipo"), "pais": o.get("pais"),
                    "estado": o.get("estado"), "kg": it.get("kg"),
                    "fecha": o.get("fecha"),
                })

    # --- lo que el equipo dijo de este lote ---------------------------------
    testimonio = []
    lote_txt = str(art.get("lote") or "").lower()
    var_txt = str(art.get("variedad") or "").lower()
    cam_txt = str(art.get("camara") or "").lower()
    for n in notas.listar():
        t = str(n.get("texto") or "").lower()
        if lote_txt in t or (var_txt and var_txt in t) or (cam_txt and cam_txt in t):
            testimonio.append(n)

    # --- diferencias de conteo abiertas sobre este lote ---------------------
    difs = [d for d in conciliacion.abiertas() if d["codigo"] == codigo]

    # --- alertas: lo que un auditor marcaría --------------------------------
    alertas = []
    medido = art.get("valor_peso")
    if (art.get("calibrado") and medido is not None
            and rango.get("min_mm") and rango.get("max_mm")
            and (medido < rango["min_mm"] or medido > rango["max_mm"])):
        alertas.append({
            "tipo": "calibre_fuera_de_grado",
            "detalle": (f"El rótulo declara {rango.get('label')} y el calibre medido "
                        f"es {medido} mm: está fuera del rango."),
            "norma": "Res. INASE 171/2000, art. 25",
        })
    if not sanidad["dentro_de_tolerancia"] and virus is not None:
        alertas.append({
            "tipo": "sanidad_fuera_de_tolerancia",
            "detalle": (f"El análisis dio {virus}% y la categoría "
                        f"{art.get('categoria_semilla')} tolera hasta {virus_max}%."),
        })
    if dias_an is not None and dias_an > 180:
        alertas.append({
            "tipo": "analisis_vencido_para_exportacion",
            "detalle": f"El análisis tiene {dias_an} días; para exportar se piden 180 o menos.",
        })
    if reloj["pasado_de_brotacion"]:
        alertas.append({
            "tipo": "pasado_de_brotacion",
            "detalle": (f"La brotación estimada era el {art.get('brotacion_estimada')}: "
                        f"hace {abs(dias_brot)} días."),
        })
    if disp.get("sobrecomprometido"):
        alertas.append({
            "tipo": "sobrecomprometido",
            "detalle": (f"Está prometido en {len(compromisos)} orden(es) por más kilos "
                        f"de los que hay disponibles: faltan "
                        f"{disp['sobrecomprometido_kg']:,.0f} kg.".replace(",", ".")),
        })
    for d in difs:
        alertas.append({
            "tipo": "diferencia_de_conteo",
            "detalle": d["hipotesis"]["texto"],
            "conteo": d["numero"],
        })

    return {
        "encontrado": True,
        "codigo": codigo,
        "lote": art.get("lote"),
        "identidad": {
            "descripcion": art.get("descripcion"),
            "variedad": art.get("variedad"),
            "categoria": art.get("categoria_semilla"),
            "clase": art.get("clase"),
            "campania": art.get("campania"),
            "calibre_grado": art.get("calibre_grado"),
            "calibre_label": rango.get("label"),
            "calibre_medido_mm": medido,
            "calibre_rango_mm": [rango.get("min_mm"), rango.get("max_mm")],
        },
        "origen": {
            "campo": art.get("campo_origen"),
            "zona": art.get("zona_origen"),
            "fecha_ingreso": art.get("fecha_ingreso"),
        },
        "sanidad": sanidad,
        "custodia": {
            "ubicacion": art.get("ubicacion"),
            "camara": art.get("camara"),
            "movimientos": movs,
            "total_movimientos": len(movs),
        },
        "disponibilidad": disp,
        "reloj": reloj,
        "compromisos": compromisos,
        "testimonio": testimonio,
        "diferencias_abiertas": difs,
        "alertas": alertas,
        "fuentes": {
            "identidad": "inventory.json · lote",
            "origen": "inventory.json · campo de producción",
            "sanidad": "inventory.json · análisis de laboratorio",
            "custodia": "apartados.json · movimientos",
            "disponibilidad": "core/movimientos.disponible()",
            "compromisos": "apartados.json · ordenes_carga",
            "testimonio": "notas_equipo.json",
            "diferencias": "apartados.json · conteos + core/conciliacion",
        },
    }


def cadena_de_custodia(texto: str) -> list[dict]:
    """Sólo la cadena: cada paso del lote, en orden cronológico, con quién lo
    hizo. Es lo que se imprime cuando alguien pide "mostrame el recorrido"."""
    art = _art(texto)
    if not art:
        return []
    movs = movimientos.listar(lote=art.get("lote"))
    movs.reverse()   # de la cosecha hacia hoy
    pasos = []
    for m in movs:
        pasos.append({
            "fecha": m.get("fecha"),
            "paso": m.get("tipo"),
            "desde": m.get("origen"),
            "hasta": m.get("destino"),
            "kg": m.get("kg"),
            "bolsones": m.get("bolsones"),
            "por": m.get("registrado_por"),
            "canal": m.get("canal"),
            "estado": m.get("estado"),
            "numero": m.get("numero"),
        })
    return pasos


def resumen() -> dict:
    """Cuán trazable es la operación hoy: cuántos lotes tienen la cadena completa
    y cuántos tienen algún cabo suelto."""
    arts = store.raw_actual()
    con_alerta = 0
    sin_analisis = 0
    for a in arts:
        if not a.get("analisis_fecha"):
            sin_analisis += 1
        f = parse_fecha(a.get("analisis_fecha"))
        if f and (hoy() - f).days > 180:
            con_alerta += 1
    return {
        "lotes": len(arts),
        "con_analisis": len(arts) - sin_analisis,
        "analisis_vencidos_para_exportacion": con_alerta,
        "movimientos_registrados": len(esquema.filas("movimientos")),
        "sin_confirmar_en_destino": len(movimientos.sin_confirmar()),
    }
