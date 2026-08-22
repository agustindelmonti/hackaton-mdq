"""
ordenes_carga.py · El sistema frena el remito antes de que lo frene el cliente.

ESTA ES LA FRASE DEL BRIEF, Y ES EL CORAZÓN DE TODO:

    «Las diferencias entre lo que dice la planilla y lo que hay en la realidad
    suelen descubrirse recién al momento de entregarle el pedido a un cliente.»

El dolor no es el desorden: es el papelón. El camión está en la playa, el
cliente esperando, y ahí aparece que faltan dieciocho bolsones. Cuarenta años de
reputación se juegan en ese momento.

Lo que pide N02 es explícito: «un tablero que PREVENGA la emisión de órdenes de
carga o remitos si no existe stock real verificado en la ubicación
correspondiente». Prevenir, no avisar. Por eso `emitir()` no devuelve una
advertencia que alguien pueda ignorar: devuelve un rechazo con el motivo, la
evidencia y qué hay que hacer para levantarlo.

LOS CINCO CONTROLES, EN ORDEN

  1. STOCK VERIFICADO — ¿hay realmente estos kilos disponibles en esa ubicación?
     Disponible descuenta lo que está en tránsito sin confirmar y lo que ya está
     prometido en otra orden. Es la resta que la planilla no hace.
  2. CONTEO EN DISCUSIÓN — si sobre ese lote y esa ubicación hay una diferencia
     de conteo abierta, el stock NO está verificado por definición: hay dos
     números y nadie sabe cuál vale. No se carga sobre un número en discusión.
  3. SANIDAD VIGENTE (sólo exportación) — el análisis del lote no puede tener más
     de 180 días. Sale de la regla que la agrónoma le enseñó al sistema
     (conocimiento, pieza K-003), y en la práctica es lo que el SENASA va a
     mirar antes de firmar el fitosanitario.
  4. RÓTULO CONSISTENTE (sólo exportación) — si el calibre medido del lote quedó
     fuera del rango del grado que declara el rótulo, el rótulo miente. Eso no se
     descubre acá: se descubre en destino, y vuelve el contenedor.
  5. BROTACIÓN — un lote que ya pasó su fecha estimada de brotación dejó de ser
     semilla de su categoría. Se puede despachar igual, pero con el ojo de un
     humano encima, no por inercia.

Los controles 1 y 2 BLOQUEAN. Los 3, 4 y 5 bloquean para exportación y advierten
para mercado interno: el criterio no lo inventa el módulo, lo declara el negocio.
"""
from __future__ import annotations

from . import conciliacion, esquema, movimientos, semilla, store
from .fechas import hoy, parse_fecha

APARTADO = "ordenes_carga"

DIAS_ANALISIS_EXPORTACION = 180   # regla K-003 (la firma la agrónoma)

# Un control que bloquea no se puede "aceptar igual" desde la pantalla: hay que
# resolver la causa. Uno que advierte pide una confirmación explícita de alguien
# con permiso, y esa confirmación queda en el registro de auditoría.
BLOQUEANTES = {"sin_stock_verificado", "conteo_en_discusion"}


def _ordenes() -> list[dict]:
    return esquema.filas(APARTADO)


def hay_datos() -> bool:
    return bool(_ordenes())


def listar(estado: str | None = None, tipo: str | None = None) -> list[dict]:
    out = [dict(o) for o in _ordenes()
           if (not estado or o.get("estado") == estado)
           and (not tipo or o.get("tipo") == tipo)]
    out.sort(key=lambda o: str(o.get("fecha") or ""), reverse=True)
    return out


def buscar(numero: str) -> dict | None:
    n = (numero or "").strip().upper()
    return next((dict(o) for o in _ordenes()
                 if str(o.get("numero") or "").upper() == n), None)


