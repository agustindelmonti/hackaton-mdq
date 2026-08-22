"""
core/tareas.py — el trabajo, repartido.

LA IDEA. PolPilot no es donde se carga: es donde se trabaja. Una planilla
compartida sabe cuánto stock hay; no sabe QUIÉN tiene que hacer qué con eso. Y
en Papasud casi todo lo que se rompe se rompe por ahí: el traslado que salió y
nadie confirmó en destino no es un problema de datos, es una tarea que nunca se
le asignó a nadie.

CÓMO SE ARMA UNA TAREA. Tres caminos, uno solo de almacenamiento:

  1. Ángela la PROPONE — `sugeridas()` cruza las señales reales (traslados sin
     confirmar, conteos abiertos, análisis por vencer, órdenes frenadas) y para
     cada una calcula la acción concreta Y A QUIÉN LE TOCA. Nada se manda solo:
     la propuesta espera el OK de una persona.
  2. El dueño o el encargado la escriben a mano ("Néstor, contá la cámara 3").
  3. El propio interesado se la anota.

Las tres terminan en el mismo lugar: `recordatorios`, que ya sabe de
destinatario, autor, estado y notificación por la campanita. No hay un segundo
almacén de tareas que pueda desincronizarse.

A QUIÉN LE TOCA SE CALCULA, NO SE HARDCODEA.
El destinatario sale del ROL y de las UBICACIONES declaradas en el perfil, no
de una lista de usernames. Un traslado sin confirmar es del operario de la
ubicación DE DESTINO — el que tiene los bolsones delante —, y si esa ubicación
no tiene operario asignado, sube al encargado. Cuando entre una persona nueva
con el mismo rol, hereda las tareas sin tocar una línea de código.
"""
from __future__ import annotations

from . import conciliacion, movimientos, ordenes_carga, recordatorios, semilla, store
from .fechas import hoy, parse_fecha

# Cuánto puede estar un traslado "en camino" antes de que sea una tarea y no
# una espera. Mismo umbral que usa anomalias.py: un solo número.
DIAS_TRASLADO = 7

# Un análisis sanitario que vence adentro de esta ventana ya es trabajo de la
# agrónoma: renovar un DAS-ELISA no es de un día para el otro. El límite de
# vigencia (180 días para exportación) NO se redefine acá — se lee de
# oportunidades_neg, que es donde vive la regla del fitosanitario del SENASA.
VENTANA_ANALISIS = 30

PRIORIDAD = {"hoy": 0, "semana": 1, "cuando_puedas": 2}


# ---------------------------------------------------------------------------
# QUIÉN — el ruteo por rol y ubicación
# ---------------------------------------------------------------------------
def _cuando(dias: int) -> str:
    """"hace 0 días" no lo dice nadie."""
    if dias <= 0:
        return "hoy"
    if dias == 1:
        return "ayer"
    return f"hace {dias} días"


def _nomina() -> list[dict]:
    """El equipo, del mismo lugar del que sale el login."""
    try:
        import usuarios_papasud
        return list(usuarios_papasud.USUARIOS.values())
    except Exception:
        return []


def _por_rol(*palabras: str) -> dict | None:
    for u in _nomina():
        rol = (u.get("rol") or "").lower()
        if any(p in rol for p in palabras):
            return u
    return None


def _operario_de(ubicacion_id: str | None) -> dict | None:
    """El operario que está parado en esa ubicación.

    Sale de `ubicaciones` del perfil. Sin coincidencia devuelve None y el
    llamador sube al encargado — nunca se le asigna a nadie "por descarte"."""
    if not ubicacion_id:
        return None
    # El OPERARIO gana sobre el encargado: el encargado responde por las cuatro
    # ubicaciones, así que sin esta preferencia se llevaría todas las tareas de
    # piso y el que tiene los bolsones delante no se enteraría de ninguna.
    candidatos = [u for u in _nomina() if ubicacion_id in (u.get("ubicaciones") or [])]
    return (next((u for u in candidatos if "operario" in (u.get("rol") or "").lower()), None)
            or next(iter(candidatos), None))


def _encargado() -> dict | None:
    return _por_rol("encargado")


def _agronoma() -> dict | None:
    return _por_rol("agrónom", "agronom")


def _comercio_exterior() -> dict | None:
    return _por_rol("comercio exterior", "administración")


def _dueno() -> dict | None:
    return next((u for u in _nomina() if u.get("es_admin")), None)


def _quien(u: dict | None) -> dict:
    u = u or _encargado() or _dueno() or {}
    return {"username": u.get("username"), "nombre": u.get("nombre"),
            "rol": u.get("rol"), "color": u.get("color")}


