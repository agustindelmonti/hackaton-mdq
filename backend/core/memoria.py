"""
Memoria del usuario — lo que hace que PolPilot "te conozca".

Guarda, por usuario: preferencias, objetivos declarados, qué datos ya cargó,
y las recomendaciones que Ángela hizo + su resultado. Es lo que personaliza la
experiencia sin que nadie configure nada: a medida que el usuario trabaja y
aprueba cosas, el sistema se afina solo.

Persiste en data/memoria.json. Compatible con `aprobar_categoria` del Plan 2.
"""
from __future__ import annotations

import json
import os
import secrets

from . import paths
from .fechas import hoy

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = paths.DATA_DIR  # por-tenant: env POLPILOT_DATA_DIR o data/ (ver core/paths.py)
MEMORIA_JSON = os.path.join(DATA_DIR, "memoria.json")

_VACIO = {
    "preferencias": {},
    "vista": {},  # P19·A: preferencias de vista estructuradas (ver VISTA_CATALOGO)
    "categorias_auto": [],
    "objetivos": [],
    "datos_cargados": [],
    "recomendaciones": [],
    "hechos": [],  # cosas sueltas que la persona contó — ver agregar_hecho()
}


def _load() -> dict:
    if not os.path.exists(MEMORIA_JSON):
        return {}
    try:
        with open(MEMORIA_JSON, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data: dict) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MEMORIA_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _usuario(data: dict, usuario: str) -> dict:
    u = data.setdefault(usuario, {})
    for k, v in _VACIO.items():
        u.setdefault(k, json.loads(json.dumps(v)))  # copia
    return u


def get(usuario: str) -> dict:
    """Toda la memoria de un usuario (secciones garantizadas)."""
    data = _load()
    return _usuario(data, usuario)


# Alias histórico (Plan 2 lo usa para leer categorias_auto).
def preferencias(usuario: str) -> dict:
    return get(usuario)


def set_pref(usuario: str, clave: str, valor) -> dict:
    data = _load()
    _usuario(data, usuario)["preferencias"][clave] = valor
    _save(data)
    return data[usuario]


# --- P19·A — preferencias de VISTA estructuradas ------------------------------
# Lo que Ángela recuerda de CÓMO le gusta ver el negocio a cada persona, con
# catálogo cerrado: cada clave la aplica una parte concreta de la interfaz.
# Nada de memoria oculta: /api/preferencias las lista y las borra una por una
# (Mi perfil las muestra). Todo pasa por acá — chat, endpoints y frontend leen
# EL MISMO archivo (memoria.json, por usuario, en el servidor: sobrevive
# recarga, logout y cambio de máquina).
#
# Catálogo: clave → (validador, descripción i18n-key para Mi perfil).
# - sin_torta: True — nunca más un gráfico de torta/donut para este usuario.
# - margen_pin_umbral: N — productos con margen teórico < N% fijados arriba
#   donde ya se listan márgenes (con datos ya calculados, nada nuevo).
# - orden_home: [bloques] — el orden de los bloques del Inicio (P19·B).
# - widgets: {seccion: [w]} — los bloques visuales pedidos por chat (P19·C).
# - nota:<texto libre> vive en "preferencias" (set_pref), no acá.

BLOQUES_HOME = ["cards", "decisiones", "oportunidades", "feed", "metricas", "plata"]


def _val_bool(v):
    return bool(v)


def _val_umbral(v):
    n = float(v)
    if not (0 < n < 100):
        raise ValueError("el umbral tiene que ser un porcentaje entre 0 y 100")
    return n


def _val_orden(v):
    if not isinstance(v, list) or sorted(v) != sorted(BLOQUES_HOME):
        raise ValueError(f"orden_home tiene que ser una permutación de {BLOQUES_HOME}")
    return list(v)


def _val_widgets(v):
    if not isinstance(v, dict):
        raise ValueError("widgets tiene que ser {seccion: [widgets]}")
    return v


VISTA_CATALOGO = {
    "sin_torta": _val_bool,
    "margen_pin_umbral": _val_umbral,
    "orden_home": _val_orden,
    "widgets": _val_widgets,
}


def vista(usuario: str) -> dict:
    """Las preferencias de vista efectivas del usuario (solo claves del catálogo)."""
    data = _load()
    u = _usuario(data, usuario)
    return dict(u.get("vista") or {})


def set_vista(usuario: str, clave: str, valor) -> dict:
    """Setea UNA preferencia de vista validada. Lanza ValueError si la clave no
    existe en el catálogo o el valor no valida — el que llama decide qué decir."""
    if clave not in VISTA_CATALOGO:
        raise ValueError(f"preferencia desconocida: {clave!r} "
                         f"(catálogo: {', '.join(sorted(VISTA_CATALOGO))})")
    valor = VISTA_CATALOGO[clave](valor)
    data = _load()
    u = _usuario(data, usuario)
    u.setdefault("vista", {})[clave] = valor
    _save(data)
    return dict(u["vista"])


def borrar_vista(usuario: str, clave: str) -> bool:
    """Borra una preferencia de vista (o una nota de 'preferencias'). True si existía."""
    data = _load()
    u = _usuario(data, usuario)
    if clave in (u.get("vista") or {}):
        del u["vista"][clave]
        _save(data)
        return True
    if clave in (u.get("preferencias") or {}):
        del u["preferencias"][clave]
        _save(data)
        return True
    return False


def aprobar_categoria(usuario: str, categoria: str) -> None:
    data = _load()
    u = _usuario(data, usuario)
    if categoria not in u["categorias_auto"]:
        u["categorias_auto"].append(categoria)
    _save(data)


