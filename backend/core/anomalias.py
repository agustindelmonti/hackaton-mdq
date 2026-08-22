"""
Anomalías sobre los datos QUE YA ESTÁN CARGADOS — arreglar el pasado.

La diferencia con «Errores en tu sistema» (que mira campos incompletos de cada
registro) es el alcance: acá se cruzan registros entre sí y contra la historia.
Papasud viene de años de planilla compartida, y una planilla no tiene forma de
avisar que un traslado quedó a mitad de camino, que un conteo se abrió y nadie
lo cerró, o que un lote perdió la categoría con la que sigue rotulado.

EL PATRÓN ES EL DE SIEMPRE: lo encuentra el código, Ángela lo explica, la
persona aprueba la corrección. Ninguna de estas anomalías se corrige sola.

POR QUÉ SE FUE «STOCK ANORMALMENTE ALTO».
Era el detector de un almacén: más de 10.000 unidades de un artículo es raro
cuando vendés paquetes de fideos. Acá la unidad es el kilo y CIENTO TREINTA Y
OCHO de los 147 lotes tienen más de 10.000 kg — es lo normal en una cámara. El
detector marcaba el 94% del catálogo y decía "$3.368M en juego". Una alerta que
se dispara siempre no es una alerta: es ruido que entrena a la gente a ignorar
la pantalla. En su lugar hay cinco detectores que sí saben de qué hablan.
"""
from __future__ import annotations

import unicodedata

from . import store, valorizacion
from .fechas import hoy, parse_fecha

# Un traslado que salió y nadie confirmó en destino: a partir de acá deja de ser
# "está en camino" y pasa a ser un agujero. Es el mismo umbral que usa el
# encargado para salir a preguntar.
DIAS_TRASLADO_HUERFANO = 7

# Un conteo que abrió una diferencia y quedó ahí. Dos semanas es el punto donde
# ya no se puede reconstruir qué pasó: el que contó no se acuerda.
DIAS_CONTEO_SIN_CERRAR = 14

# Los campos SIN LOS CUALES un lote no se puede certificar ni exportar. No es
# una preferencia de diseño: el formulario del INASE los pide.
CAMPOS_TRAZABILIDAD = ("campo_origen", "campania", "categoria_semilla", "variedad")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def _vivos(raw):
    return [d for d in raw if float(d.get("stock") or 0) > 0]


def _valor(items) -> float:
    return round(sum(float(d.get("stock") or 0) * float(d.get("costo_iva") or 0)
                     for d in items), 2)


def _perdida(raw):
    # Consciente de unidad: para un lote por peso compara $/kg vs $/kg, para
    # uno normal $/u vs $/u. Nunca cruza unidades. Ver core/valorizacion.py.
    return [d for d in raw if valorizacion.es_a_perdida(d)]


def _duplicados(raw):
    grupos = {}
    for d in raw:
        grupos.setdefault(_norm(d.get("lote") or d.get("descripcion")), []).append(d)
    return [d for k, items in grupos.items() if k and len(items) > 1 for d in items]


def _trazabilidad_incompleta(raw):
    """Lotes con kilos y con algún campo del pedigrí en blanco."""
    return [d for d in _vivos(raw)
            if any(not str(d.get(c) or "").strip() for c in CAMPOS_TRAZABILIDAD)]


def _sin_analisis(raw):
    """Lotes con kilos sin análisis sanitario aprobado.

    Sin DAS-ELISA aprobado el lote no puede salir como semilla fiscalizada de su
    categoría: el certificado del SENASA lo pide y el rótulo del INASE declara
    la tolerancia de virus."""
    return [d for d in _vivos(raw)
            if str(d.get("analisis_estado") or "").lower() not in ("aprobado", "vigente")]


def _categoria_perdida(raw):
    """Lotes YA BROTADOS que siguen declarados con su categoría.

    Un tubérculo que brotó dejó de ser semilla de esa categoría — el rótulo
    dice una cosa y la bolsa tiene otra. Es la anomalía más cara del catálogo
    porque la descubre el cliente, no la planilla."""
    h = hoy()
    out = []
    for d in _vivos(raw):
        b = parse_fecha(d.get("brotacion_estimada"))
        if b and b < h and str(d.get("categoria_semilla") or "").strip():
            out.append(d)
    return out


def _traslados_huerfanos():
    """Traslados que salieron de una cámara y nadie confirmó en la otra."""
    from . import movimientos
    try:
        return [m for m in movimientos.sin_confirmar()
                if (m.get("dias_en_transito") or 0) >= DIAS_TRASLADO_HUERFANO]
    except Exception:
        return []


def _conteos_sin_cerrar():
    """Diferencias de conteo abiertas hace más de dos semanas."""
    from . import conciliacion
    h = hoy()
    out = []
    try:
        for c in conciliacion.abiertas():
            f = parse_fecha(c.get("fecha"))
            if f and (h - f).days >= DIAS_CONTEO_SIN_CERRAR:
                out.append(c)
    except Exception:
        pass
    return out


