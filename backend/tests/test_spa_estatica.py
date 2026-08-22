"""El catch-all de la SPA no puede responder HTML cuando piden un .js.

Regresión de la pantalla en blanco en Render: el navegador pedía
/assets/index-HASH.js (hash de un deploy anterior) y FastAPI devolvía
index.html con MIME text/html.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

from core import spa_estatica as spa

TENANT_PAPASUD = True


def test_es_asset_js_css_sw():
    assert spa.es_asset("assets/index-D-dmM4ks.js") is True
    assert spa.es_asset("/assets/index-CU0CoDKJ.css") is True
    assert spa.es_asset("sw.js") is True
    assert spa.es_asset("fonts/foo.woff2") is True


def test_ruta_spa_no_es_asset():
    assert spa.es_asset("") is False
    assert spa.es_asset("mapa") is False
    assert spa.es_asset("index.html") is False


def test_resolver_asset_inexistente_es_404(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>x</title>", encoding="utf-8")
    kind, path, _cc = spa.resolver(str(tmp_path), "assets/index-VIEJO.js")
    assert kind == "404"
    assert path is None


def test_resolver_js_existente_es_file(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    assets = tmp_path / "assets"
    assets.mkdir()
    js = assets / "index-abc.js"
    js.write_text("console.log(1)", encoding="utf-8")
    kind, path, cc = spa.resolver(str(tmp_path), "assets/index-abc.js")
    assert kind == "file"
    assert path == str(js)
    assert "immutable" in cc


def test_resolver_ruta_app_cae_al_index(tmp_path):
    idx = tmp_path / "index.html"
    idx.write_text("<!doctype html>", encoding="utf-8")
    kind, path, cc = spa.resolver(str(tmp_path), "mapa")
    assert kind == "index"
    assert path == str(idx)
    assert cc == "no-cache"


def test_cache_control_html_y_sw_sin_cache():
    assert spa.cache_control("index.html") == "no-cache"
    assert spa.cache_control("sw.js") == "no-cache"
    assert spa.cache_control("") == "no-cache"


def test_sw_no_cae_a_index_html_en_assets():
    """El fallback a index.html tiene que ser sólo para navegaciones, no para .js."""
    raiz = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    src = open(os.path.join(raiz, "frontend", "public", "sw.js"), encoding="utf-8").read()
    assert "esAsset" in src
    assert "esHtml" in src
    assert "papasud-v2-" in src
    # El catch que devolvía HTML para CUALQUIER fetch fallido es lo que
    # envenenaba /assets/*.js. Tiene que quedar acotado a navegación.
    assert src.count('caches.match("/index.html")') == 1


def test_http_asset_inexistente_da_404_no_html():
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raiz = os.path.dirname(backend)
    data = os.path.join(raiz, "data-papasud")
    dist = tempfile.mkdtemp(prefix="polpilot-spa-")
    os.makedirs(os.path.join(dist, "assets"))
    with open(os.path.join(dist, "index.html"), "w", encoding="utf-8") as f:
        f.write('<!doctype html><script type="module" src="/assets/index-NUEVO.js"></script>')
    with open(os.path.join(dist, "assets", "index-NUEVO.js"), "w", encoding="utf-8") as f:
        f.write("console.log('ok')")
    env = {**os.environ,
           "POLPILOT_TENANT": "papasud",
           "POLPILOT_DATA_DIR": data,
           "POLPILOT_STATIC_DIR": dist,
           "POLPILOT_DEMO_TODAY": "2026-08-22",
           "PYTHONIOENCODING": "utf-8"}
    code = r"""
from fastapi.testclient import TestClient
import main
c = TestClient(main.app)

# hash viejo: 404, NUNCA text/html
r = c.get("/assets/index-VIEJO.js")
assert r.status_code == 404, r.status_code
assert "text/html" not in (r.headers.get("content-type") or "")
assert not (r.text or "").lstrip().lower().startswith("<!doctype")

# hash actual: javascript
r2 = c.get("/assets/index-NUEVO.js")
assert r2.status_code == 200
assert "javascript" in (r2.headers.get("content-type") or "")
assert "immutable" in (r2.headers.get("cache-control") or "")

# ruta de la SPA: sí, HTML
r3 = c.get("/mapa")
assert r3.status_code == 200
assert "text/html" in (r3.headers.get("content-type") or "")
assert "no-cache" in (r3.headers.get("cache-control") or "")

# el index también revalida
r4 = c.get("/")
assert r4.status_code == 200
assert "no-cache" in (r4.headers.get("cache-control") or "")

# sw.js existente o 404, nunca HTML si no está
r5 = c.get("/sw.js")
assert r5.status_code == 404
assert "text/html" not in (r5.headers.get("content-type") or "")
print("OK")
"""
    r = subprocess.run([sys.executable, "-c", code], cwd=backend, env=env,
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0 and "OK" in r.stdout, (r.stdout[-800:], r.stderr[-800:])