# ---------------------------------------------------------------------------
# QUÉ — las tareas que Ángela propone, derivadas de señales reales
# ---------------------------------------------------------------------------
def sugeridas() -> list[dict]:
    """Lo que el sistema detectó y todavía no tiene dueño.

    Cada propuesta viaja con su EVIDENCIA (el número de movimiento, el lote, la
    fecha) para que quien la aprueba pueda verificarla sin salir de la pantalla.
    """
    out = []
    nombre_a_id = {u["nombre"]: u["id"] for u in semilla.ubicaciones()}

    # 1) los kilos en el aire — la tarea es de quien está en el DESTINO
    for m in movimientos.sin_confirmar():
        dias = m.get("dias_en_transito") or 0
        destino_id = nombre_a_id.get(m.get("destino"))
        persona = _operario_de(destino_id) or _encargado()
        out.append({
            "id": f"confirmar:{m['numero']}",
            "clase": "traslado_sin_confirmar",
            "titulo": f"Confirmar la llegada de {m['numero']} a {m.get('destino')}",
            "detalle": (f"Salieron {m['kg']:,.0f} kg de {m.get('origen')} {_cuando(dias)} "
                        f"y nadie confirmó que llegaran. Mientras tanto esos kilos no "
                        f"están en ningún lado.").replace(",", "."),
            "para": _quien(persona),
            "seccion": "movimientos",
            "prioridad": "hoy" if dias >= DIAS_TRASLADO else "semana",
            "evidencia": {"movimiento": m["numero"], "kg": m.get("kg"),
                          "origen": m.get("origen"), "destino": m.get("destino"),
                          "dias": dias},
        })

    # 2) las diferencias de conteo — las cierra el encargado
    for dif in conciliacion.abiertas():
        u = semilla.ubicacion(dif.get("ubicacion_id")) or {}
        f = parse_fecha(dif.get("fecha"))
        dias = (hoy() - f).days if f else 0
        out.append({
            "id": f"conteo:{dif['numero']}",
            "clase": "diferencia_abierta",
            "titulo": f"Cerrar la diferencia del lote {dif['lote']} en {u.get('nombre', '—')}",
            "detalle": dif.get("hipotesis", {}).get("texto") or
                       f"Quedan {abs(dif.get('diferencia_kg') or 0):,.0f} kg sin explicar.".replace(",", "."),
            "para": _quien(_encargado()),
            "seccion": "conciliacion",
            "prioridad": "hoy" if dias >= 14 else "semana",
            "evidencia": {"conteo": dif["numero"], "lote": dif.get("lote"),
                          "diferencia_kg": dif.get("diferencia_kg"), "dias": dias},
        })

    # 3) las órdenes frenadas — son de comercio exterior, que tiene el contenedor
    for o in ordenes_carga.pendientes_con_estado():
        if o.get("puede_emitirse"):
            continue
        motivos = ", ".join(b["control"].replace("_", " ") for b in (o.get("bloqueos") or []))
        out.append({
            "id": f"orden:{o['numero']}",
            "clase": "orden_frenada",
            "titulo": f"Destrabar la orden {o['numero']} · {o.get('cliente')}",
            "detalle": f"No se puede emitir el remito: {motivos}.",
            "para": _quien(_comercio_exterior()),
            "seccion": "logistica",
            "prioridad": "hoy",
            "evidencia": {"orden": o["numero"], "cliente": o.get("cliente"),
                          "bloqueos": [b["control"] for b in (o.get("bloqueos") or [])]},
        })

    # 4) los análisis sanitarios por vencer — de la agrónoma, que los firma
    from .oportunidades_neg import DIAS_ANALISIS_EXPORTACION
    por_vencer = []
    for a in store.raw_actual():
        if float(a.get("stock") or 0) <= 0 or a.get("destino") != "exportacion":
            continue
        f = parse_fecha(a.get("analisis_fecha"))
        if not f:
            continue
        dias_restantes = DIAS_ANALISIS_EXPORTACION - (hoy() - f).days
        if dias_restantes <= VENTANA_ANALISIS:
            por_vencer.append((dias_restantes, a))
    if por_vencer:
        por_vencer.sort(key=lambda x: x[0])
        dias, peor = por_vencer[0]
        vencidos = sum(1 for d, _ in por_vencer if d <= 0)
        out.append({
            "id": "analisis:por_vencer",
            "clase": "analisis_por_vencer",
            "titulo": f"Renovar el análisis sanitario de {len(por_vencer)} lotes de exportación",
            "detalle": (f"{vencidos} ya pasaron los {DIAS_ANALISIS_EXPORTACION} días de "
                        f"vigencia. El más viejo es {peor.get('lote')}. Sin DAS-ELISA "
                        f"vigente el SENASA no emite el fitosanitario y el contenedor "
                        f"no sale."),
            "para": _quien(_agronoma()),
            "seccion": "trazabilidad",
            "prioridad": "hoy" if vencidos else "semana",
            "evidencia": {"lotes": len(por_vencer), "vencidos": vencidos,
                          "primero": peor.get("lote"), "dias": dias},
        })

    # 5) lo que se brota primero — al encargado, que decide qué se despacha antes
    h = hoy()
    riesgo = []
    for a in store.raw_actual():
        b = parse_fecha(a.get("brotacion_estimada"))
        if not b or float(a.get("stock") or 0) <= 0:
            continue
        dd = (b - h).days
        if 0 < dd <= 45:
            riesgo.append((dd, a))
    if riesgo:
        riesgo.sort(key=lambda x: x[0])
        dd, peor = riesgo[0]
        out.append({
            "id": "brotacion:ventana",
            "clase": "brotacion",
            "titulo": f"Adelantar el despacho de {len(riesgo)} lotes que se brotan",
            "detalle": (f"El primero es {peor.get('lote')} en {dd} días. Un lote que "
                        f"brota antes de despacharse deja de ser semilla de su categoría."),
            "para": _quien(_encargado()),
            "seccion": "deposito",
            "prioridad": "semana",
            "evidencia": {"lotes": len(riesgo), "primero": peor.get("lote"), "dias": dd},
        })

    ya = _ya_asignadas()
    out = [s for s in out if s["id"] not in ya]
    out.sort(key=lambda s: PRIORIDAD.get(s["prioridad"], 9))
    return out