def analizar_existentes() -> list[dict]:
    raw = store.raw_actual()
    out = []

    perdida = _perdida(raw)
    if perdida:
        loss = round(sum((d["costo_iva"] - d["pvp"]) * (d.get("stock") or 0) for d in perdida), 2)
        out.append({
            "tipo": "precio_perdida", "titulo": "Lotes cotizados por debajo del costo",
            "descripcion": f"{len(perdida)} lotes figuran con el costo de producción más alto "
                           f"que el precio de venta. Casi siempre es un error de carga (costo "
                           f"con IVA contra precio sin IVA, o un precio de la campaña pasada). "
                           f"Conviene revisarlo con Ángela, no ponerle un margen a ciegas.",
            "items": len(perdida), "impacto_pesos": loss,
            "codigos": [d.get("codigo") for d in perdida],
        })

    brotados = _categoria_perdida(raw)
    if brotados:
        out.append({
            "tipo": "categoria_perdida", "titulo": "Lotes brotados que siguen con su categoría",
            "descripcion": f"{len(brotados)} lotes ya pasaron su fecha de brotación y siguen "
                           f"declarados con la categoría del rótulo. Un tubérculo brotado dejó "
                           f"de ser semilla de esa categoría: el rótulo dice una cosa y la bolsa "
                           f"tiene otra. Hay que recategorizarlos o darlos de baja como semilla.",
            "items": len(brotados), "impacto_pesos": _valor(brotados),
            "codigos": [d.get("codigo") for d in brotados],
        })

    sin_traza = _trazabilidad_incompleta(raw)
    if sin_traza:
        out.append({
            "tipo": "trazabilidad_incompleta", "titulo": "Lotes sin el pedigrí completo",
            "descripcion": f"{len(sin_traza)} lotes con kilos en cámara tienen algún campo del "
                           f"origen en blanco (campo, campaña, categoría o variedad). Sin eso no "
                           f"se puede completar la solicitud del INASE ni el fitosanitario: "
                           f"el lote existe pero no se puede vender como semilla fiscalizada.",
            "items": len(sin_traza), "impacto_pesos": _valor(sin_traza),
            "codigos": [d.get("codigo") for d in sin_traza],
        })

    sin_an = _sin_analisis(raw)
    if sin_an:
        out.append({
            "tipo": "sin_analisis", "titulo": "Lotes sin análisis sanitario aprobado",
            "descripcion": f"{len(sin_an)} lotes con kilos no tienen un DAS-ELISA aprobado. "
                           f"El rótulo del INASE declara una tolerancia de virus por categoría "
                           f"y el certificado del SENASA la pide: sin el análisis, esos kilos no "
                           f"salen del país y tampoco deberían salir como semilla de su categoría.",
            "items": len(sin_an), "impacto_pesos": _valor(sin_an),
            "codigos": [d.get("codigo") for d in sin_an],
        })

    huerfanos = _traslados_huerfanos()
    if huerfanos:
        kg = sum(float(m.get("kg") or 0) for m in huerfanos)
        out.append({
            "tipo": "traslado_huerfano", "titulo": "Traslados que quedaron a mitad de camino",
            "descripcion": f"{len(huerfanos)} traslados salieron de una cámara hace más de "
                           f"{DIAS_TRASLADO_HUERFANO} días y nadie confirmó que llegaran. "
                           f"Son {kg:,.0f} kg que no están en ningún lado: ni en el origen, que "
                           f"ya los descontó, ni en el destino, que nunca los sumó. Ahí nacen "
                           f"las diferencias que aparecen el día que carga el camión."
                           .replace(",", "."),
            "items": len(huerfanos), "impacto_pesos": 0.0,
            "codigos": [m.get("numero") for m in huerfanos],
        })

    viejos = _conteos_sin_cerrar()
    if viejos:
        out.append({
            "tipo": "conteo_sin_cerrar", "titulo": "Conteos que nunca cerraron",
            "descripcion": f"{len(viejos)} diferencias de conteo llevan más de "
                           f"{DIAS_CONTEO_SIN_CERRAR} días abiertas. Pasado ese tiempo ya nadie "
                           f"se acuerda de qué pasó esa mañana: o se recuenta la cámara o se "
                           f"acepta el ajuste, pero dejarlas abiertas las vuelve permanentes.",
            "items": len(viejos), "impacto_pesos": 0.0,
            "codigos": [c.get("numero") for c in viejos],
        })

    dups = _duplicados(raw)
    if dups:
        out.append({
            "tipo": "duplicado", "titulo": "Posibles lotes duplicados",
            "descripcion": f"{len(dups)} lotes comparten identificador con otro (códigos "
                           f"distintos). Es la firma clásica de la planilla editada por dos "
                           f"personas a la vez, y hace que los mismos kilos se cuenten dos veces.",
            "items": len(dups), "impacto_pesos": round(sum(d.get("inmovilizado") or 0 for d in dups), 2),
            "codigos": [d.get("codigo") for d in dups],
        })

    out.sort(key=lambda g: g["impacto_pesos"], reverse=True)
    return out


def aplicar(tipo: str, accion: str, params: dict | None = None, actor: str = "dueño") -> dict:
    """Aplica una corrección de anomalía en lote sobre los datos existentes, con backup."""
    params = params or {}
    if tipo != "precio_perdida" or accion != "set_margen":
        raise ValueError("Esa anomalía no se corrige automáticamente; revisala en el inventario.")
    raw = store.raw_actual()
    backup = store.versiones.save({"articulos": raw}, motivo="Backup antes de corregir precios a pérdida", autor=actor)
    margen = params.get("margen", 30)
    afectados = _perdida(raw)
    for d in afectados:
        d["pvp"] = round(d["costo_iva"] * (1 + margen / 100), 2)
    store.guardar(raw)
    store.audit.record(actor=actor, accion="corregir_precio_perdida",
                       antes={"afectados": len(afectados)}, despues={"margen": margen, "version_backup": backup["id"]})
    return {"corregidos": len(afectados), "version_backup": backup["id"],
            "mensaje": f"Listo. Le puse un margen del {margen}% a {len(afectados)} lotes que "
                       f"cotizabas por debajo del costo. Guardé un backup por si querés revertir."}
