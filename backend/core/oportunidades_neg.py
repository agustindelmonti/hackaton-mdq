"""
oportunidades_neg.py · Las oportunidades del negocio de la semilla.

Un set CERRADO de hallazgos serios. Cada uno cruza al menos dos fuentes que hoy
no se hablan, sale entero de cálculo, y trae la plata que hay en juego con el
detalle de cómo se llegó a ese número. Si no hay dato, la card no aparece: el
sistema se calla antes que inventar.

LA REGLA DE INTEGRIDAD (la que más cuesta y la que más vale): cada peso se
cuenta UNA sola vez. Un lote que está por brotar Y además está en una orden
frenada aparece en las dos cards, pero el total de "capital recuperable" no lo
suma dos veces. Por eso cada card declara su `naturaleza`:

    recuperable → plata que se puede volver a poner en circulación
    accionable  → algo que hay que hacer, sin monto propio que sumar
    riesgo      → exposición, NO es plata que entre: es plata que puede salir

Con el dueño de la empresa en la sala, un total inflado por doble conteo se nota
en dos segundos y se lleva puesta la credibilidad de todo lo demás.
"""
from __future__ import annotations

import i18n

from . import conciliacion, esquema, movimientos, ordenes_carga, semilla, store
from .fechas import hoy, parse_fecha

# Cuánto falta para que la brotación sea un problema y no una fecha lejana.
VENTANA_BROTACION_DIAS = 45
# Vigencia del análisis sanitario para exportar (regla de la agrónoma, K-003).
DIAS_ANALISIS_EXPORTACION = 180
# Un lote sin frío en el galpón que lleva más de esto ya está en riesgo.
DIAS_MAX_GALPON = 21

NATURALEZA = {
    "brotacion_inminente": "recuperable",
    "ya_brotado": "recuperable",
    "kilos_en_el_aire": "recuperable",
    "embarque_frenado": "accionable",
    "diferencias_abiertas": "accionable",
    "rotulos_inconsistentes": "accionable",
    "analisis_por_vencer": "accionable",
    "galpon_sin_frio": "accionable",
    "concentracion_exportacion": "riesgo",
}


def _t(key: str, lang: str | None = None, **params) -> str:
    return i18n.t(key, lang, **params)


def _pesos(n, lang):
    return i18n.pesos(n or 0, lang)


def _num(x, lang) -> str:
    return i18n.numero(x, lang) if hasattr(i18n, "numero") else f"{x:,.0f}".replace(",", ".")


def _grafico(nombre, puntos, unidad, temporal, rango=None):
    return {"nombre": nombre, "puntos": puntos, "unidad": unidad,
            "temporal": temporal, "rango": rango}


def _ctx(lang) -> dict:
    """Todo lo que las cards necesitan, calculado UNA vez."""
    arts = store.raw_actual()
    h = hoy()
    for a in arts:
        b = parse_fecha(a.get("brotacion_estimada"))
        a["_dias_brot"] = (b - h).days if b else None
        f = parse_fecha(a.get("analisis_fecha"))
        a["_dias_analisis"] = (h - f).days if f else None
        a["_valor"] = float(a.get("stock") or 0) * float(a.get("costo_iva") or 0)
    return {
        "hoy": h,
        "lang": lang,
        "arts": [a for a in arts if float(a.get("stock") or 0) > 0],
        "ubicaciones": {u["id"]: u for u in semilla.ubicaciones()},
        "conc": conciliacion.resumen(),
        "difs": conciliacion.abiertas(),
        "ordenes": ordenes_carga.pendientes_con_estado(),
        "sin_confirmar": movimientos.sin_confirmar(),
    }