# ---------------------------------------------------------------------------
# La verificación
# ---------------------------------------------------------------------------
def verificar(numero: str) -> dict:
    """¿Se puede emitir esta orden? Devuelve el veredicto y TODO el detalle.

    No escribe nada: es la consulta que la pantalla hace antes de mostrar el
    botón, y la misma que `emitir()` corre antes de dejar pasar."""
    o = buscar(numero)
    if not o:
        return {"encontrado": False, "numero": numero}

    es_export = o.get("tipo") == "exportacion"
    controles: list[dict] = []
    arts = {a.get("codigo"): a for a in store.raw_actual()}
    difs_abiertas = conciliacion.abiertas()

    for it in o.get("items") or []:
        cod = it.get("codigo")
        art = arts.get(cod) or {}
        pedido = float(it.get("kg") or 0)

        # --- 1) stock verificado ------------------------------------------
        disp = movimientos.disponible(cod, art.get("ubicacion_id"))
        # los kilos de ESTA orden ya están contados como comprometidos: no se
        # cuentan dos veces contra sí misma
        libre = disp.get("disponible_kg", 0) + (pedido if o.get("estado") in
                                                ("emitida", "pendiente") else 0)
        if pedido > libre:
            controles.append({
                "control": "sin_stock_verificado",
                "estado": "bloquea",
                "lote": it.get("lote"),
                "codigo": cod,
                "ubicacion": disp.get("ubicacion"),
                "pedido_kg": round(pedido, 1),
                "disponible_kg": round(libre, 1),
                "faltante_kg": round(pedido - libre, 1),
                "faltante_bolsones": round((pedido - libre) / 1000, 2),
                "detalle": disp,
            })

        # --- 2) conteo en discusión ---------------------------------------
        en_discusion = [d for d in difs_abiertas if d["codigo"] == cod]
        for d in en_discusion:
            controles.append({
                "control": "conteo_en_discusion",
                "estado": "bloquea",
                "lote": it.get("lote"),
                "codigo": cod,
                "ubicacion": d["ubicacion"],
                "diferencia_kg": d["diferencia_kg"],
                "hipotesis": d["hipotesis"],
                "conteo": d["numero"],
            })

        # --- 3) sanidad vigente -------------------------------------------
        f_analisis = parse_fecha(art.get("analisis_fecha"))
        dias_analisis = (hoy() - f_analisis).days if f_analisis else None
        if dias_analisis is not None and dias_analisis > DIAS_ANALISIS_EXPORTACION:
            controles.append({
                "control": "analisis_vencido",
                "estado": "bloquea" if es_export else "advierte",
                "lote": it.get("lote"),
                "codigo": cod,
                "dias": dias_analisis,
                "limite_dias": DIAS_ANALISIS_EXPORTACION,
                "analisis_fecha": art.get("analisis_fecha"),
            })
        if art.get("analisis_estado") == "observado":
            controles.append({
                "control": "sanidad_observada",
                "estado": "bloquea" if es_export else "advierte",
                "lote": it.get("lote"),
                "codigo": cod,
                "virus_pct": art.get("virus_pct"),
                "virus_max_pct": art.get("virus_max_pct"),
                "categoria": art.get("categoria_semilla"),
            })

        # --- 4) rótulo consistente ----------------------------------------
        medido = art.get("valor_peso")
        cinf, csup = art.get("cota_inf"), art.get("cota_sup")
        if art.get("calibrado") and medido is not None and cinf and csup:
            if medido < cinf or medido > csup:
                controles.append({
                    "control": "calibre_fuera_de_grado",
                    "estado": "bloquea" if es_export else "advierte",
                    "lote": it.get("lote"),
                    "codigo": cod,
                    "grado": art.get("calibre_grado"),
                    "medido_mm": medido,
                    "rango_mm": [cinf, csup],
                })

        # --- 5) brotación --------------------------------------------------
        b = parse_fecha(art.get("brotacion_estimada"))
        if b and (b - hoy()).days <= 0:
            controles.append({
                "control": "pasado_de_brotacion",
                "estado": "bloquea" if es_export else "advierte",
                "lote": it.get("lote"),
                "codigo": cod,
                "brotacion_estimada": art.get("brotacion_estimada"),
                "dias_pasados": (hoy() - b).days,
            })

    bloqueos = [c for c in controles if c["estado"] == "bloquea"]
    avisos = [c for c in controles if c["estado"] == "advierte"]
    return {
        "encontrado": True,
        "numero": o["numero"],
        "cliente": o.get("cliente"),
        "tipo": o.get("tipo"),
        "pais": o.get("pais"),
        "estado": o.get("estado"),
        "kg_total": o.get("kg_total"),
        "items": o.get("items"),
        "ubicacion_carga": o.get("ubicacion_carga"),
        "puede_emitirse": not bloqueos,
        "bloqueos": bloqueos,
        "advertencias": avisos,
        "controles_corridos": 5,
    }


