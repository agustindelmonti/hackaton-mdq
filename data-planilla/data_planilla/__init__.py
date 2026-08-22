"""Modelo de datos calcado de la Planilla de movimientos 2026.xls.

Vive en un subtree aparte de `data-papasud/` para no romper el seed sintético
de la demo. El libro real no es un stock: es un remito con líneas, lotes
namespaced por chacra y un código visual (bolsa + hilo).
"""
from . import dominio, modelo

__all__ = ["dominio", "modelo"]
