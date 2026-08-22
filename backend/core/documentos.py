"""
Documentos entregables — Ángela propone, el usuario edita, recién ahí sale el PDF.

Los dos base (orden de pedido, resumen ejecutivo) se arman desde los datos reales
del negocio y funcionan sin API key. Para documentos libres (una carta a un
proveedor, etc.), el contenido lo genera el modelo (Sonnet) desde el contexto;
acá queda el borrador templado de fallback.
"""
from __future__ import annotations

import datetime

from . import store, anomalias
from . import fechas, paths


def _fecha() -> str:
    return fechas.hoy().strftime("%d/%m/%Y")


def _t(key: str, lang: str | None = None, **params) -> str:
    import i18n
    return i18n.t(key, lang, **params)


def _pi(n: float, lang: str | None = None) -> str:
    """$ entero redondeado — mismo criterio que i18n.pesos, para que el documento
    diga EXACTAMENTE el mismo número que la pantalla y el chat (P18·B).
    Agrupación según idioma (ES $1.234.567 / EN $1,234,567)."""
    crudo = f"{round(n or 0):,}"
    return "$" + (crudo if lang == "en" else crudo.replace(",", "."))


def resumen_ejecutivo(lang: str | None = None) -> dict:
    """P18·B — un executive summary que ANALIZA (pirámide: veredicto primero,
    evidencia después). Composición DETERMINISTA con plantillas interpretativas:
    cada hallazgo cruza ≥2 fuentes ya calculadas, toda acción lleva $, y los
    números son LOS MISMOS de pantalla y chat (misma fuente, analisis/cuentas).
    Si un análisis no se sostiene con datos (piloto sin ventas), NO se escribe."""
    from . import analisis as an
    from . import cuentas as ctas

    pan = store.panorama()
    res = pan["resumen"]
    al = pan.get("alertas", {})
    top = pan["top_inmovilizado"][:10]
    anos = anomalias.analizar_existentes()
    rot = an.rotacion(lang)
    est = an.estacionalidad(lang)
    hay_rot = rot.get("disponible") and rot.get("dormidos_top")

    # --- 1 · Veredicto: la conclusión accionable primero ---
    # (el label de salud va en minúscula: vive a mitad de frase)
    salud_txt = _t(f"core.salud.{res['salud']['nivel']}", lang).lower()
    if hay_rot:
        top5 = sum(x["inmovilizado"] for x in rot["dormidos_top"][:5])
        veredicto = _t("core.doc.veredicto_rot", lang, salud=salud_txt,
                       dormido=_pi(rot["por_estado"]["dormido"], lang),
                       pct=rot["pct_dormido"], top5=_pi(top5, lang))
    else:
        veredicto = _t("core.doc.veredicto_base", lang, salud=salud_txt,
                       inmovilizado=_pi(res["inmovilizado_total"], lang))

    # --- 2 · Los hallazgos que importan (cada uno cruza ≥2 fuentes) ---
    hallazgos = []
    if hay_rot:
        t0 = rot["dormidos_top"][0]
        sin_venta = t0.get("dias_rotacion") is None
        hallazgos.append(_t(
            "core.doc.h_dormido_sin_venta" if sin_venta else "core.doc.h_dormido_lento",
            lang, pct=rot["pct_dormido"], producto=t0["producto"],
            monto=_pi(t0["inmovilizado"], lang),
            dias=round(t0["dias_rotacion"]) if not sin_venta else 0))
    if est.get("disponible") and est.get("categorias"):
        cat, dcat = max(est["categorias"].items(), key=lambda kv: kv[1]["idx_max"])
        import i18n as _i18n
        hallazgos.append(_t("core.doc.h_pico", lang, cat=cat,
                            indice=f"{dcat['idx_max']:.2f}",
                            mes=_i18n.mes_nombre(dcat["pico_max"], lang)))
    morosos = ctas.morosos()
    if morosos:
        tot = ctas.totales()
        peor = morosos[0]
        hallazgos.append(_t("core.doc.h_morosos", lang, n=len(morosos),
                            total=_pi(tot["total_morosos"], lang),
                            nombre=peor["nombre"], atraso=peor["atraso_vs_promedio"]))

    # --- 3 · Qué hacer ahora: acciones con $ y próximo paso ---
    acciones = []
    if hay_rot:
        acciones.append(_t("core.doc.acc_liquidar", lang,
                           monto=_pi(sum(x["inmovilizado"] for x in rot["dormidos_top"][:5]), lang)))
    if morosos:
        acciones.append(_t("core.doc.acc_recordatorio", lang,
                           monto=_pi(ctas.totales()["total_morosos"], lang), n=len(morosos)))
    if al.get("calibre", {}).get("cantidad"):
        acciones.append(_t("core.doc.acc_balanzas", lang, n=al["calibre"]["cantidad"],
                           monto=_pi(al["calibre"]["impacto_pesos"], lang)))
    if al.get("sin_pvp", {}).get("cantidad"):
        acciones.append(_t("core.doc.acc_pvp", lang, n=al["sin_pvp"]["cantidad"],
                           monto=_pi(al["sin_pvp"].get("impacto_pesos") or 0, lang)))
    perdida = next((a for a in anos if a["tipo"] == "precio_perdida"), None)
    if perdida:
        acciones.append(_t("core.doc.accion_perdida", lang, n=perdida["items"],
                           monto=_pi(perdida["impacto_pesos"], lang)))
    if res.get("stock_negativo"):
        acciones.append(_t("core.doc.accion_conteo", lang, n=res["stock_negativo"]))
    if not hay_rot:
        acciones.append(_t("core.doc.accion_cargar", lang))

    # --- 4 · Para vigilar: riesgos honestos que el dato muestra ---
    vigilar = []
    if al.get("calibre", {}).get("cantidad"):
        vigilar.append(_t("core.doc.v_balanzas", lang, n=al["calibre"]["cantidad"]))
    if al.get("costo_viejo", {}).get("cantidad"):
        vigilar.append(_t("core.doc.v_costos", lang, n=al["costo_viejo"]["cantidad"]))
    if res.get("stock_negativo"):
        vigilar.append(_t("core.doc.v_negativos", lang, n=res["stock_negativo"]))

    return {
        "tipo": "resumen_ejecutivo",
        "titulo": _t("core.doc.resumen_titulo", lang),
        "subtitulo": f"{paths.EMPRESA} · {_fecha()}",
        "veredicto": veredicto,
        "hallazgos": hallazgos[:3],
        "kpis": [
            {"label": _t("core.doc.kpi_inmovilizado", lang),
             "valor": _pi(res["inmovilizado_total"], lang)},
            {"label": _t("core.doc.kpi_articulos", lang),
             "valor": str(res["total_articulos"])},
            {"label": _t("core.doc.kpi_problemas", lang),
             "valor": str(res["total_articulos"] - res["con_costo"])},
        ],
        "acciones": acciones[:5],
        "vigilar": vigilar[:3],
        # --- 5 · Anexo de datos: las tablas completas, recién acá ---
        "tablas": [{
            "titulo": _t("core.doc.tabla_top", lang),
            "columnas": [_t("core.doc.col_producto", lang),
                         _t("core.doc.col_stock", lang),
                         _t("core.doc.col_plata", lang)],
            "filas": [[d["descripcion"], str(round(d.get("stock") or 0)),
                       _pi(d.get("inmovilizado") or 0, lang)] for d in top],
        }],
        "anomalias": [{"titulo": a["titulo"], "items": a["items"],
                       "impacto": _pi(a["impacto_pesos"], lang)} for a in anos],
        "nota": _t("core.doc.resumen_nota", lang),
    }


