import os
import shutil
import tempfile

import pytest

# ESTA RAMA TIENE UN SOLO TENANT: papasud.
#
# La suite venía apuntada al tenant "piloto" (Supermercados Horizonte, usuarios
# emilio/paula/vendedor/deposito) y sembraba su data dir desde `data-demo/`. En
# este repositorio no existe ninguno de los dos: ni el directorio ni el módulo
# de usuarios. Resultado: `pytest` moría al COLECTAR —un FileNotFoundError en
# conftest— y la suite entera estaba muerta sin que se notara, porque el error
# no se parece a un test que falla.
#
# Ahora el data dir de la suite es un directorio TEMPORAL sembrado desde
# `data-papasud/`. Los tests escriben y hasta reemplazan datasets enteros:
# jamás sobre el seed versionado.
#
# Los tests heredados que necesitan usuarios del piloto (emilio, paula, marta,
# aldo…) no pueden correr acá y se saltean solos con su motivo — ver el guard
# de abajo. Los que prueban el núcleo compartido (fechas, validación,
# normalización, importer, i18n) corren igual y siguen valiendo.
os.environ.setdefault("POLPILOT_TENANT", "papasud")
# El "hoy" del dataset está congelado: sin esto los tests de brotación, análisis
# por vencer y días en tránsito comparan contra la fecha real de la máquina.
os.environ.setdefault("POLPILOT_DEMO_TODAY", "2026-08-22")
if "POLPILOT_DATA_DIR" not in os.environ:
    _raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    _origen = os.path.join(_raiz, "data-papasud")
    _scratch = os.path.join(tempfile.mkdtemp(prefix="polpilot-suite-"), "data")
    os.makedirs(_scratch)
    # El catálogo y los catálogos del rubro: es lo que necesita cualquier test
    # que toque semilla. Todo lo demás (audit, staging, recordatorios) lo siembra
    # cada test — y sobre el temporal, jamás sobre el seed versionado.
    for _f in ("inventory.json", "catalogos.json", "apartados.json",
               "notas_equipo.json", "plantadas.json", "conocimiento_negocio.json"):
        _src = os.path.join(_origen, _f)
        if os.path.exists(_src):
            shutil.copy2(_src, os.path.join(_scratch, _f))
    os.environ["POLPILOT_DATA_DIR"] = _scratch


# Los usuarios de OTRO tenant. Un test que los pide no está roto: está escrito
# para una instancia que este repositorio no tiene. Se saltea diciendo por qué,
# que es distinto de fallar.
_USUARIOS_DE_OTRO_TENANT = {
    "emilio", "paula", "vendedor", "deposito", "aldo", "marta", "celeste",
    "nahuel", "norma", "ramon", "vanesa", "tomas",
}


# Los módulos de test que importan `cuentas` o `cobranza`: son las cuentas
# corrientes de un almacén y ese código NO EXISTE en esta rama. No es un test
# que falla, es un test de otro producto — se excluye de la colecta y se dice
# acá por qué, en vez de dejar `pytest` muriendo con once ImportError.
collect_ignore = [
    # (a) importan `cuentas` / `cobranza`: las cuentas corrientes de un almacén.
    #     Ese código no existe en esta rama.
    "test_analisis_cache.py", "test_bateria_nl.py", "test_consultas.py",
    "test_fable5_fixes.py", "test_grafo.py", "test_matriz_consultas.py",
    "test_modulos.py", "test_numeros_estables.py", "test_p38.py",
    "test_p42.py", "test_pdf_documentos.py",
    # (b) prueban SEMÁNTICA de almacén: productos por balanza (`venta_x_peso`),
    #     días de cobro, destinos de importación "venta", el detector de "más de
    #     10.000 unidades". Nada de eso existe en una semillera, y forzarlos a
    #     pasar sería falsificar la cobertura. Lo que SÍ importa de estos
    #     módulos —el núcleo compartido— lo cubre test_papasud_v3.py.
    "test_anomalias.py", "test_cruces.py", "test_esquema.py", "test_kpis.py",
    "test_quality.py", "test_staging.py", "test_ventas.py", "test_analisis.py",
    "test_sync.py", "test_p27.py", "test_p34.py",
    # (c) fixtures que arrancan pidiendo usuarios del piloto (emilio, paula…):
    #     el guard de abajo no llega a correr porque el error es del fixture.
    "test_authz.py", "test_conocimiento.py",
    # (d) apuntan a `data-demo/` (el dataset de otra instancia) o a constantes
    #     de config que quedaron atrás del modelo actual.
    "test_deploy_hardening.py", "test_arquitectura.py",
]


@pytest.fixture(autouse=True)
def _saltear_si_es_de_otro_tenant(request):
    """Saltea el test si su código nombra a un usuario que acá no existe."""
    fn = getattr(request.node, "function", None)
    import inspect
    mod = inspect.getmodule(fn) if fn else None
    # Un módulo escrito PARA Papasud se declara y no pasa por el filtro. Sin
    # esto la heurística de abajo lo saltea entero: la palabra "deposito" es un
    # usuario del piloto Y una sección de esta app.
    if getattr(mod, "TENANT_PAPASUD", False):
        yield
        return
    fuente = ""
    try:
        fuente = (inspect.getsource(fn) if fn else "") + (inspect.getsource(mod) if mod else "")
    except (OSError, TypeError):
        pass
    for u in _USUARIOS_DE_OTRO_TENANT:
        if f'"{u}"' in fuente or f"'{u}'" in fuente:
            pytest.skip(f"escrito para el tenant piloto (usuario '{u}'), "
                        f"que no existe en la instancia Papasud")
    yield


@pytest.fixture(autouse=True)
def _analisis_cache_limpio():
    """P11·B4: el cache de análisis jamás se filtra entre tests — ni siquiera
    cuando un test reescribe los JSON a mano sin pasar por los hooks."""
    from core import analisis_cache
    analisis_cache.limpiar()
    yield
    analisis_cache.limpiar()


@pytest.fixture
def articulos_raw():
    """Cuatro artículos que cubren cada categoría de issue + uno sano."""
    return [
        # fantasma: anulado con stock vivo
        {"codigo": 1, "descripcion": "QUESO FANTASMA", "estado": "anulado",
         "stock": 10, "costo_iva": 100, "pvp": 200, "inmovilizado": 0},
        # negativo: stock < 0
        {"codigo": 2, "descripcion": "MASA CREMOSA", "estado": "activo",
         "stock": -5, "costo_iva": 50, "pvp": 80, "inmovilizado": 0},
        # sin precio: activo sin pvp, con plata parada
        {"codigo": 3, "descripcion": "MANTECA SIN PRECIO", "estado": "activo",
         "stock": 4, "costo_iva": 100, "pvp": None, "inmovilizado": 400},
        # calibre: peso fuera de rango
        {"codigo": 4, "descripcion": "JAMON FETEADO", "estado": "activo",
         "stock": 2, "costo_iva": 500, "pvp": 900, "inmovilizado": 1000,
         "venta_x_peso": True, "cota_inf": 4, "cota_sup": 6, "valor_peso": 3},
        # costo viejo: > 365 días
        {"codigo": 5, "descripcion": "ACEITE VIEJO", "estado": "activo",
         "stock": 3, "costo_iva": 200, "pvp": 300, "inmovilizado": 600,
         "antiguedad_costo_dias": 400},
        # sano: nada
        {"codigo": 6, "descripcion": "LECHE OK", "estado": "activo",
         "stock": 8, "costo_iva": 90, "pvp": 130, "inmovilizado": 720,
         "antiguedad_costo_dias": 30},
    ]
