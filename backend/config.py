"""
config.py · El switch central — de dónde sale el modelo que usa Ángela.

TRES MODOS, UNA SOLA VARIABLE (`LLM_MODE`):

    gateway    → Claude por el AI Gateway de Vercel (V0). Es el modo de la demo.
                 Usa AI_GATEWAY_API_KEY y un modelo prefijado por proveedor
                 (`anthropic/claude-sonnet-5`).
    anthropic  → Claude por la API directa de Anthropic (ANTHROPIC_API_KEY).
    simulado   → sin modelo: el router determinista por intenciones que vive en
                 angela._fallback y los intérpretes por patrones de voz y
                 movimientos. El sistema NO se cae ni se degrada a un error:
                 responde con los mismos módulos core, sólo entiende menos
                 lenguaje.

POR QUÉ EL GATEWAY ES UN CAMBIO DE TRANSPORTE Y NADA MÁS

El AI Gateway de Vercel expone LA MISMA Messages API de Anthropic. Cambian dos
cosas y ninguna es lógica de negocio:

    · `base_url` → https://ai-gateway.vercel.sh   (el SDK agrega /v1/messages)
    · `api_key`  → la del Gateway, no la de Anthropic
    · el `model` viaja prefijado por proveedor: "anthropic/claude-sonnet-5"

Por eso las 48 tools, el tool-use forzado de visión y de voz, el prompt caching
y los guardarraíles funcionan exactamente igual: el SDK es el mismo objeto.

Doc: https://vercel.com/docs/ai-gateway/sdks-and-apis/anthropic-messages-api

EL FALLBACK NO ES DECORATIVO. Si el sábado el Gateway no responde, `modo()`
sigue devolviendo lo que corresponde y cada borde tiene su camino determinista.
La demo no depende de que una red ajena esté de buen humor.
"""
from __future__ import annotations

import os

# La key vive en backend/.env (gitignored), nunca en el código. config es el
# switch central y todos lo importan primero, así que la carga vive acá.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass  # sin python-dotenv, las vars pueden venir del entorno igual

# En esta máquina la consulta WMI de Windows se cuelga indefinidamente, y
# platform.win32_ver() (Python 3.12+) la usa. El SDK de Anthropic llama a
# platform.system() al armar sus headers → la PRIMERA llamada real de Ángela
# quedaba colgada para siempre. Deshabilitamos solo la fuente WMI: al tirar
# OSError, _win32_ver cae en su propio fallback oficial (registro +
# sys.getwindowsversion), que da los mismos datos sin colgarse.
if os.name == "nt":
    import platform
    if hasattr(platform, "_wmi_query"):
        def _wmi_deshabilitado(*_a, **_k):
            raise OSError("WMI deshabilitado por PolPilot (se cuelga en esta máquina)")
        platform._wmi_query = _wmi_deshabilitado


# --- EL GATEWAY --------------------------------------------------------------
GATEWAY_BASE_URL = os.environ.get("AI_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh")

# El modelo del Gateway viaja PREFIJADO POR PROVEEDOR. Sonnet 5 es el default
# porque es el que el tier del Gateway habilita y el más rápido para chat en
# vivo con tool use. Se cambia por env sin tocar código.
GATEWAY_MODEL = os.environ.get("GATEWAY_MODEL", "anthropic/claude-sonnet-5")

