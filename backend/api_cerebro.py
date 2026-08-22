"""
api_cerebro.py · Los endpoints de «¿tengo o no tengo?».

Vive aparte de `main.py` a propósito: mientras el track del modelo y el
importador se mueve, este archivo agrega UNA línea a `main.py` en vez de
cincuenta. Menos superficie de merge, menos hora perdida.

Todo lo que devuelve sale de `core/disponibilidad.py` y `core/comercial.py`,
que calculan sobre el libro de movimientos. Ningún endpoint inventa un número
ni lo reformatea: los strings ya vienen armados del core para que la pantalla
—y el modelo— los copien tal cual.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from authz import usuario_actual
from core import comercial, consulta_nl, disponibilidad as disp, papasud_real as real

router = APIRouter(prefix="/api/cerebro", tags=["cerebro"])


def _exigir_datos() -> None:
    if not real.hay_datos_reales():
        raise HTTPException(
            status_code=503,
            detail="La planilla todavía no está importada. "
                   "Corré: python data-papasud/planilla_real.py")


# ===========================================================================
# 1 · LA CONSULTA QUE ABRE LA DEMO
# ===========================================================================
class Pregunta(BaseModel):
    texto: str


@router.post("/preguntar")
def preguntar(req: Pregunta, _u: dict = Depends(usuario_actual)):
    """«¿tengo 1.200 bolsas de Spunta?» — por texto o por voz, desde el celular.

    Devuelve SIEMPRE `entendido`: lo que la máquina escuchó, para que la persona
    lo confirme antes de creerle. Ese paso es lo que hace que un operario confíe.
    """
    _exigir_datos()
    p = consulta_nl.interpretar(req.texto or "")
    salida = {"interpretacion": p, "entendido": consulta_nl.entendido(p)}

    if p["intencion"] == "venta_cliente" and p.get("cliente"):
        salida["tipo"] = "venta_cliente"
        salida["ventas"] = comercial.ventas(cliente=p["cliente"])
        v = salida["ventas"]
        salida["titular"] = (
            f"A {p['cliente'].title()} se le entregaron "
            f"{v['kg']:,} kg en {v['camiones']} camiones.".replace(",", "."))
        return salida

    if not any((p.get("variedad"), p.get("ubicacion"), p.get("lote"))):
        salida["tipo"] = "no_entendi"
        salida["titular"] = (
            "No reconocí ni la variedad ni el lugar. Probá con «cuánta agata "
            "hay en el galpón» o «tengo 1.200 bolsas de spunta».")
        salida["catalogo"] = catalogo(_u)
        return salida

    salida["tipo"] = "disponibilidad"
    salida["respuesta"] = disp.consultar(
        variedad=p["variedad"], calibre=p["calibre"], ubicacion=p["ubicacion"],
        lote=p["lote"], cantidad=p["cantidad"], unidad=p["unidad"])
    salida["titular"] = salida["respuesta"]["titular"]

    # Si preguntaron por una cantidad y no alcanza, se contesta con las salidas
    # ya calculadas: frenar sin decir cómo sí resolverlo es una traba, no ayuda.
    if p.get("cantidad") and salida["respuesta"]["alcanza"] is False:
        salida["evaluacion"] = disp.evaluar_pedido(
            variedad=p["variedad"], cantidad=p["cantidad"], unidad=p["unidad"],
            calibre=p["calibre"], ubicacion=p["ubicacion"])
    return salida


@router.get("/disponibilidad")
def disponibilidad(variedad: str | None = None, calibre: str | None = None,
                   ubicacion: str | None = None, lote: str | None = None,
                   cantidad: float | None = None, unidad: str = "kg",
                   _u: dict = Depends(usuario_actual)):
    _exigir_datos()
    return disp.consultar(variedad=variedad, calibre=calibre, ubicacion=ubicacion,
                          lote=lote, cantidad=cantidad, unidad=unidad)


@router.get("/partidas")
def partidas(variedad: str | None = None, calibre: str | None = None,
             ubicacion: str | None = None, lote: str | None = None,
             _u: dict = Depends(usuario_actual)):
    """El detalle verificable: cada partida con su remito y su fila del Excel."""
    _exigir_datos()
    ps = disp.partidas(variedad=variedad, calibre=calibre,
                       ubicacion=ubicacion, lote=lote)
    return {"partidas": ps[:400], "total": len(ps), "resumen": disp.resumen(ps)}


# ===========================================================================
# 2 · EL BLOQUEO CON ALTERNATIVA
# ===========================================================================
class Pedido(BaseModel):
    variedad: str
    cantidad: float
    unidad: str = "kg"
    calibre: str | None = None
    ubicacion: str | None = None
    cliente: str | None = None
    entrega: str | None = None


@router.post("/pedido/evaluar")
def evaluar(req: Pedido, _u: dict = Depends(usuario_actual)):
    """Antes de comprometer: ¿se puede? Y si no, de dónde sale."""
    _exigir_datos()
    return disp.evaluar_pedido(
        variedad=req.variedad, cantidad=req.cantidad, unidad=req.unidad,
        calibre=req.calibre, ubicacion=req.ubicacion, cliente=req.cliente)


@router.post("/pedido/comprometer")
def comprometer(req: Pedido, u: dict = Depends(usuario_actual)):
    """Reserva el stock. Pasa por la MISMA evaluación que la pantalla: no hay
    puerta de atrás por la que salga un pedido sin verificar."""
    _exigir_datos()
    if not req.cliente:
        raise HTTPException(status_code=400, detail="Falta el cliente.")
    r = disp.comprometer(
        variedad=req.variedad, cantidad=req.cantidad, unidad=req.unidad,
        cliente=req.cliente, calibre=req.calibre, ubicacion=req.ubicacion,
        entrega=req.entrega, quien=u.get("username", ""))
    if not r["ok"]:
        raise HTTPException(status_code=409, detail=r["evaluacion"]["titular"])
    return r


@router.get("/pedidos")
def pedidos(_u: dict = Depends(usuario_actual)):
    _exigir_datos()
    return {"pedidos": disp.pedidos_abiertos()}


# ===========================================================================
# 3 · CONSULTAS COMERCIALES · «¿cuánto le vendimos a este cliente?»
# ===========================================================================
@router.get("/clientes")
def clientes(_u: dict = Depends(usuario_actual)):
    _exigir_datos()
    return {"clientes": comercial.clientes()}


@router.get("/ventas")
def ventas(cliente: str | None = None, desde: str | None = None,
           hasta: str | None = None, variedad: str | None = None,
           _u: dict = Depends(usuario_actual)):
    _exigir_datos()
    return comercial.ventas(cliente=cliente, desde=desde, hasta=hasta,
                            variedad=variedad)


@router.get("/ventas/comparar")
def comparar(_u: dict = Depends(usuario_actual)):
    _exigir_datos()
    return comercial.comparar()


# ===========================================================================
# 4 · ADMINISTRACIÓN · lo que hay que pagarle a cada uno
# ===========================================================================
@router.get("/liquidacion")
def liquidacion(desde: str | None = None, hasta: str | None = None,
                _u: dict = Depends(usuario_actual)):
    """«Hay que pagarle al camión A: ¿cuántos kilos trajo? Listo, acá está.»"""
    _exigir_datos()
    return {
        "transportistas": comercial.transportistas(desde=desde, hasta=hasta),
        "frigorificos": comercial.frigorificos(desde=desde, hasta=hasta),
    }


# ===========================================================================
# 5 · LA PLANILLA POR DENTRO · lo que trae mal, con el número de fila
# ===========================================================================
@router.get("/planilla")
def planilla(_u: dict = Depends(usuario_actual)):
    """No esconde la mugre: la lista.

    Que la columna «Cliente» tenga un peso adentro no es un defecto a tapar —
    es la prueba de por qué necesitan esto. Cada hallazgo trae la solapa y la
    fila del Excel, para abrirlo en la planilla de ellos y verlo.
    """
    _exigir_datos()
    anom = real.anomalias()
    por_id: dict[str, dict] = {}
    for a in anom:
        d = por_id.setdefault(a["id"], {"id": a["id"], "cantidad": 0, "ejemplos": []})
        d["cantidad"] += 1
        if len(d["ejemplos"]) < 5:
            d["ejemplos"].append(a)
    l = disp.libro()
    return {
        "meta": real.meta(),
        "totales": {
            "movimientos": len(real.movimientos()),
            "lotes": len(real.lotes()),
            "kg": sum(m.get("kg") or 0 for m in real.movimientos()),
            "hallazgos": len(anom),
            "saldo_anterior_kg": l["saldo_anterior_kg"],
        },
        "hallazgos": sorted(por_id.values(), key=lambda d: -d["cantidad"]),
        "saldos_anteriores": l["saldos_anteriores"][:40],
    }


@router.get("/remito/{remito_id:path}")
def remito(remito_id: str, _u: dict = Depends(usuario_actual)):
    """El camión arriba y los lotes que llevó abajo — como lo pidieron."""
    _exigir_datos()
    filas = [m for m in real.movimientos()
             if (m.get("remito_id") == remito_id or m.get("remito") == remito_id)]
    if not filas:
        raise HTTPException(status_code=404, detail=f"No hay remito {remito_id}.")
    return {"remitos": comercial.remitos(filas)}


@router.get("/catalogo")
def catalogo(_u: dict = Depends(usuario_actual)):
    """Lo que la pantalla necesita para armar los selectores, sacado de los
    datos reales: si una variedad no está en la planilla, no está en la lista."""
    _exigir_datos()
    return {
        "variedades": consulta_nl.variedades(),
        "calibres": [c for c in disp.ORDEN_CALIBRE if c != disp.SIN_CLASIFICAR],
        "ubicaciones": real.ubicaciones(),
        "clientes": consulta_nl.clientes(),
        "campos": real.campos(),
        "lotes": [{"id": l["id"], "variedad": l["variedad"], "campo": l["campo"]}
                  for l in real.lotes()],
    }