# ---------------------------------------------------------------------------
# 1 · Lo que se está por brotar
# ---------------------------------------------------------------------------
def _card_brotacion(lang, ctx) -> dict | None:
    """La semilla no vence: brota. Y cuando brota deja de ser semilla de su
    categoría, así que el kilo pasa a valer lo que vale una papa de consumo.

    Es el reloj real del negocio y no está en ninguna planilla."""
    en_riesgo = [a for a in ctx["arts"]
                 if a["_dias_brot"] is not None and 0 < a["_dias_brot"] <= VENTANA_BROTACION_DIAS]
    if not en_riesgo:
        return None
    en_riesgo.sort(key=lambda a: a["_dias_brot"])
    total = sum(a["_valor"] for a in en_riesgo)
    kg = sum(float(a.get("stock") or 0) for a in en_riesgo)
    primero = en_riesgo[0]

    puntos = []
    for d in range(0, VENTANA_BROTACION_DIAS + 1, 5):
        v = sum(a["_valor"] for a in en_riesgo if a["_dias_brot"] <= d)
        puntos.append({"x": f"{d}d", "y": round(v, 2)})

    return {
        "id": "brotacion_inminente", "tipo": "despachar",
        "titulo": _t("core.opn.brot_t", lang, n=len(en_riesgo)),
        "monto": round(total, 2),
        "resumen": _t("core.opn.brot_r", lang, lote=primero.get("lote"),
                      dias=primero["_dias_brot"], kg=_num(kg, lang)),
        "accion_chat": _t("core.opn.brot_chat", lang),
        "navegar": "deposito",
        "fuentes": [_t("core.opn.f_lotes", lang), _t("core.opn.f_camaras", lang)],
        "drill": {
            "porque": [
                _t("core.opn.brot_p1", lang, n=len(en_riesgo), dias=VENTANA_BROTACION_DIAS,
                   kg=_num(kg, lang), total=_pesos(total, lang)),
                _t("core.opn.brot_p2", lang, lote=primero.get("lote"),
                   variedad=primero.get("variedad"), dias=primero["_dias_brot"],
                   ubicacion=primero.get("ubicacion")),
            ],
            "grafico": _grafico(_t("core.opn.brot_g", lang), puntos, "$", False),
            "involucrados": [{"nombre": a.get("lote"), "monto": round(a["_valor"], 2),
                              "detalle": _t("core.opn.brot_i", lang, dias=a["_dias_brot"],
                                            ubicacion=a.get("ubicacion"))}
                             for a in en_riesgo[:12]],
            "supuestos": [_t("core.opn.brot_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# 2 · Lo que ya brotó
# ---------------------------------------------------------------------------
def _card_ya_brotado(lang, ctx) -> dict | None:
    """Lo que pasó su fecha y sigue ocupando cámara. No es pérdida total —
    se puede vender como consumo — pero al precio de la semilla ya no."""
    pasados = [a for a in ctx["arts"] if a["_dias_brot"] is not None and a["_dias_brot"] <= 0]
    if not pasados:
        return None
    total = sum(a["_valor"] for a in pasados)
    kg = sum(float(a.get("stock") or 0) for a in pasados)
    pasados.sort(key=lambda a: -a["_valor"])
    por_camp: dict[str, float] = {}
    for a in pasados:
        k = a.get("campania") or "—"
        por_camp[k] = por_camp.get(k, 0.0) + a["_valor"]

    return {
        "id": "ya_brotado", "tipo": "liquidar",
        "titulo": _t("core.opn.brotado_t", lang, n=len(pasados)),
        "monto": round(total, 2),
        "resumen": _t("core.opn.brotado_r", lang, kg=_num(kg, lang),
                      t=round(kg / 1000, 1)),
        "accion_chat": _t("core.opn.brotado_chat", lang),
        "navegar": "inventario",
        "fuentes": [_t("core.opn.f_lotes", lang), _t("core.opn.f_camaras", lang)],
        "drill": {
            "porque": [
                _t("core.opn.brotado_p1", lang, n=len(pasados), t=round(kg / 1000, 1),
                   total=_pesos(total, lang)),
                _t("core.opn.brotado_p2", lang,
                   campanias=", ".join(sorted(por_camp, reverse=True)[:3])),
            ],
            "grafico": _grafico(
                _t("core.opn.brotado_g", lang),
                [{"x": k, "y": round(v, 2)} for k, v in sorted(por_camp.items())],
                "$", False),
            "involucrados": [{"nombre": a.get("lote"), "monto": round(a["_valor"], 2),
                              "detalle": _t("core.opn.brotado_i", lang,
                                            campania=a.get("campania"),
                                            dias=abs(a["_dias_brot"]))}
                             for a in pasados[:12]],
            "supuestos": [_t("core.opn.brotado_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# 3 · Los kilos que no están en ningún lado
# ---------------------------------------------------------------------------
def _card_kilos_en_el_aire(lang, ctx) -> dict | None:
    """Salieron de una cámara y nadie los confirmó en la otra. Es la causa raíz
    del problema del brief y la más barata de arreglar: alguien tiene que ir a
    mirar."""
    abiertos = ctx["sin_confirmar"]
    if not abiertos:
        return None
    por_cod = {a.get("codigo"): a for a in store.raw_actual()}
    total = 0.0
    for m in abiertos:
        a = por_cod.get(m.get("codigo")) or {}
        total += float(m.get("kg") or 0) * float(a.get("costo_iva") or 0)
    kg = sum(float(m.get("kg") or 0) for m in abiertos)
    peor = max(abiertos, key=lambda m: m.get("dias_en_transito") or 0)

    return {
        "id": "kilos_en_el_aire", "tipo": "verificar",
        "titulo": _t("core.opn.aire_t", lang, n=len(abiertos), kg=_num(kg, lang)),
        "monto": round(total, 2),
        "resumen": _t("core.opn.aire_r", lang, numero=peor.get("numero"),
                      dias=peor.get("dias_en_transito"), destino=peor.get("destino")),
        "accion_chat": _t("core.opn.aire_chat", lang),
        "navegar": "movimientos",
        "fuentes": [_t("core.opn.f_movs", lang), _t("core.opn.f_conteos", lang)],
        "drill": {
            "porque": [
                _t("core.opn.aire_p1", lang, n=len(abiertos), kg=_num(kg, lang),
                   total=_pesos(total, lang)),
                _t("core.opn.aire_p2", lang, numero=peor.get("numero"),
                   origen=peor.get("origen"), destino=peor.get("destino"),
                   quien=peor.get("registrado_por"), dias=peor.get("dias_en_transito")),
            ],
            "grafico": None,
            "involucrados": [{"nombre": m.get("lote"),
                              "monto": round(float(m.get("kg") or 0)
                                             * float((por_cod.get(m.get("codigo")) or {})
                                                     .get("costo_iva") or 0), 2),
                              "detalle": _t("core.opn.aire_i", lang,
                                            origen=m.get("origen"), destino=m.get("destino"),
                                            dias=m.get("dias_en_transito"))}
                             for m in abiertos],
            "supuestos": [_t("core.opn.aire_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# 4 · El embarque frenado
# ---------------------------------------------------------------------------
def _card_embarque_frenado(lang, ctx) -> dict | None:
    """Una orden que el sistema no deja emitir. Es la card que más importa: es
    el papelón que NO va a pasar."""
    bloqueadas = [o for o in ctx["ordenes"] if not o.get("puede_emitirse")]
    if not bloqueadas:
        return None
    kg = sum(float(o.get("kg_total") or 0) for o in bloqueadas)
    exportacion = [o for o in bloqueadas if o.get("tipo") == "exportacion"]
    primera = exportacion[0] if exportacion else bloqueadas[0]
    motivos = [b["control"] for o in bloqueadas for b in (o.get("bloqueos") or [])]

    return {
        "id": "embarque_frenado", "tipo": "destrabar",
        "titulo": _t("core.opn.frenado_t", lang, n=len(bloqueadas)),
        "monto": 0.0,   # accionable: no suma al capital recuperable
        "resumen": _t("core.opn.frenado_r", lang, numero=primera.get("numero"),
                      cliente=primera.get("cliente"), kg=_num(primera.get("kg_total"), lang)),
        "accion_chat": _t("core.opn.frenado_chat", lang, numero=primera.get("numero")),
        "navegar": "logistica",
        "fuentes": [_t("core.opn.f_ordenes", lang), _t("core.opn.f_movs", lang),
                    _t("core.opn.f_conteos", lang)],
        "drill": {
            "porque": [
                _t("core.opn.frenado_p1", lang, n=len(bloqueadas), kg=_num(kg, lang)),
                _t("core.opn.frenado_p2", lang, numero=primera.get("numero"),
                   motivos=", ".join(sorted(set(motivos)))),
            ],
            "grafico": None,
            "involucrados": [{"nombre": o.get("numero"), "monto": 0.0,
                              "detalle": _t("core.opn.frenado_i", lang,
                                            cliente=o.get("cliente"),
                                            kg=_num(o.get("kg_total"), lang),
                                            n=len(o.get("bloqueos") or []))}
                             for o in bloqueadas],
            "supuestos": [_t("core.opn.frenado_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# 5 · Las diferencias de conteo abiertas
# ---------------------------------------------------------------------------
def _card_diferencias(lang, ctx) -> dict | None:
    difs = ctx["difs"]
    if not difs:
        return None
    c = ctx["conc"]
    peor = difs[0]
    return {
        "id": "diferencias_abiertas", "tipo": "conciliar",
        "titulo": _t("core.opn.difs_t", lang, n=len(difs)),
        "monto": 0.0,   # el kilo en discusión NO es plata nueva: es plata en duda
        "resumen": _t("core.opn.difs_r", lang, lote=peor.get("lote"),
                      kg=_num(abs(peor.get("diferencia_kg") or 0), lang),
                      plata=_pesos(c.get("plata_en_diferencia"), lang)),
        "accion_chat": _t("core.opn.difs_chat", lang),
        "navegar": "conciliacion",
        "fuentes": [_t("core.opn.f_conteos", lang), _t("core.opn.f_movs", lang),
                    _t("core.opn.f_notas", lang)],
        "drill": {
            "porque": [
                _t("core.opn.difs_p1", lang, n=len(difs),
                   kg=_num(c.get("kg_en_diferencia"), lang),
                   plata=_pesos(c.get("plata_en_diferencia"), lang)),
                _t("core.opn.difs_p2", lang, sin=c.get("sin_explicacion")),
            ],
            "grafico": None,
            "involucrados": [{"nombre": d.get("lote"), "monto": d.get("impacto_pesos"),
                              "detalle": d["hipotesis"]["texto"]}
                             for d in difs],
            "supuestos": [_t("core.opn.difs_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# 6 · Rótulos que no coinciden con el calibre
# ---------------------------------------------------------------------------
def _card_rotulos(lang, ctx) -> dict | None:
    """Un rótulo que declara un grado y un calibre medido que cae afuera. Nadie
    lo mira hasta que el contenedor está en destino."""
    malos = []
    for a in ctx["arts"]:
        medido, ci, cs = a.get("valor_peso"), a.get("cota_inf"), a.get("cota_sup")
        if a.get("calibrado") and medido and ci and cs and (medido < ci or medido > cs):
            malos.append(a)
    if not malos:
        return None
    total = sum(a["_valor"] for a in malos)
    return {
        "id": "rotulos_inconsistentes", "tipo": "corregir",
        "titulo": _t("core.opn.rotulo_t", lang, n=len(malos)),
        "monto": 0.0,
        "resumen": _t("core.opn.rotulo_r", lang, total=_pesos(total, lang)),
        "accion_chat": _t("core.opn.rotulo_chat", lang),
        "navegar": "saneamiento",
        "fuentes": [_t("core.opn.f_lotes", lang), _t("core.opn.f_inase", lang)],
        "drill": {
            "porque": [_t("core.opn.rotulo_p1", lang, n=len(malos), total=_pesos(total, lang)),
                       _t("core.opn.rotulo_p2", lang)],
            "grafico": None,
            "involucrados": [{"nombre": a.get("lote"), "monto": round(a["_valor"], 2),
                              "detalle": _t("core.opn.rotulo_i", lang,
                                            grado=a.get("calibre_grado"),
                                            medido=a.get("valor_peso"),
                                            min=a.get("cota_inf"), max=a.get("cota_sup"))}
                             for a in malos],
            "supuestos": [_t("core.opn.rotulo_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# 7 · Análisis por vencer para exportación
# ---------------------------------------------------------------------------
def _card_analisis(lang, ctx) -> dict | None:
    """Un análisis de más de 180 días frena el fitosanitario del SENASA. Los
    lotes marcados para exportación son los que hay que reanalizar primero."""
    export = [a for a in ctx["arts"] if a.get("destino") == "exportacion"]
    vencidos = [a for a in export
                if a["_dias_analisis"] is not None
                and a["_dias_analisis"] > DIAS_ANALISIS_EXPORTACION - 30]
    if not vencidos:
        return None
    vencidos.sort(key=lambda a: -(a["_dias_analisis"] or 0))
    total = sum(a["_valor"] for a in vencidos)
    ya = [a for a in vencidos if a["_dias_analisis"] > DIAS_ANALISIS_EXPORTACION]
    return {
        "id": "analisis_por_vencer", "tipo": "gestionar",
        "titulo": _t("core.opn.analisis_t", lang, n=len(vencidos)),
        "monto": 0.0,
        "resumen": _t("core.opn.analisis_r", lang, ya=len(ya),
                      total=_pesos(total, lang)),
        "accion_chat": _t("core.opn.analisis_chat", lang),
        "navegar": "trazabilidad",
        "fuentes": [_t("core.opn.f_lotes", lang), _t("core.opn.f_senasa", lang)],
        "drill": {
            "porque": [_t("core.opn.analisis_p1", lang, n=len(vencidos),
                          limite=DIAS_ANALISIS_EXPORTACION, total=_pesos(total, lang)),
                       _t("core.opn.analisis_p2", lang, ya=len(ya))],
            "grafico": None,
            "involucrados": [{"nombre": a.get("lote"), "monto": round(a["_valor"], 2),
                              "detalle": _t("core.opn.analisis_i", lang,
                                            dias=a["_dias_analisis"])}
                             for a in vencidos[:12]],
            "supuestos": [_t("core.opn.analisis_s", lang, limite=DIAS_ANALISIS_EXPORTACION)],
        },
    }


# ---------------------------------------------------------------------------
# 8 · El galpón sin frío
# ---------------------------------------------------------------------------
def _card_galpon(lang, ctx) -> dict | None:
    """El galpón es tránsito, no depósito: lo que entra ahí corre a reloj
    natural. Es la regla que el encargado le enseñó al sistema."""
    galpones = [u for u in ctx["ubicaciones"].values() if u.get("tipo") == "galpon"]
    if not galpones:
        return None
    ids = {u["id"] for u in galpones}
    dentro = [a for a in ctx["arts"] if a.get("ubicacion_id") in ids]
    if not dentro:
        return None
    total = sum(a["_valor"] for a in dentro)
    kg = sum(float(a.get("stock") or 0) for a in dentro)
    urgentes = [a for a in dentro
                if a["_dias_brot"] is not None and a["_dias_brot"] <= DIAS_MAX_GALPON]
    if not urgentes:
        return None
    return {
        "id": "galpon_sin_frio", "tipo": "despachar",
        "titulo": _t("core.opn.galpon_t", lang, n=len(urgentes),
                     galpon=galpones[0]["nombre"]),
        # Sin monto propio: estos lotes YA están contados en las cards de
        # brotación. Sumarlos acá sería contar la misma plata dos veces, que es
        # exactamente lo que un dueño detecta en dos segundos.
        "monto": 0.0,
        "resumen": _t("core.opn.galpon_r", lang, kg=_num(kg, lang),
                      total=_pesos(total, lang)),
        "accion_chat": _t("core.opn.galpon_chat", lang),
        "navegar": "deposito",
        "fuentes": [_t("core.opn.f_camaras", lang), _t("core.opn.f_conocimiento", lang)],
        "drill": {
            "porque": [_t("core.opn.galpon_p1", lang, n=len(urgentes),
                          dias=DIAS_MAX_GALPON),
                       _t("core.opn.galpon_p2", lang)],
            "grafico": None,
            "involucrados": [{"nombre": a.get("lote"), "monto": round(a["_valor"], 2),
                              "detalle": _t("core.opn.galpon_i", lang,
                                            dias=a["_dias_brot"])}
                             for a in sorted(urgentes, key=lambda x: x["_dias_brot"])],
            "supuestos": [_t("core.opn.galpon_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# 9 · Concentración de exportación (RIESGO, no plata que entra)
# ---------------------------------------------------------------------------
def _card_concentracion(lang, ctx) -> dict | None:
    """Cuánto del stock comprometido depende de un solo cliente. No es plata a
    cobrar: es exposición. Se muestra aparte y NUNCA suma al recuperable."""
    por_cliente: dict[str, float] = {}
    por_cod = {a.get("codigo"): a for a in store.raw_actual()}
    for o in esquema.filas("ordenes_carga"):
        if o.get("estado") == "despachada":
            continue
        for it in o.get("items") or []:
            a = por_cod.get(it.get("codigo")) or {}
            v = float(it.get("kg") or 0) * float(a.get("costo_iva") or 0)
            por_cliente[o.get("cliente") or "—"] = por_cliente.get(o.get("cliente") or "—", 0.0) + v
    if len(por_cliente) < 2:
        return None
    total = sum(por_cliente.values())
    if total <= 0:
        return None
    top, monto = max(por_cliente.items(), key=lambda kv: kv[1])
    pct = monto / total * 100
    if pct < 35:
        return None
    return {
        "id": "concentracion_exportacion", "tipo": "riesgo",
        "titulo": _t("core.opn.conc_t", lang, pct=round(pct, 1), cliente=top),
        "monto": round(monto, 2),
        "resumen": _t("core.opn.conc_r", lang, cliente=top, pct=round(pct, 1),
                      total=_pesos(total, lang)),
        "accion_chat": _t("core.opn.conc_chat", lang),
        "navegar": "logistica",
        "fuentes": [_t("core.opn.f_ordenes", lang), _t("core.opn.f_lotes", lang)],
        "drill": {
            "porque": [_t("core.opn.conc_p1", lang, cliente=top,
                          monto=_pesos(monto, lang), pct=round(pct, 1)),
                       _t("core.opn.conc_p2", lang)],
            "grafico": _grafico(
                _t("core.opn.conc_g", lang),
                [{"x": k, "y": round(v, 2)} for k, v in
                 sorted(por_cliente.items(), key=lambda kv: -kv[1])],
                "$", False),
            "involucrados": [{"nombre": k, "monto": round(v, 2),
                              "detalle": _t("core.opn.conc_i", lang,
                                            pct=round(v / total * 100, 1))}
                             for k, v in sorted(por_cliente.items(), key=lambda kv: -kv[1])],
            "supuestos": [_t("core.opn.conc_s", lang)],
        },
    }


# ---------------------------------------------------------------------------
# Quién ve qué
# ---------------------------------------------------------------------------
# Cada hallazgo declara los módulos que hay que tener para verlo. Al operario de
# frigorífico no le llega la exposición comercial con un cliente de exportación:
# no es su trabajo ni su información. El cálculo es UNO solo para todos (y sigue
# siendo el canónico, cacheado una vez); lo que cambia por persona es qué se le
# muestra.
DOMINIO = {
    "brotacion_inminente": ("deposito",),
    "ya_brotado": ("inventario",),
    "kilos_en_el_aire": ("movimientos",),
    "embarque_frenado": ("logistica",),
    "diferencias_abiertas": ("conciliacion",),
    "rotulos_inconsistentes": ("saneamiento",),
    "analisis_por_vencer": ("trazabilidad",),
    "galpon_sin_frio": ("deposito",),
    "concentracion_exportacion": ("logistica", "oportunidades"),
}


def visibles_para(cards_: list[dict], features) -> list[dict]:
    """Las tarjetas que le corresponden a un rol, por sus módulos.

    Se aplica DESPUÉS del cache a propósito: filtrar adentro guardaría el
    recorte del primero que preguntó.

    Una tarjeta sin dominio declarado NO se muestra: si mañana se agrega un
    hallazgo y nadie dijo de quién es, el default seguro es no filtrarlo a quien
    no corresponde."""
    feats = set(features or ())
    return [c for c in cards_
            if set(DOMINIO.get(c.get("id"), ("__sin_dominio__",))) <= feats]


_SET = [
    _card_brotacion,
    _card_ya_brotado,
    _card_kilos_en_el_aire,
    _card_embarque_frenado,
    _card_diferencias,
    _card_rotulos,
    _card_analisis,
    _card_galpon,
    _card_concentracion,
]


def cards(lang: str | None = None) -> list[dict]:
    """El set completo, ordenado por plata. Una card que falla no tira la
    sección: se omite y las demás salen igual."""
    ctx = _ctx(lang)
    out = []
    for fn in _SET:
        try:
            c = fn(lang, ctx)
        except Exception:  # noqa: BLE001 — una card rota no tira la sección
            c = None
        if c:
            c["naturaleza"] = NATURALEZA.get(c["id"], "accionable")
            out.append(c)
    out.sort(key=lambda c: -(c.get("monto") or 0))
    return out


def capital_recuperable(lang: str | None = None) -> dict:
    """LA cifra defendible: sólo lo `recuperable`, sumado una vez.

    Lo `accionable` no tiene monto propio (ya está contado adentro de otra
    card) y lo de `riesgo` es exposición: si se sumara, el total diría que la
    empresa va a "recuperar" plata que en realidad puede perder."""
    cs = cards(lang)
    partes = [c for c in cs if c.get("naturaleza") == "recuperable"]
    total = sum(c.get("monto") or 0 for c in partes)
    return {
        "total": round(total, 2),
        "total_fmt": _pesos(total, lang),
        "partes": [{"id": c["id"], "titulo": c["titulo"], "monto": c.get("monto"),
                    "naturaleza": c.get("naturaleza")} for c in partes],
        "otras": [{"id": c["id"], "titulo": c["titulo"],
                   "monto": c.get("monto"), "naturaleza": c.get("naturaleza")}
                  for c in cs if c.get("naturaleza") != "recuperable"],
        "nota": _t("core.opn.recuperable_nota", lang),
    }
