"""
core/objetivos_medidos.py — P36·E4

Objetivos que Ángela MIDE SOLA contra datos que ya existen (no metas escritas a
mano por el dueño). Cada uno es un UMBRAL con:
  · valor ACTUAL   → REAL, computado en vivo del mismo endpoint que ya lo muestra
  · meta + baseline → el umbral y el punto de partida
  · historial      → SINTÉTICO (solo tenant demo, fechas ≤ fecha congelada) para
                     que la barra tenga pasado y se vea la tendencia
El progreso se CALCULA (baseline → actual → meta); nunca se hardcodea. El dueño
no carga nada: abre la app y el objetivo ya avanzó porque el `actual` es el dato
real vivo. Ver OBJETIVOS_SINTETICOS.md para el criterio de lo sintético.

Este módulo NO lee datos: recibe los `actuales` (reales) que arma el endpoint y
sólo aplica la definición + el cálculo. Así el "actual" siempre sale del mismo
lugar que el resto de la app (una sola fuente de verdad).
"""
from __future__ import annotations

# Historial SINTÉTICO: 3 puntos semanales previos (Jun 16 / 23 / 30). El 4º
# punto (la fecha congelada) lo agrega el endpoint con el valor REAL vivo.
# Definiciones: responsable = empleado REAL del demo; `fuente_lk`/`seccion` = de
# qué cruce sale; `direccion` = hacia dónde es "mejor".
DEFS = {
    # LOS SIETE OBJETIVOS SON LOS DEL BRIEF, NO METAS DE OFICINA.
    # Cada uno mide la MISMA cuenta que ya muestra una pantalla —el endpoint le
    # pasa el `actual` vivo—, y cada uno tiene un dueño real del organigrama. El
    # baseline y los tres puntos de historial son SINTÉTICOS (sólo demo, fechas
    # ≤ la fecha congelada): sin pasado la barra no dice si avanza o está
    # estancada. Criterio en OBJETIVOS_SINTETICOS.md.
    "traslados_confirmados": {
        # actual = movimientos.sin_confirmar(). Meta CERO y no "pocos": un
        # traslado sin confirmar en destino son kilos que no están en ningún
        # lado. Es el problema textual del brief.
        "responsable": "ruben", "fuente_lk": "obj.f_movimientos", "seccion": "movimientos",
        "unidad": "traslados", "direccion": "menor", "baseline": 9, "meta": 0,
        "hist": [("2026-08-01", 9), ("2026-08-08", 7), ("2026-08-15", 5)],
    },
    "diferencias_cerradas": {
        # actual = conciliacion.abiertas(). Meta cero: una diferencia que queda
        # abierta dos semanas ya no se puede reconstruir.
        "responsable": "ruben", "fuente_lk": "obj.f_conciliacion", "seccion": "conciliacion",
        "unidad": "diferencias", "direccion": "menor", "baseline": 12, "meta": 0,
        "hist": [("2026-08-01", 12), ("2026-08-08", 9), ("2026-08-15", 6)],
    },
    "ordenes_sin_bloqueo": {
        # actual = órdenes de carga que HOY no pueden emitirse. Meta cero: el
        # camión en la playa con el cliente esperando es el papelón que este
        # sistema vino a evitar.
        "responsable": "cecilia", "fuente_lk": "obj.f_ordenes", "seccion": "logistica",
        "unidad": "ordenes", "direccion": "menor", "baseline": 5, "meta": 0,
        "hist": [("2026-08-01", 5), ("2026-08-08", 4), ("2026-08-15", 2)],
    },
    "analisis_vigentes": {
        # actual = lotes de exportación con el DAS-ELISA fuera de la ventana de
        # vigencia. Sin análisis vigente el SENASA no emite el fitosanitario.
        "responsable": "dalia", "fuente_lk": "obj.f_analisis", "seccion": "trazabilidad",
        "unidad": "lotes", "direccion": "menor", "baseline": 33, "meta": 0,
        "hist": [("2026-08-01", 33), ("2026-08-08", 27), ("2026-08-15", 20)],
    },
    "brotacion_ventana": {
        # actual = lotes que se brotan adentro de la ventana de 45 días. Meta
        # cero: un lote que brota antes de despacharse deja de ser semilla de su
        # categoría, y eso no se recupera.
        "responsable": "ruben", "fuente_lk": "obj.f_brotacion", "seccion": "deposito",
        "unidad": "lotes", "direccion": "menor", "baseline": 21, "meta": 0,
        "hist": [("2026-08-01", 21), ("2026-08-08", 16), ("2026-08-15", 11)],
    },
    "galpon_liviano": {
        # actual = lotes parados en el galpón, que no tiene frío. Meta 3: el
        # galpón es TRÁNSITO, no depósito — ahí la dormancia corre a reloj
        # natural y la semilla se brota mucho antes que en cámara.
        "responsable": "nestor", "fuente_lk": "obj.f_galpon", "seccion": "deposito",
        "unidad": "lotes", "direccion": "menor", "baseline": 24, "meta": 3,
        "hist": [("2026-08-01", 24), ("2026-08-08", 18), ("2026-08-15", 13)],
    },
    "datos_corregir": {
        # actual = los registros del libro triado (los mismos 17 del badge).
        "responsable": "dalia", "fuente_lk": "obj.f_saneamiento", "seccion": "saneamiento",
        "unidad": "registros", "direccion": "menor", "baseline": 44, "meta": 0,
        "hist": [("2026-08-01", 44), ("2026-08-08", 34), ("2026-08-15", 26)],
    },
}
ORDEN = ["traslados_confirmados", "diferencias_cerradas", "ordenes_sin_bloqueo",
         "analisis_vigentes", "brotacion_ventana", "galpon_liviano", "datos_corregir"]