def _ya_asignadas() -> set[str]:
    """Las sugerencias que ALGUIEN YA ACEPTÓ.

    Sin esto, la misma propuesta vuelve a aparecer después de asignarla y el
    dueño la manda dos veces. El origen queda guardado en el recordatorio."""
    # `incluir_hechos`: una sugerencia que ya se asignó Y SE CERRÓ tampoco
    # tiene que volver a ofrecerse — si no, cada vez que alguien termina un
    # trabajo el sistema se lo vuelve a pedir.
    return {r.get("origen") for r in recordatorios.listar(None, incluir_hechos=True)
            if r.get("origen")}


# ---------------------------------------------------------------------------
# ASIGNAR — la propuesta se vuelve tarea de alguien
# ---------------------------------------------------------------------------
def asignar(titulo: str, para: str, creado_por: str, origen: str | None = None,
            seccion: str | None = None, prioridad: str = "semana",
            detalle: str = "") -> dict:
    """Crea la tarea y AVISA al destinatario por la campanita.

    Guarda `origen` (el id de la sugerencia) para que la propuesta no vuelva a
    ofrecerse: aceptar dos veces la misma cosa es la forma más rápida de que el
    equipo deje de mirar las notificaciones."""
    r = recordatorios.crear(titulo, para=para, creado_por=creado_por)
    r["origen"] = origen
    r["seccion"] = seccion
    r["prioridad"] = prioridad
    r["detalle"] = detalle
    _persistir(r)
    try:
        from . import notificaciones
        notificaciones.emitir(
            para=para,
            titulo="Te asignaron una tarea",
            cuerpo=titulo,
            tipo="tarea_asignada", ref=r["id"],
        )
    except Exception:  # noqa: BLE001 — la tarea existe aunque falle el aviso
        pass
    return r


def _persistir(r: dict) -> None:
    """Vuelve a guardar el recordatorio con los campos extra de tarea."""
    items = recordatorios._load()  # noqa: SLF001 — mismo módulo de datos
    for i, x in enumerate(items):
        if x["id"] == r["id"]:
            items[i] = r
            break
    recordatorios._save(items)  # noqa: SLF001


def puede_asignar(u: dict) -> bool:
    """Quién puede dejarle trabajo a otro.

    El dueño, obviamente. Y el ENCARGADO: es el que reparte el día en la cámara,
    y obligarlo a pedirle al dueño que le asigne un conteo a Néstor convertiría
    la herramienta en un trámite."""
    return bool(u.get("es_admin")) or "encargado" in (u.get("rol") or "").lower()


# ---------------------------------------------------------------------------
# LEER — lo de cada uno y el panorama del que reparte
# ---------------------------------------------------------------------------
def de_usuario(username: str) -> list[dict]:
    todas = recordatorios.listar(username)
    return [r for r in todas if r.get("estado") != "hecho"]


def panorama() -> dict:
    """Lo que el dueño mira: quién tiene qué y qué se cerró.

    Sirve a la pregunta que hoy se contesta por WhatsApp: «¿alguien confirmó lo
    de Chapadmalal?»."""
    todas = recordatorios.listar(None, incluir_hechos=True)
    por_persona: dict[str, dict] = {}
    for r in todas:
        p = r.get("para") or "—"
        g = por_persona.setdefault(p, {"username": p, "abiertas": 0, "hechas": 0,
                                       "titulos": []})
        if r.get("estado") == "hecho":
            g["hechas"] += 1
        else:
            g["abiertas"] += 1
            g["titulos"].append(r.get("texto"))
    nom = {u["username"]: u for u in _nomina()}
    for p, g in por_persona.items():
        u = nom.get(p) or {}
        g["nombre"] = u.get("nombre") or p
        g["rol"] = u.get("rol")
        g["color"] = u.get("color")
    return {
        "personas": sorted(por_persona.values(), key=lambda g: -g["abiertas"]),
        "abiertas": sum(g["abiertas"] for g in por_persona.values()),
        "hechas": sum(g["hechas"] for g in por_persona.values()),
    }