# Modelo cuando se va por la API directa de Anthropic.
ANTHROPIC_MODEL = os.environ.get("ANGELA_MODEL",
                                 os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"))


def _key_gateway() -> str | None:
    # AI_GATEWAY_API_KEY es el nombre de la doc de Vercel; V0_API_KEY es alias.
    return os.environ.get("AI_GATEWAY_API_KEY") or os.environ.get("V0_API_KEY")


def llm_mode() -> str:
    """El transporte elegido, resuelto AHORA (no en import-time).

    Si `LLM_MODE` está seteado manda esa. Si no, se autodetecta por las keys
    presentes, con el Gateway primero: es el camino de la demo."""
    modo = (os.environ.get("LLM_MODE") or "").strip().lower()
    if modo in ("gateway", "anthropic", "mock", "simulado"):
        if modo == "gateway" and not _key_gateway():
            return "simulado"      # pidieron gateway y no hay key: no mentimos
        if modo == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
            return "simulado"
        return "simulado" if modo == "mock" else modo
    if _key_gateway():
        return "gateway"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    return "simulado"


def modo() -> str:
    """El modo de Ángela para el resto del sistema: 'claude' si hay un modelo
    real detrás (por el transporte que sea), 'simulado' si no.

    Todo el código existente pregunta por esto y no tiene por qué enterarse de
    si el transporte es el Gateway o la API directa."""
    return "simulado" if llm_mode() == "simulado" else "claude"


# Snapshot de import-time, sólo por compatibilidad. El código nuevo llama modo().
MODO = modo()


def cliente_llm(proposito: str = "chat"):
    """La ÚNICA fábrica de cliente del sistema. Devuelve `(client, modelo)`.

    `(None, None)` en modo simulado — cada borde tiene su camino determinista y
    ninguno explota por no tener modelo.

    `proposito` existe para que visión y voz puedan pedir un modelo distinto
    (por env) sin que ninguno instancie su propio cliente por las suyas: si
    mañana cambia el transporte, cambia acá y en ningún otro lado."""
    m = llm_mode()
    if m == "simulado":
        return None, None
    try:
        import anthropic
    except ImportError:
        return None, None

    if m == "gateway":
        client = anthropic.Anthropic(api_key=_key_gateway(), base_url=GATEWAY_BASE_URL)
        modelo = _modelo_gateway(proposito)
    else:
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        modelo = _modelo_anthropic(proposito)
    return client, modelo


def _modelo_gateway(proposito: str) -> str:
    override = {
        "vision": os.environ.get("POLPILOT_VISION_MODEL_GATEWAY"),
        "voz": os.environ.get("POLPILOT_VOZ_MODEL_GATEWAY"),
    }.get(proposito)
    return override or GATEWAY_MODEL


def _modelo_anthropic(proposito: str) -> str:
    override = {
        "vision": os.environ.get("POLPILOT_VISION_MODEL"),
        "voz": os.environ.get("POLPILOT_VOZ_MODEL"),
    }.get(proposito)
    return override or ANTHROPIC_MODEL


def modelo_visible() -> str:
    """Qué modelo está corriendo, para el health y para la pantalla. Que se vea
    el transporte importa: en la demo alguien va a preguntar por dónde sale."""
    m = llm_mode()
    if m == "gateway":
        return f"{GATEWAY_MODEL} (Vercel AI Gateway)"
    if m == "anthropic":
        return f"{ANTHROPIC_MODEL} (Anthropic API)"
    return "router determinista (sin modelo)"


# --- ROUTING DE MODELOS ------------------------------------------------------
# Apagado: un solo modelo para todo. El costo de Sonnet es insignificante frente
# a perder una respuesta en cámara. Se prende cuando haya datos de uso reales.
ROUTING_ACTIVO = False

MODELO_VALIDACION = ANTHROPIC_MODEL   # compat con el código que lo lee directo

MODELOS_DISPONIBLES = {
    "anthropic/claude-sonnet-5": "Sonnet 5 por el Gateway (default de la demo)",
    "claude-sonnet-4-6": "Sonnet 4.6 (API directa)",
    "claude-haiku-4-5": "Haiku 4.5 (barato, tareas simples)",
    "claude-opus-4-8": "Opus 4.8 (razonamiento pesado)",
}

# Tools de bajo razonamiento → ruteables a un modelo barato si se prende routing.
TOOLS_SIMPLES = {
    "navegar_a", "modificar_vista", "crear_pestana", "crear_widget", "plata_en",
    "buscar_productos", "top_inmovilizado", "listar_grupo", "recordar", "recuperar",
    "cancelar_mensaje", "recuperar_contexto_negocio", "stock_ubicaciones",
}


def modelo_para(tools_pedidas: set[str] | None = None) -> str:
    """El modelo del chat. Con routing apagado, el del transporte activo."""
    _, modelo = cliente_llm("chat")
    return modelo or MODELO_VALIDACION


# --- PROMPT CACHING ----------------------------------------------------------
# El system prompt + el contexto estable del negocio se repiten en cada request.
# Marcarlos cacheables = pagar una fracción del input en las lecturas. El
# Gateway soporta el mismo header que la API directa.
PROMPT_CACHE = True