# El umbral de cobertura que define "por quebrar" — el MISMO que
# oportunidades_neg.COBERTURA_QUIEBRE_DIAS, para que el objetivo y el hallazgo
# no cuenten cosas distintas.
COBERTURA_QUIEBRE_DIAS = 14


def _nombre_de(username: str) -> str:
    try:
        import usuarios_papasud
        return usuarios_papasud.USUARIOS.get(username, {}).get("nombre") or username.capitalize()
    except Exception:
        return username.capitalize()


def _progreso(baseline, actual, meta, direccion):
    rango = abs(baseline - meta) or 1
    avance = (baseline - actual) if direccion == "menor" else (actual - baseline)
    return max(0.0, min(1.0, avance / rango))


def _estado(d, actual, progreso):
    """avanza | estancado | cumplido. Estancado = el último tramo (vs el punto
    sintético más reciente) casi no se movió (o retrocedió)."""
    if progreso >= 0.999:
        return "cumplido"
    prev = d["hist"][-1][1]
    rango = abs(d["baseline"] - d["meta"]) or 1
    mejora = (prev - actual) if d["direccion"] == "menor" else (actual - prev)
    if mejora < 0.02 * rango:
        return "estancado"
    return "avanza"


def construir(actuales: dict, hoy_iso: str) -> list[dict]:
    """`actuales` = {id: valor REAL vivo} (ya normalizado por el endpoint, en las
    mismas unidades que baseline/meta). Devuelve los objetivos con progreso,
    estado e historial (los 3 puntos sintéticos + el actual real de hoy)."""
    out = []
    for oid in ORDEN:
        d = DEFS[oid]
        if oid not in actuales or actuales[oid] is None:
            continue
        actual = actuales[oid]
        prog = _progreso(d["baseline"], actual, d["meta"], d["direccion"])
        serie = [{"fecha": f, "valor": v} for f, v in d["hist"]]
        serie.append({"fecha": hoy_iso, "valor": actual})
        out.append({
            "id": oid, "responsable": d["responsable"],
            # El NOMBRE, no el username: "Ruben" con la e sin tilde en la ficha
            # de una persona real se lee como un dato mal cargado.
            "responsable_nombre": _nombre_de(d["responsable"]),
            "fuente_lk": d["fuente_lk"],
            "seccion": d["seccion"], "unidad": d["unidad"], "direccion": d["direccion"],
            "baseline": d["baseline"], "meta": d["meta"], "actual": actual,
            "progreso": round(prog, 3), "estado": _estado(d, actual, prog),
            "historial": serie,
        })
    return out


def resumen(objs: list[dict]) -> dict:
    """Para la cabecera del panel: activos, cuántos avanzaron esta semana, y cuál
    está más cerca de cumplirse."""
    activos = [o for o in objs if o["estado"] != "cumplido"]
    avanzaron = [o for o in objs if o["estado"] == "avanza"]
    mas_cerca = max(objs, key=lambda o: o["progreso"], default=None)
    return {
        "activos": len(activos),
        "avanzaron": len(avanzaron),
        "mas_cerca": mas_cerca["id"] if mas_cerca else None,
        "mas_cerca_pct": round(mas_cerca["progreso"] * 100) if mas_cerca else 0,
    }