def emitir(numero: str, actor: str, forzar_advertencias: bool = False) -> dict:
    """Emite la orden — o la frena.

    Si hay bloqueos devuelve `{ok: False}` con el motivo y no escribe nada. Que
    el freno viva ACÁ y no en la pantalla es deliberado: el mismo control corre
    para el botón, para el chat de Ángela y para cualquier integración futura.
    No hay una puerta de atrás por la que salga un remito sin verificar."""
    v = verificar(numero)
    if not v.get("encontrado"):
        return {"ok": False, "motivo": "orden_inexistente", "numero": numero}
    if v["estado"] == "despachada":
        return {"ok": False, "motivo": "ya_despachada", "numero": numero}
    if v["bloqueos"]:
        store.audit.record(actor=actor, accion="emision_bloqueada",
                     antes={"numero": numero, "cliente": v["cliente"]},
                     despues={"bloqueos": [b["control"] for b in v["bloqueos"]]})
        return {"ok": False, "motivo": "bloqueada", **v}
    if v["advertencias"] and not forzar_advertencias:
        return {"ok": False, "motivo": "requiere_confirmacion", **v}

    filas = _ordenes()
    for o in filas:
        if o.get("numero") == numero:
            o["estado"] = "emitida"
            o["emitida_por"] = actor
            o["emitida_fecha"] = hoy().isoformat()
            if v["advertencias"]:
                o["advertencias_aceptadas"] = [a["control"] for a in v["advertencias"]]
            break
    esquema.reemplazar_filas(APARTADO, filas)
    store.audit.record(actor=actor, accion="emitir_orden_carga",
                 antes={"numero": numero, "estado": v["estado"]},
                 despues={"estado": "emitida", "cliente": v["cliente"],
                          "kg": v["kg_total"],
                          "advertencias_aceptadas": [a["control"] for a in v["advertencias"]]})
    return {"ok": True, "numero": numero, "estado": "emitida",
            "advertencias_aceptadas": v["advertencias"]}


# ---------------------------------------------------------------------------
# El tablero de despachos
# ---------------------------------------------------------------------------
def pendientes_con_estado() -> list[dict]:
    """Las órdenes abiertas, cada una con su veredicto ya calculado.

    Es la pantalla que hoy no existe: de un vistazo, cuál sale y cuál no, y por
    qué. Sin abrir la planilla y sin llamar por teléfono al depósito."""
    out = []
    for o in listar():
        if o.get("estado") == "despachada":
            continue
        v = verificar(o["numero"])
        out.append({**o,
                    "puede_emitirse": v["puede_emitirse"],
                    "bloqueos": v["bloqueos"],
                    "advertencias": v["advertencias"]})
    out.sort(key=lambda o: (o["puede_emitirse"], str(o.get("fecha") or "")))
    return out


def resumen() -> dict:
    pend = pendientes_con_estado()
    bloqueadas = [o for o in pend if not o["puede_emitirse"]]
    kg_bloqueado = sum(float(o.get("kg_total") or 0) for o in bloqueadas)
    return {
        "hay_datos": hay_datos(),
        "total": len(_ordenes()),
        "abiertas": len(pend),
        "bloqueadas": len(bloqueadas),
        "listas": len(pend) - len(bloqueadas),
        "kg_bloqueado": round(kg_bloqueado, 1),
        "exportacion_abiertas": sum(1 for o in pend if o.get("tipo") == "exportacion"),
    }
