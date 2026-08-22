"""Servir el frontend compilado sin disfrazar un 404 de HTML.

Vite pone hash en `/assets/index-XXXX.js`. Después de un deploy esa URL
deja de existir. Si el catch-all de la SPA responde `index.html`
(`text/html`) el navegador revienta el `<script type="module">`:

    Expected a JavaScript-or-Wasm module script but the server responded
    with a MIME type of "text/html".

Eso es exactamente la pantalla en blanco del demo en Render.
"""
from __future__ import annotations

import os

ASSET_EXTS = frozenset({
    ".js", ".mjs", ".cjs", ".css", ".map", ".wasm",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".json", ".txt", ".webmanifest", ".xml",
})


def _rel(spa_path: str) -> str:
    return (spa_path or "").lstrip("/").replace("\\", "/")


def es_asset(spa_path: str) -> bool:
    """True si esta URL tiene que ser un archivo, nunca el HTML de la SPA."""
    p = _rel(spa_path)
    if not p:
        return False
    if p.startswith("assets/") or p == "sw.js":
        return True
    ext = os.path.splitext(p)[1].lower()
    return ext in ASSET_EXTS


def cache_control(spa_path: str) -> str:
    p = _rel(spa_path)
    if not p or p == "index.html" or p.endswith(".html") or p == "sw.js":
        # El HTML y el SW tienen que revalidar: si se cachean, el hash del
        # bundle queda pegado y volvemos al MIME text/html.
        return "no-cache"
    if p.startswith("assets/"):
        return "public, max-age=31536000, immutable"
    return "public, max-age=3600"


def resolver(static_dir: str, spa_path: str) -> tuple[str, str | None, str]:
    """Qué hacer con un GET que no matcheó `/api/...`.

    Devuelve `(kind, path, cache_control)`:
      · `file`  — el archivo existe, servirlo
      · `index` — ruta de la SPA, caer al index.html
      · `404`   — pedían un asset que no está; NO devolver HTML
    """
    raiz = os.path.normpath(os.path.abspath(static_dir))
    rel = _rel(spa_path)
    candidato = os.path.normpath(os.path.join(raiz, rel)) if rel else raiz
    if not (candidato == raiz or candidato.startswith(raiz + os.sep)):
        return ("404", None, "no-cache")
    if rel and os.path.isfile(candidato):
        return ("file", candidato, cache_control(rel))
    if es_asset(rel):
        return ("404", None, "no-cache")
    index = os.path.join(raiz, "index.html")
    return ("index", index, cache_control("index.html"))