def marcar_dato_cargado(usuario: str, dato: str) -> None:
    data = _load()
    u = _usuario(data, usuario)
    if dato not in u["datos_cargados"]:
        u["datos_cargados"].append(dato)
    _save(data)


def registrar_recomendacion(usuario: str, texto: str) -> dict:
    data = _load()
    u = _usuario(data, usuario)
    rec = {"id": len(u["recomendaciones"]) + 1, "texto": texto, "resultado": None}
    u["recomendaciones"].append(rec)
    _save(data)
    return rec


def registrar_resultado(usuario: str, rec_id: int, resultado: str) -> None:
    data = _load()
    u = _usuario(data, usuario)
    for r in u["recomendaciones"]:
        if r["id"] == rec_id:
            r["resultado"] = resultado
    _save(data)


def agregar_archivo_libre(usuario: str, nombre: str, descripcion: str) -> None:
    data = _load()
    u = _usuario(data, usuario)
    u.setdefault("archivos", []).append({"nombre": nombre, "descripcion": descripcion})
    _save(data)


def agregar_objetivo(usuario: str, objetivo: str) -> None:
    data = _load()
    u = _usuario(data, usuario)
    if objetivo not in u["objetivos"]:
        u["objetivos"].append(objetivo)
    _save(data)


# --- Hechos sueltos ("acordate que...") ----------------------------------------
# Lo que la persona cuenta de pasada y no entra en ningún catálogo cerrado: un
# dato del negocio, la costumbre de un cliente, algo de su función. Cada uno
# queda con el ROL bajo el que se dijo (para que a un empleado de piso no le
# vuelva una nota que el dueño dejó en otro contexto — memoria privada de cada
# usuario, pero FILTRADA por rol) y con una CONFIANZA:
#   - 'confirmado': la persona lo dijo directo ("acordate que...") o tocó
#     confirmar. Es lo que Ángela puede usar como verdad.
#   - 'dudoso': Ángela lo propuso sola de algo mencionado al pasar (tool
#     'recordar_hecho') y todavía espera el toque de confirmación — nada queda
#     como verdad sin que una persona lo confirme.
#
# `categoria` es la clave de identidad opcional: dos hechos con la misma
# categoria son LA MISMA nota (el segundo actualiza al primero, como
# recordar_preferencia); sin categoria, cada mención es un hecho nuevo salvo
# que el texto sea idéntico a uno ya guardado.

def _norm_hecho(s) -> str:
    return " ".join((s or "").strip().lower().split())


def agregar_hecho(usuario: str, texto: str, *, categoria: str | None = None,
                  rol: str | None = None, fuente: str = "explicito",
                  confianza: str = "confirmado") -> tuple[dict, str]:
    """Guarda un hecho suelto. Devuelve (hecho, cambio) con cambio en
    {'added','updated','existing'} — es lo que pinta el chip en el frontend."""
    texto = (texto or "").strip()
    if not texto:
        raise ValueError("el hecho no puede estar vacío")
    if confianza not in ("confirmado", "dudoso"):
        raise ValueError(f"confianza desconocida: {confianza!r}")
    data = _load()
    u = _usuario(data, usuario)
    hechos = u.setdefault("hechos", [])
    cat_norm = _norm_hecho(categoria) if categoria else None
    if cat_norm:
        existente = next((h for h in hechos
                          if _norm_hecho(h.get("categoria")) == cat_norm), None)
    else:
        existente = next((h for h in hechos if not h.get("categoria")
                          and _norm_hecho(h.get("texto")) == _norm_hecho(texto)), None)
    ahora = hoy().isoformat()
    if existente:
        if _norm_hecho(existente.get("texto")) == _norm_hecho(texto):
            _save(data)
            return existente, "existing"
        existente.update(texto=texto, rol=rol or existente.get("rol"),
                         fuente=fuente, confianza=confianza, actualizado_en=ahora)
        _save(data)
        return existente, "updated"
    hecho = {
        "id": "h" + secrets.token_hex(4), "texto": texto,
        "categoria": categoria or None, "rol": rol, "fuente": fuente,
        "confianza": confianza, "creado_en": ahora, "actualizado_en": ahora,
    }
    hechos.append(hecho)
    _save(data)
    return hecho, "added"


def listar_hechos(usuario: str, rol: str | None = None, ver_todo: bool = False) -> list[dict]:
    """Los hechos de este usuario. Con `rol` y sin `ver_todo`, sólo los dichos
    bajo ese rol (más los sin rol — notas de alcance general). `ver_todo=True`
    es para el dueño: su propia memoria, completa, sin recorte por rol."""
    hechos = get(usuario).get("hechos", [])
    if ver_todo or not rol:
        return list(hechos)
    return [h for h in hechos if not h.get("rol") or h["rol"] == rol]


def confirmar_hecho(usuario: str, hecho_id: str) -> dict | None:
    """Pasa un hecho 'dudoso' (propuesto por la tool) a 'confirmado'."""
    data = _load()
    u = _usuario(data, usuario)
    for h in u.get("hechos", []):
        if h.get("id") == hecho_id:
            h["confianza"] = "confirmado"
            _save(data)
            return h
    return None


def borrar_hecho(usuario: str, hecho_id: str) -> bool:
    data = _load()
    u = _usuario(data, usuario)
    antes = len(u.get("hechos", []))
    u["hechos"] = [h for h in u.get("hechos", []) if h.get("id") != hecho_id]
    if len(u["hechos"]) != antes:
        _save(data)
        return True
    return False