def orden_pedido(proveedor: str | None = None, lang: str | None = None) -> dict:
    raw = store.raw_actual()
    # Reponer lo que está en cero o negativo (y tiene costo).
    faltantes = [d for d in raw if d.get("estado") != "anulado"
                 and (d.get("stock") or 0) <= 0 and d.get("costo_iva")]
    faltantes = sorted(faltantes, key=lambda d: d.get("costo_iva") or 0, reverse=True)[:12]
    # P18·B — cantidad sugerida FUNDADA: con ventas validadas, cobertura de 14
    # días según la demanda real de ese producto (unidades_12m/365 × 14).
    # Sin ventas (piloto): fallback fijo honesto de siempre.
    from . import analisis as an
    u12 = an._unidades_por_codigo(365) if not an._no_disponible(lang) else {}
    items = []
    for d in faltantes:
        u = u12.get(d.get("codigo"))
        if u and u > 0:
            cantidad = max(1, round(u / 365 * 14))
            motivo = _t("core.doc.orden_cobertura", lang, dias=14)
        else:
            cantidad = 10
            motivo = _t("core.doc.orden_sin_stock" if (d.get("stock") or 0) == 0
                        else "core.doc.orden_negativo", lang)
        items.append({"producto": d["descripcion"], "cantidad": cantidad, "unidad": "u",
                      "motivo": motivo, "costo_unitario": d.get("costo_iva")})
    total = sum((it["cantidad"] or 0) * (it["costo_unitario"] or 0) for it in items)
    return {
        "tipo": "orden_pedido",
        "titulo": _t("core.doc.orden_titulo", lang),
        "subtitulo": f"{paths.EMPRESA} · {_fecha()}",
        "proveedor": proveedor or _t("core.doc.orden_proveedor", lang),
        "plazo_pago": _t("core.doc.orden_plazo", lang),
        "items": items,
        "total_estimado": _pi(total, lang) if total else None,
        "nota": _t("core.doc.orden_nota", lang),
    }


def carta_libre(asunto: str, destinatario: str = "", lang: str | None = None) -> dict:
    """Borrador templado de fallback (sin API key). Con el modelo, Sonnet lo redacta fino."""
    return {
        "tipo": "carta",
        "titulo": _t("core.doc.carta_titulo", lang),
        "subtitulo": f"{paths.EMPRESA} · {_fecha()}",
        "destinatario": destinatario or _t("core.doc.carta_destinatario", lang),
        "cuerpo": (f"Estimados,\n\nNos dirigimos a ustedes en relación a: {asunto}.\n\n"
                   f"[Ángela completa el cuerpo con el contexto del negocio cuando se conecta el modelo. "
                   f"Mientras tanto, este es el borrador base para que edites.]\n\n"
                   f"Quedamos a disposición.\n{paths.EMPRESA}"),
        "nota": _t("core.doc.carta_nota", lang),
    }


def generar(tipo: str, params: dict | None = None, lang: str | None = None) -> dict:
    params = params or {}
    if tipo == "resumen_ejecutivo":
        return resumen_ejecutivo(lang)
    if tipo == "orden_pedido":
        return orden_pedido(params.get("proveedor"), lang)
    if tipo == "carta":
        return carta_libre(params.get("asunto", ""), params.get("destinatario", ""), lang)
    raise ValueError(f"tipo de documento desconocido: {tipo}")
