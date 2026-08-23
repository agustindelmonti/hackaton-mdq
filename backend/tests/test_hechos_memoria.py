"""
Memoria por hechos sueltos ("acordate que...") — la cara nueva de core/memoria.py
que hace que Ángela aprenda del negocio, no solo de la vista.

Cubre: alta/actualización/no-cambio (lo que pinta el chip en el frontend), el
recorte por rol al leer, la confirmación de un hecho 'dudoso' propuesto por la
tool, el borrado, y el atajo determinístico de frase explícita que corre ANTES
de tocar el modelo.
"""
from __future__ import annotations

import os

import pytest

# Este módulo es de esta instancia (Papasud): el guard de conftest lo deja pasar.
TENANT_PAPASUD = True

import angela
from core import memoria


@pytest.fixture(autouse=True)
def limpio():
    if os.path.exists(memoria.MEMORIA_JSON):
        os.remove(memoria.MEMORIA_JSON)
    usuario, rol = angela._usuario_actual(), angela._rol_actual()
    yield
    angela._set_sesion(usuario=usuario, rol=rol)
    if os.path.exists(memoria.MEMORIA_JSON):
        os.remove(memoria.MEMORIA_JSON)


# --- agregar_hecho: added / updated / existing --------------------------------

def test_agregar_hecho_nuevo_es_added():
    hecho, cambio = memoria.agregar_hecho("ruben", "el cliente López pide entrega a la tarde")
    assert cambio == "added"
    assert hecho["confianza"] == "confirmado"
    assert hecho["texto"] == "el cliente López pide entrega a la tarde"


def test_agregar_hecho_mismo_texto_es_existing():
    memoria.agregar_hecho("ruben", "el galpón 2 tiene la balanza descalibrada")
    _, cambio = memoria.agregar_hecho("ruben", "el galpón 2 tiene la balanza descalibrada")
    assert cambio == "existing"
    assert len(memoria.listar_hechos("ruben")) == 1


def test_agregar_hecho_misma_categoria_texto_distinto_es_updated():
    memoria.agregar_hecho("ruben", "sale a las 8", categoria="horario_carga")
    hecho, cambio = memoria.agregar_hecho("ruben", "sale a las 9", categoria="horario_carga")
    assert cambio == "updated"
    assert hecho["texto"] == "sale a las 9"
    assert len(memoria.listar_hechos("ruben")) == 1  # no duplicó, reemplazó


def test_agregar_hecho_vacio_rechaza():
    with pytest.raises(ValueError):
        memoria.agregar_hecho("ruben", "   ")


# --- listar_hechos: recorte por rol --------------------------------------------

def test_listar_hechos_filtra_por_rol():
    memoria.agregar_hecho("marcos", "el frigo 3 tarda más en enfriar", rol="Operario de frigorífico")
    memoria.agregar_hecho("marcos", "el margen de la exportación bajó", rol="Dueño")
    memoria.agregar_hecho("marcos", "hoy no vino el camión")  # sin rol: general

    propios = memoria.listar_hechos("marcos", rol="Operario de frigorífico")
    textos = {h["texto"] for h in propios}
    assert "el frigo 3 tarda más en enfriar" in textos
    assert "hoy no vino el camión" in textos
    assert "el margen de la exportación bajó" not in textos

    todo = memoria.listar_hechos("marcos", ver_todo=True)
    assert len(todo) == 3


# --- confirmar / borrar ---------------------------------------------------------

def test_confirmar_hecho_dudoso():
    hecho, _ = memoria.agregar_hecho("ruben", "el proveedor de bolsones cambió",
                                     fuente="tool", confianza="dudoso")
    assert hecho["confianza"] == "dudoso"
    confirmado = memoria.confirmar_hecho("ruben", hecho["id"])
    assert confirmado["confianza"] == "confirmado"


def test_borrar_hecho():
    hecho, _ = memoria.agregar_hecho("ruben", "algo para olvidar")
    assert memoria.borrar_hecho("ruben", hecho["id"]) is True
    assert memoria.listar_hechos("ruben") == []
    assert memoria.borrar_hecho("ruben", hecho["id"]) is False


# --- La tool de Ángela: mención al pasar queda DUDOSA, nunca confirmada sola ---

def test_tool_recordar_hecho_queda_dudoso():
    angela._set_sesion(usuario="ruben", rol="Encargado de depósito")
    result, accion = angela._run_tool("recordar_hecho", {"texto": "el galpón 1 gotea cuando llueve"})
    assert result["ok"] is True
    assert result["hecho"]["confianza"] == "dudoso"
    assert accion is None
    # y aparece filtrado por su propio rol al leer
    leido, _ = angela._run_tool("recuperar", {})
    assert any(h["texto"] == "el galpón 1 gotea cuando llueve" for h in leido["hechos"])


# --- La frase explícita: determinística, corre antes de llamar al modelo ------

def test_frase_explicita_guarda_confirmado_directo():
    angela._set_sesion(usuario="ruben", rol="Encargado de depósito")
    r = angela._intentar_recordar_explicito("Acordate que el cliente Fresh Import paga a 60 días")
    assert r is not None
    assert r["tool_events"][0]["result"]["hecho"]["confianza"] == "confirmado"
    assert r["tool_events"][0]["result"]["cambio"] == "added"
    hechos = memoria.listar_hechos("ruben", ver_todo=True)
    assert hechos[0]["texto"] == "el cliente Fresh Import paga a 60 días"
    assert hechos[0]["fuente"] == "explicito"


def test_frase_explicita_no_matchea_mensajes_comunes():
    angela._set_sesion(usuario="ruben", rol="Encargado de depósito")
    assert angela._intentar_recordar_explicito("cuánto stock hay en el galpón 2") is None
    # "recordame" sigue siendo del riel de recordatorios/tareas, no de hechos
    assert angela._intentar_recordar_explicito("recordame llamar al proveedor mañana") is None
