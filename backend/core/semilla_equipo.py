"""
core/semilla_equipo.py — la semana anterior del equipo.

POR QUÉ ESTO EXISTE. «Lo que pasó con tu equipo» y «Quién tiene qué» son
agregadores de la auditoría REAL: cuentan lo que la gente hizo adentro de
PolPilot. En una instancia recién levantada eso es cero, y el dueño abre la
pantalla que más promete —una herramienta que conecta a toda la empresa— y ve
«0/6 usaron PolPilot esta semana · Sin actividad registrada». La herramienta
parece muerta antes de que alguien la use.

QUÉ SE SIEMBRA Y QUÉ NO. Se siembran los SIETE DÍAS PREVIOS a la fecha del
dataset: consultas a Ángela (el TEMA, nunca el texto), cargas, correcciones y
un puñado de tareas —algunas cerradas, otras abiertas—. Es exactamente el mismo
criterio que el resto del dataset: la empresa es real, los números están
calcados de su operación, y **todo el contenido es sintético**. Nada de esto
pisa un número canónico: el stock, las diferencias y los embarques siguen
saliendo del generador.

SE SIEMBRA UNA SOLA VEZ. Si el archivo ya existe (porque alguien usó la app, o
porque ya se sembró), no se toca. Así lo que hace el equipo en vivo durante la
demo se suma a esto en lugar de pisarlo.
"""
from __future__ import annotations

import datetime
import json
import os

from . import paths
from .fechas import hoy

MARCA = os.path.join(paths.DATA_DIR, ".semilla_equipo")

# Las tareas de la semana. `dias` = hace cuántos días se asignó.
# Las cerradas son las que hacen creíble el tablero: un equipo donde nadie
# cerró nunca nada no es un equipo, es una lista de pendientes.
TAREAS = [
    {"texto": "Contar la Cámara 2 de Ruta 226 · lote de Spunta",
     "para": "marcos", "de": "ruben", "dias": 5, "hecho": True},
    {"texto": "Confirmar lo que llegó de Sierra el lunes",
     "para": "nestor", "de": "ruben", "dias": 4, "hecho": True},
    {"texto": "Revisar el calibre declarado de los tres lotes de Innovator",
     "para": "dalia", "de": "ernesto", "dias": 3, "hecho": True},
    {"texto": "Pedirle al despachante la fecha firme del contenedor de Vietnam",
     "para": "cecilia", "de": "ernesto", "dias": 2, "hecho": False},
    {"texto": "Acondicionar los bolsones del galpón que salen esta semana",
     "para": "nestor", "de": "ruben", "dias": 1, "hecho": False},
]

# La actividad adentro de PolPilot. `accion` usa el mismo vocabulario que la
# auditoría real, para que el agregador la cuente sin excepciones.
ACTIVIDAD = [
    ("ruben", "consulta_angela", 6, {"tool": "stock_por_ubicacion"}),
    ("ruben", "consulta_angela", 5, {"tool": "diferencias_abiertas"}),
    ("ruben", "confirmar_movimiento", 5, {"numero": "MOV-2026-0906"}),
    ("marcos", "consulta_angela", 5, {"tool": "stock_de_lote"}),
    ("marcos", "registrar_movimiento", 4, {"numero": "MOV-2026-0908"}),
    ("marcos", "consulta_angela", 2, {"tool": "stock_de_lote"}),
    ("dalia", "consulta_angela", 4, {"tool": "analisis_por_vencer"}),
    ("dalia", "corregir_calibre", 3, {"lotes": 2}),
    ("cecilia", "consulta_angela", 3, {"tool": "documentacion_embarque"}),
    ("cecilia", "generar_documento", 3, {"documento": "packing_list"}),
    ("nestor", "consulta_angela", 4, {"tool": "donde_va_el_lote"}),
    ("nestor", "confirmar_movimiento", 4, {"numero": "MOV-2026-0907"}),
    ("nestor", "consulta_angela", 1, {"tool": "que_me_toca"}),
    ("ernesto", "consulta_angela", 2, {"tool": "panorama"}),
]


def _fecha(dias: int) -> str:
    d = hoy() - datetime.timedelta(days=dias)
    # una hora de trabajo cualquiera, estable entre arranques
    return datetime.datetime.combine(d, datetime.time(9 + (dias % 6), 20)).isoformat(
        timespec="seconds")


def sembrar() -> bool:
    """Materializa la semana previa. Devuelve True si sembró algo."""
    if os.path.exists(MARCA):
        return False
    os.makedirs(paths.DATA_DIR, exist_ok=True)

    # --- las tareas ---------------------------------------------------------
    rec_path = os.path.join(paths.DATA_DIR, "recordatorios.json")
    if not os.path.exists(rec_path):
        items = []
        for i, x in enumerate(TAREAS):
            items.append({
                "id": f"rsem{i:02d}",
                "texto": x["texto"],
                "para": x["para"],
                "creado_por": x["de"],
                "condicion": None,
                "estado": "hecho" if x["hecho"] else "activo",
                "creado": _fecha(x["dias"]),
                "disparado_en": None,
                "detalle_disparo": None,
                "canales": ["panel"],
                "prioridad": "semana",
                "sembrado": True,
            })
        json.dump(items, open(rec_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    # --- la actividad adentro de la app -------------------------------------
    aud_path = os.path.join(paths.DATA_DIR, "audit.json")
    if not os.path.exists(aud_path):
        eventos = []
        for i, (actor, accion, dias, detalle) in enumerate(ACTIVIDAD, start=1):
            eventos.append({
                "id": i, "actor": actor, "accion": accion,
                "antes": None, "despues": detalle,
                "cuando": _fecha(dias), "sembrado": True,
            })
        json.dump(eventos, open(aud_path, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    open(MARCA, "w", encoding="utf-8").write(hoy().isoformat())
    return True
