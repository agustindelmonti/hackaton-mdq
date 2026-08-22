"""
paths.py · UN solo lugar decide dónde viven los datos — la base del multi-tenant.

Esta instancia es **Papasud S.A.** (Mar del Plata): semilla de papa, cuatro
ubicaciones físicas, exportación. Sin env, apunta a `data-papasud/`.

POLPILOT_TENANT elige el seed de usuarios (auth.py) y la identidad visible.
POLPILOT_DATA_DIR aísla el directorio de datos por completo: dos instancias
nunca se pisan, ni por accidente.

NOTA SOBRE LOS DATOS: la empresa es real y el modelo sale de la Planilla de
movimientos 2026. Lo genera `data-papasud/generar.py`. Las personas del equipo
son inventadas. Ver el README.
"""
from __future__ import annotations

import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_DEFAULT = os.path.abspath(os.path.join(_HERE, "..", "..", "data-papasud"))

DATA_DIR = os.path.abspath(os.environ.get("POLPILOT_DATA_DIR") or _DEFAULT)
TENANT = os.environ.get("POLPILOT_TENANT", "papasud")

# Identidad visible de la instancia (el header/meta de la API la usa).
# `nombre_corto` es cómo la empresa se nombra a sí misma ante SUS clientes.
_IDENTIDAD = {
    "papasud": {
        "empresa": "Papasud S.A.",
        "nombre_corto": "Papasud",
        "fuente": "Planilla de stock + registros de campo · núcleo de verdad PolPilot",
        "logo": "/logos/papasud.svg",
    },
}
_ACTUAL = _IDENTIDAD.get(TENANT, _IDENTIDAD["papasud"])
EMPRESA = _ACTUAL["empresa"]
NOMBRE_CORTO = _ACTUAL["nombre_corto"]
FUENTE = _ACTUAL["fuente"]
LOGO = _ACTUAL["logo"]

# Idioma default del tenant (config por env, NO hardcodeado por nombre de tenant).
# La preferencia POR USUARIO (perfiles.idioma_de) pisa este default. El inglés
# importa: el 25–30% del negocio es exportación y la documentación viaja en inglés.
IDIOMAS = ("es", "en")
DEFAULT_LANG = os.environ.get("POLPILOT_DEFAULT_LANG", "es")
if DEFAULT_LANG not in IDIOMAS:
    DEFAULT_LANG = "es"
