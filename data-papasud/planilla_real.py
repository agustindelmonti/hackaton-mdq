"""
planilla_real.py · La planilla de Papasud entra como está, con la mugre adentro.

Esto NO es un generador de datos sintéticos. Lee la `Planilla de movimientos
2026.xls` que nos dieron los dueños —doce solapas, hechas a mano, editadas por
varias personas— y la convierte en el libro de movimientos canónico que define
`docs/CONTRATO_DATOS.md`.

POR QUÉ IMPORTA QUE SEA LA PLANILLA DE VERDAD

  Si el dueño pregunta «¿tengo 1.200 bolsas de Spunta?» y el sistema responde
  con el remito 1009 del 29/03 atrás, lo verifica en la sala en diez segundos.
  Con datos inventados, no.

DOS REGLAS AL IMPORTAR

  1. **Nada se corrige solo.** Lo que está mal se marca, se cuenta y se muestra
     con el número de fila del Excel. Corregirlo en silencio sería repetir el
     problema que vinimos a resolver: un dato que cambió y nadie sabe quién.

  2. **Lo que la planilla explica no es un error.** El remito 829 declara 37
     bolsas y 925 kg — 25 kg por bolsa, imposible. Pero la observación dice
     «bolsa papasud x 25kg»: es otra bolsa, no un error de carga. Un detector
     que marca eso pierde a la primera al que conoce la operación.

PROVISIONAL, Y A PROPÓSITO
  El importador de verdad lo hace Agustín. Este módulo materializa el mismo
  contrato para que la capa de consulta pueda construirse en paralelo. Cuando
  el suyo escriba `data-papasud/real/`, esto se borra y nada más se entera.

    python data-papasud/planilla_real.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

# La consola de Windows viene en cp1252 y esto imprime flechas y acentos.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import pandas as pd
except ImportError:                                          # pragma: no cover
    sys.exit("Falta pandas. `pip install pandas xlrd openpyxl`")

AQUI = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(AQUI, "real")

# Los archivos que nos pasaron los dueños. Se busca en varios lugares porque en
# el equipo cada uno los tiene en una carpeta distinta.
CANDIDATOS = [
    os.environ.get("PAPASUD_PLANILLAS"),
    os.path.join(AQUI, "planillas-papasud"),
    os.path.join(AQUI, "..", "assets-origen", "planillas"),
    os.path.expanduser(r"~\OneDrive\Desktop\papaseud"),
    os.path.expanduser(r"~\Desktop\papaseud"),
]
ARCHIVO_MOV = "Planilla de movimientos 2026.xls"
ARCHIVO_MUESTRAS = "Muestras pre-cosecha Oriente 2020.xlsx"


def _origen_archivos() -> str:
    for c in CANDIDATOS:
        if c and os.path.isfile(os.path.join(c, ARCHIVO_MOV)):
            return os.path.abspath(c)
    sys.exit(
        f"No encuentro '{ARCHIVO_MOV}'. Poné la carpeta en PAPASUD_PLANILLAS "
        f"o copiala a {os.path.join(AQUI, 'planillas-papasud')}."
    )


# ---------------------------------------------------------------------------
# El mapa de solapas. Cada solapa de la planilla ES un tipo de movimiento: así
# es como ellos separan el trabajo, y respetarlo hace que el sistema hable su
# idioma en vez de obligarlos a aprender el nuestro.
# ---------------------------------------------------------------------------
SOLAPAS = {
    "Ingreso Tolvas Santa Ana": "ingreso_tolva",
    "Ingreso  Trevelin": "ingreso_multiplicacion",       # sí, dos espacios
    "De campo a Frío": "campo_a_frio",
    "Env a Frio": "envio_a_frio",
    "Ret Frio": "retiro_de_frio",
    "Entregas a clientes 2026": "entrega_cliente",
}

# Las solapas que todavía no entran, con el motivo escrito. Declararlo es más
# honesto que dejar que parezca que importamos todo.
SOLAPAS_PENDIENTES = {
    "P.Chica": "cuadro cruzado por destino (Frigopap/Sasula/Belmonte/Paraguay), no filas de movimiento",
    "Stocks": "resumen de producción por lote, no movimientos — alimenta superficie y rinde",
    "SP": "tablero de stock y ventas de Spunta por lote, armado a mano",
    "DJ Panc": "declaración jurada a Pancani — planilla vacía en esta copia",
    "Transportes": "solapa vacía",
    "Frigoríficos": "solapa vacía",
}

PLANTA = {"tipo": "planta", "id": "planta_mdp"}
GALPON = {"tipo": "galpon", "id": "galpon_mdp"}

# Los frigoríficos que aparecen en los datos reales. Son subcontratados: por eso
# hay que trackear cada movimiento por lugar — hay que pagarles por kilo movido.
FRIGORIFICOS = {
    "dospanca": "Dospanca",
    "pancani": "Pancani",
    "sasula": "Sasula (Balcarce)",
    "belmonte": "Belmonte",
    "cecive": "Cecive",
    "frigopap": "Frigopap",
    "teramal": "Teramal",
}

CAMPOS = {
    "santa_ana": {"nombre": "Santa Ana", "pivotes": ["A", "B"]},
    "marisol": {"nombre": "Marisol", "pivotes": []},
    "trevelin": {"nombre": "Trevelin", "pivotes": []},
    "oriente": {"nombre": "Oriente", "pivotes": []},
    "pampa_chica": {"nombre": "Pampa Chica", "pivotes": []},
}

# Del plano Santa Ana 2023: el pivote se divide en cuadrantes y cada cuadrante
# tiene sus lotes. Es la jerarquía física que el mapa tiene que mostrar.
PLANO_SANTA_ANA = {
    "A": {"cuadrantes": [1, 2, 3, 4],
          "lotes": ["L30", "L35", "L37", "L38", "L41", "L42", "L43", "L44", "L45", "L55"]},
    "B": {"cuadrantes": [5, 6, 7, 8],
          "lotes": ["L31", "L32", "L33", "L34", "L34B", "L36", "L37B", "L54",
                    "L71", "L72B", "L75", "L77", "L79"]},
}

# El DTV ampara el tránsito entre establecimientos. Sólo tres solapas tienen
# columna para cargarlo: reclamarlo en las otras sería pedir un dato que la
# planilla nunca previó.
SOLAPAS_CON_DTV = {"Ingreso Tolvas Santa Ana", "De campo a Frío",
                   "Entregas a clientes 2026"}

CATEGORIAS_VALIDAS = {"inicial 1", "inicial 2", "inicial 3"}
CALIBRES = {
    "exportacion": "exportacion",
    "expo buena": "exportacion",
    "desc.expo": "descarte de exportacion",
    "desc.paraguay": "descarte paraguay",
    "sin chicas": "sin chicas",
    "granel": "granel",
    "recibo": "recibo",
}

# Un kilo por bolsa fuera de esta banda no existe en la operación: la bolsa de
# semilla pesa entre 47 y 54 kg, y el máximo legal a campo son 50 (INASE 171/2000
# art. 23). Damos margen para el redondeo de la báscula.
KG_BOLSA_MIN, KG_BOLSA_MAX = 45.0, 56.0

COLORES_BOLSA = ["blanca", "roja", "verde", "negra", "naranja", "amarilla",
                 "marron", "celeste", "varias", "gris", "azul"]
COLORES_HILO = ["blanco", "negro", "verde", "amarillo", "rojo", "celeste",
                "marron", "azul", "naranja"]


# ---------------------------------------------------------------------------
# Normalizadores
# ---------------------------------------------------------------------------
def _sn(s) -> str:
    """Sin acentos, minúscula, espacios colapsados."""
    if s is None:
        return ""
    t = unicodedata.normalize("NFKD", str(s))
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().lower()


def _texto(v) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    t = str(v).strip()
    return t or None


def _numero(v) -> float | None:
    """Kilos que vienen como '29080 kg', '29.080', 29080.0 o basura."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    t = re.sub(r"[^\d,.\-]", "", str(v))
    if not t:
        return None
    # 49,87 → 49.87 · 1.234 con punto de miles no aparece en esta planilla
    if "," in t and "." not in t:
        t = t.replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def _fecha(v) -> str | None:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        return pd.Timestamp(v).date().isoformat()
    except Exception:
        return None


def _lote(v) -> str | None:
    """El lote es SIEMPRE string: hay lotes '55 b', 'g1', 'L37B'."""
    t = _texto(v)
    if t is None:
        return None
    t = t.strip()
    if t.endswith(".0"):
        t = t[:-2]
    return t.lower()


_RE_DTV = re.compile(r"(\d{7,9})\s*-\s*(\d)")


def _dtv(*fuentes) -> str | None:
    for f in fuentes:
        t = _texto(f)
        if not t:
            continue
        m = _RE_DTV.search(t)
        if m:
            return f"{m.group(1)}-{m.group(2)}"
    return None


def _transporte(v) -> tuple[str | None, str | None]:
    """'camillo/mario' → (camillo, mario) · 'cerone(sotelo)' → (cerone, sotelo).

    'serantes-vera' queda entero: así lo nombran ellos y así lo listaron.
    """
    t = _texto(v)
    if not t:
        return None, None
    t = _sn(t)
    t = t.replace("((", "(")                      # 'cerone((raphael)' — se les fue
    m = re.match(r"^([^(/]+)[(/]\s*([^)/]+)\)?\s*$", t)
    if m:
        return m.group(1).strip(" -()"), m.group(2).strip(" -()")
    return t.strip(" -()"), None


def _colores(obs: str | None) -> tuple[str | None, str | None]:
    """'bolsa blanca-hilo negro', 'b.roja-h.blanco', 'b.b nueva-h.b.' …"""
    if not obs:
        return None, None
    o = _sn(obs)
    bolsa = hilo = None
    mb = re.search(r"\bb(?:olsa|\.)?\s*([a-z]+)", o)
    if mb and mb.group(1) in COLORES_BOLSA:
        bolsa = mb.group(1)
    mh = re.search(r"\bh(?:ilo|\.)?\s*([a-z]+)", o)
    if mh and mh.group(1) in COLORES_HILO:
        hilo = mh.group(1)
    return bolsa, hilo


# El texto libre donde vive el origen o el destino cuando la columna no lo trae.
_LUGARES = [
    ("planta_mdp", "planta", r"\bplanta\b"),
    ("galpon_mdp", "galpon", r"\bgalp[oó]n\b"),
    ("dospanca", "frigorifico", r"\bdospanca\b"),
    ("cecive", "frigorifico", r"\bcecive\b"),
    ("sasula", "frigorifico", r"\bsasula\b"),
    ("belmonte", "frigorifico", r"\bbelmonte\b"),
    ("frigopap", "frigorifico", r"\bfrigopap\b"),
    ("pancani", "frigorifico", r"\bpancani\b"),
    ("teramal", "frigorifico", r"\bteramal\b"),
    ("santa_ana", "campo", r"\b(santa ana|sta\.? ?ana|sta ana)\b"),
    ("pampa_chica", "campo", r"\bpampa chica\b"),
    ("paraguay", "cliente", r"\bparaguay\b"),
]


def _lugar(texto: str | None) -> dict | None:
    """Resuelve un nodo desde texto libre. Devuelve None si no se puede.

    Adivinar acá sería inventar de dónde salió la mercadería. Preferimos el
    hueco declarado: el que lee la pantalla ve que falta y lo completa.
    """
    if not texto:
        return None
    t = _sn(texto)
    for nid, tipo, patron in _LUGARES:
        if re.search(patron, t):
            return {"tipo": tipo, "id": nid}
    return None


def _ubic_columna(v) -> dict | None:
    """La columna Destino/Origen: 'dospanca', 'galpon', 'galpon-galpon', 'sasula balcarce'."""
    t = _sn(v)
    if not t:
        return None
    t = t.split("-")[0].strip() if t.count("-") and t.split("-")[0].strip() == t.split("-")[-1].strip() else t
    return _lugar(t) or {"tipo": "cliente", "id": _sn(v)}


# ---------------------------------------------------------------------------
# La lectura
# ---------------------------------------------------------------------------
class Importacion:
    def __init__(self, carpeta: str):
        self.carpeta = carpeta
        self.movimientos: list[dict] = []
        self.anomalias: list[dict] = []
        self._n = 0

    # -- anomalías ---------------------------------------------------------
    def _marcar(self, mov: dict | None, aid: str, detalle: str,
                fuente: dict | None = None, valor=None) -> None:
        if mov is not None:
            mov.setdefault("anomalias", []).append(aid)
        self.anomalias.append({
            "id": aid,
            "detalle": detalle,
            "valor": None if valor is None else str(valor),
            "movimiento": None if mov is None else mov["id"],
            "fuente": fuente or (mov or {}).get("fuente"),
        })

    # -- una fila ----------------------------------------------------------
    def _nuevo_id(self) -> str:
        self._n += 1
        return f"MOV-2026-{self._n:06d}"

    def _fila(self, tipo: str, solapa: str, fila_excel: int, r: dict) -> dict:
        mov = {
            "id": self._nuevo_id(),
            "tipo": tipo,
            "remito": None, "remito_id": None, "fecha": None,
            "lote": None, "variedad": None, "categoria": None, "calibre": None,
            "bolsas": None, "granel": False, "kg": None, "kg_prom": None,
            "origen": None, "destino": None,
            "transporte": None, "chofer": None, "dtv": None,
            "observaciones": None, "bolsa_color": None, "hilo_color": None,
            "fuente": {"archivo": ARCHIVO_MOV, "solapa": solapa, "fila_excel": fila_excel},
            "anomalias": [],
        }
        mov.update(r)
        return mov

    # -----------------------------------------------------------------
    def importar(self) -> None:
        ruta = os.path.join(self.carpeta, ARCHIVO_MOV)
        xl = pd.ExcelFile(ruta)
        vistas = {_sn(s): s for s in xl.sheet_names}

        for nombre, tipo in SOLAPAS.items():
            real = vistas.get(_sn(nombre))
            if real is None:
                print(f"  ! no encuentro la solapa '{nombre}'")
                continue
            df = xl.parse(real, header=0).dropna(how="all")
            antes = len(self.movimientos)
            getattr(self, f"_leer_{tipo}")(df, real)
            print(f"  · {real:<26} → {len(self.movimientos) - antes:>3} movimientos ({tipo})")

        self._cruces()

    # -- lectores por solapa ----------------------------------------------
    def _comun(self, r, solapa, fila, tipo, *, col_kg, col_obs, col_dtv=None,
               col_bolsas="Bolsas", col_cat=None, col_calibre=None):
        obs = _texto(r.get(col_obs))
        bolsas_raw = r.get(col_bolsas)
        bolsas = _numero(bolsas_raw)
        granel = False
        if bolsas is None and _texto(bolsas_raw):
            # 'granel', 'granel(chasis)', 'granel/acop.' — no es un número, es
            # la forma en que vino: suelta en la tolva.
            granel = "granel" in _sn(bolsas_raw)
        bcol, hcol = _colores(obs)
        remito = _texto(r.get("Remito"))
        if remito and remito.endswith(".0"):
            remito = remito[:-2]
        mov = self._fila(tipo, solapa, fila, {
            "remito": remito,
            "remito_id": f"{tipo}:{remito}" if remito else None,
            "fecha": _fecha(r.get("Fecha")),
            "lote": _lote(r.get("Lote")),
            "variedad": _sn(r.get("Variedad") if "Variedad" in r else r.get("Variedad ")) or None,
            "bolsas": int(bolsas) if bolsas and bolsas > 0 else None,
            "granel": granel,
            "kg": int(round(_numero(r.get(col_kg)) or 0)) or None,
            "observaciones": obs,
            "bolsa_color": bcol, "hilo_color": hcol,
        })
        mov["transporte"], mov["chofer"] = _transporte(r.get("Transporte"))
        mov["dtv"] = _dtv(r.get(col_dtv) if col_dtv else None, obs)

        if col_cat:
            self._categoria(mov, r.get(col_cat))
        if col_calibre:
            cal = _sn(r.get(col_calibre))
            mov["calibre"] = CALIBRES.get(cal, cal or None)
        return mov

    def _categoria(self, mov: dict, valor) -> None:
        """La columna Categoría es donde la planilla acumula todo lo que no
        tiene columna propia. Ahí está la mejor prueba de por qué necesitan
        esto: 'camara 2', 'solo chasis', '56 BOLSONES', un DTV suelto."""
        t = _texto(valor)
        if not t:
            return
        c = _sn(t).replace("inicial3", "inicial 3")
        if c in CATEGORIAS_VALIDAS:
            mov["categoria"] = c
            return
        if _RE_DTV.search(t):
            mov["dtv"] = mov["dtv"] or _dtv(t)
            self._marcar(mov, "dtv_en_columna_ajena",
                         "un DTV cargado en la columna Categoría", valor=t)
            return
        self._marcar(mov, "columna_con_otro_dato",
                     "la columna Categoría no trae una categoría", valor=t)

    # Ingreso Tolvas Santa Ana · lote → planta, a granel, la pesa la báscula
    def _leer_ingreso_tolva(self, df, solapa):
        for i, r in df.iterrows():
            if not _texto(r.get("Remito")):
                continue
            mov = self._comun(r, solapa, int(i) + 2, "ingreso_tolva",
                              col_kg="Kgs", col_obs="Observaciones",
                              col_dtv="Valor Flete / DTV")
            mov["origen"] = {"tipo": "lote", "id": mov["lote"]}
            mov["destino"] = dict(PLANTA)
            # 'idem' = lo mismo que la fila de arriba; 'paraguay' en la columna
            # del DTV es un destino, no un documento.
            flete = _sn(r.get("Valor Flete / DTV"))
            if flete and not mov["dtv"] and flete not in ("idem",):
                self._marcar(mov, "columna_con_otro_dato",
                             "la columna del DTV no trae un DTV", valor=flete)
            self._push(mov)

    # Ingreso Trevelin · la multiplicación inicial, con categoría de verdad
    def _leer_ingreso_multiplicacion(self, df, solapa):
        for i, r in df.iterrows():
            if not _texto(r.get("Remito")):
                continue
            mov = self._comun(r, solapa, int(i) + 2, "ingreso_multiplicacion",
                              col_kg="Kgs", col_obs=None, col_cat="categoria")
            mov["origen"] = {"tipo": "lote", "id": mov["lote"]}
            mov["destino"] = dict(PLANTA)
            mov["bolsa_color"] = _sn(r.get("Color bolsa")) or None
            mov["hilo_color"] = _sn(r.get("Color hilo")) or None
            mov["campo_origen"] = "trevelin"
            self._push(mov)

    # De campo a Frío · el lote va derecho al frigorífico, sin pasar por planta
    def _leer_campo_a_frio(self, df, solapa):
        for i, r in df.iterrows():
            if not _texto(r.get("Remito")):
                continue
            mov = self._comun(r, solapa, int(i) + 2, "campo_a_frio",
                              col_kg="Kgs.", col_obs="Observaciones / DTV")
            mov["origen"] = {"tipo": "lote", "id": mov["lote"]}
            mov["destino"] = _ubic_columna(r.get("Destino"))
            # La columna se llama «Cliente» y adentro hay un peso: '49,87 kg'.
            # Es el kilo por bolsa. Lo usamos, y lo marcamos.
            cli = _texto(r.get("Cliente"))
            if cli and re.search(r"kg", _sn(cli)):
                mov["kg_prom"] = _numero(cli)
                self._marcar(mov, "columna_con_otro_dato",
                             "la columna Cliente trae el kilo por bolsa", valor=cli)
            self._push(mov)

    # Env a Frio · planta → frigorífico
    def _leer_envio_a_frio(self, df, solapa):
        for i, r in df.iterrows():
            if not _texto(r.get("Remito")):
                continue
            mov = self._comun(r, solapa, int(i) + 2, "envio_a_frio",
                              col_kg="Kgs.", col_obs="Observaciones",
                              col_cat="Categoría", col_calibre="Calibre")
            mov["kg_prom"] = _numero(r.get("Kg.Prom"))
            mov["destino"] = _ubic_columna(r.get("Destino"))
            # Casi siempre sale de la planta, pero no siempre: hay filas que
            # salen de Pampa Chica y una que va de galpón a galpón.
            mov["origen"] = _lugar(mov["observaciones"]) or dict(PLANTA)
            if mov["origen"] == mov["destino"]:
                mov["origen"] = dict(PLANTA)
            self._push(mov)

    # Ret Frio · EL RETORNO. Frigorífico → planta. El tramo que peor siguen.
    def _leer_retiro_de_frio(self, df, solapa):
        for i, r in df.iterrows():
            if _texto(r.get("Fecha")) is None and _texto(r.get("Remito")) is None:
                continue
            mov = self._comun(r, solapa, int(i) + 2, "retiro_de_frio",
                              col_kg="Kg", col_obs="Observaciones / Destino")
            mov["kg_prom"] = _numero(r.get("Promedio"))
            mov["origen"] = _ubic_columna(r.get("Origen"))
            # El destino de un retiro no tiene columna: vive en el texto libre.
            # 'a planta para trabajar', 'A SASULA PARA REPASAR', 'paraguay'.
            mov["destino"] = _lugar(mov["observaciones"])
            if mov["destino"] is None:
                self._marcar(mov, "destino_no_declarado",
                             "el retiro no dice a dónde fue la mercadería",
                             valor=mov["observaciones"])
            elif mov["destino"] == mov["origen"]:
                # 'saco p/trabajar en cecive': sale y vuelve al mismo lugar.
                mov["destino"] = dict(mov["origen"])
                mov["reingresa"] = True
            if _texto(r.get("Kg")) and not isinstance(r.get("Kg"), (int, float)):
                self._marcar(mov, "kg_como_texto",
                             "los kilos vienen escritos como texto", valor=r.get("Kg"))
            self._push(mov)

    # Entregas a clientes · la venta. Sale de la planta, salvo que diga otra cosa.
    def _leer_entrega_cliente(self, df, solapa):
        for i, r in df.iterrows():
            if not _texto(r.get("Remito")):
                continue
            mov = self._comun(r, solapa, int(i) + 2, "entrega_cliente",
                              col_kg="Kgs.", col_obs="Observaciones",
                              col_dtv="Numero DTVs", col_cat="Categoría",
                              col_calibre="Calibre")
            mov["kg_prom"] = _numero(r.get("Kg.Prom"))
            cliente = _sn(r.get("Destino"))
            mov["destino"] = {"tipo": "cliente", "id": cliente} if cliente else None
            mov["origen"] = _lugar(mov["observaciones"]) or dict(PLANTA)
            com = _texto(r.get("Comisionista"))
            if com:
                mov["comisionista"] = _sn(com)
            self._push(mov)

    # -- controles de fila -------------------------------------------------
    def _push(self, mov: dict) -> None:
        if not mov.get("kg"):
            return                                   # fila sin kilos: no es un movimiento
        if not mov.get("remito") or _sn(mov["remito"]).startswith("s/remito"):
            mov["remito"] = mov.get("remito") or "s/remito"
            self._marcar(mov, "sin_remito", "movimiento sin número de remito")
        # Sólo se reclama el DTV donde la planilla TIENE columna para cargarlo.
        # Marcar 88 filas de Trevelin por una columna que no existe es ruido, y
        # el ruido es lo que hace que se deje de mirar la lista.
        if not mov.get("dtv") and mov["fuente"]["solapa"] in SOLAPAS_CON_DTV:
            self._marcar(mov, "sin_dtv", "movimiento sin DTV registrado")
        self._kg_por_bolsa(mov)
        self.movimientos.append(mov)

    def _kg_por_bolsa(self, mov: dict) -> None:
        b, k = mov.get("bolsas"), mov.get("kg")
        if not b or not k:
            return
        prom = k / b
        if mov.get("kg_prom") is None:
            mov["kg_prom"] = round(prom, 2)
        if KG_BOLSA_MIN <= prom <= KG_BOLSA_MAX:
            return
        # Antes de marcar, mirar si la planilla lo explica. Una bolsa de 25 kg
        # declarada en la observación no es un error de carga: es otra bolsa.
        obs = _sn(mov.get("observaciones"))
        explicado = re.search(r"x\s*\d+\s*kg|\bbolson|\bgranel|\btarima|\bmonton", obs)
        if explicado:
            mov["kg_prom_explicado"] = explicado.group(0)
            return
        self._marcar(mov, "kg_prom_imposible",
                     f"{b:.0f} bolsas para {k:,.0f} kg da {prom:,.0f} kg por bolsa"
                     .replace(",", "."),
                     valor=round(prom, 2))

    # -- controles que necesitan ver todo junto ----------------------------
    def _cruces(self) -> None:
        # 1 · LA REGLA DURA: un lote, una variedad.
        por_lote: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for m in self.movimientos:
            if m["lote"] and m["variedad"]:
                por_lote[m["lote"]][m["variedad"]].append(m)
        for lote, vs in sorted(por_lote.items()):
            if len(vs) < 2:
                continue
            # La variedad con más kilos es la que manda; las otras son el error.
            peso = {v: sum(x["kg"] or 0 for x in ms) for v, ms in vs.items()}
            manda = max(peso, key=peso.get)
            detalle = " · ".join(
                f"{v} en {len(ms)} fila{'s' if len(ms) > 1 else ''}"
                for v, ms in sorted(vs.items(), key=lambda kv: -peso[kv[0]])
            )
            for v, ms in vs.items():
                if v == manda:
                    continue
                for m in ms:
                    self._marcar(m, "lote_multivariedad",
                                 f"el lote {lote} declara {len(vs)} variedades ({detalle}); "
                                 f"por kilos manda {manda}", valor=v)

        # 2 · El mismo nombre escrito de dos maneras. «cerone(sotelo)» y
        #     «cerone(sotelol)» son el mismo chofer, y a la hora de liquidarle
        #     el flete son dos personas distintas en la planilla.
        import difflib
        for campo in ("transporte", "chofer"):
            nombres = sorted({m[campo] for m in self.movimientos if m.get(campo)})
            ya: set[str] = set()
            for i, a in enumerate(nombres):
                for b in nombres[i + 1:]:
                    if b in ya or abs(len(a) - len(b)) > 2:
                        continue
                    if difflib.SequenceMatcher(None, a, b).ratio() < 0.88:
                        continue
                    ya.add(b)
                    for m in self.movimientos:
                        if m.get(campo) == b:
                            self._marcar(m, "nombre_escrito_distinto",
                                         f"«{b}» y «{a}» parecen la misma persona "
                                         f"escrita de dos maneras ({campo})",
                                         valor=b)

        # 3 · El mismo DTV en dos remitos distintos. Un DTV ampara UN tránsito.
        por_dtv: dict[str, set] = defaultdict(set)
        for m in self.movimientos:
            if m["dtv"]:
                por_dtv[m["dtv"]].add(m["remito_id"] or m["remito"])
        for m in self.movimientos:
            if m["dtv"] and len(por_dtv[m["dtv"]]) > 1:
                self._marcar(m, "dtv_repetido",
                             f"el DTV {m['dtv']} ampara "
                             f"{len(por_dtv[m['dtv']])} remitos distintos",
                             valor=m["dtv"])


# ---------------------------------------------------------------------------
# Lotes y campos — derivados de la evidencia, nunca inventados
# ---------------------------------------------------------------------------
def construir_lotes(movs: list[dict]) -> tuple[list[dict], list[dict]]:
    """De qué campo sale cada lote. Sólo cuando los datos lo dicen.

    Un lote sin campo declarado queda con campo=None y sale en «datos a
    corregir». Inventarle un campo a un lote es exactamente el error que
    vinimos a resolver: un dato plausible que nadie puede verificar.
    """
    huerfanos: list[dict] = []
    por_lote: dict[str, dict] = {}
    for m in movs:
        lote = m["lote"]
        if not lote:
            continue
        d = por_lote.setdefault(lote, {
            "id": lote, "campo": None, "pivote": None, "cuadrante": None,
            "variedad": None, "variedades_declaradas": {}, "categoria": None,
            "kg_prom": None, "movimientos": 0, "primera_fecha": None,
            "evidencia_campo": None,
        })
        d["movimientos"] += 1
        if m["variedad"]:
            d["variedades_declaradas"][m["variedad"]] = \
                d["variedades_declaradas"].get(m["variedad"], 0) + (m["kg"] or 0)
        if m["categoria"] and not d["categoria"]:
            d["categoria"] = m["categoria"]
        if m["fecha"] and (d["primera_fecha"] is None or m["fecha"] < d["primera_fecha"]):
            d["primera_fecha"] = m["fecha"]

        # La evidencia del campo: por dónde ENTRÓ el lote al circuito.
        if d["campo"] is None:
            if m["tipo"] == "ingreso_tolva":
                d["campo"], d["evidencia_campo"] = "santa_ana", \
                    f"entró por la solapa «Ingreso Tolvas Santa Ana» (fila {m['fuente']['fila_excel']})"
            elif m["tipo"] == "ingreso_multiplicacion":
                d["campo"], d["evidencia_campo"] = "trevelin", \
                    f"entró por la solapa «Ingreso Trevelin» (fila {m['fuente']['fila_excel']})"
            else:
                lugar = _lugar(m.get("observaciones"))
                if lugar and lugar["tipo"] == "campo":
                    d["campo"] = lugar["id"]
                    d["evidencia_campo"] = f"la observación dice «{m['observaciones']}»"

    for lote, d in por_lote.items():
        vs = d.pop("variedades_declaradas")
        if vs:
            d["variedad"] = max(vs, key=vs.get)
            d["variedades_en_conflicto"] = sorted(vs) if len(vs) > 1 else []
        # kg por bolsa propio del lote, ponderado por kilos. La conversión
        # bolsas↔kilos usa esto, nunca un 50 fijo.
        filas = [m for m in movs if m["lote"] == lote and m.get("kg_prom")
                 and KG_BOLSA_MIN <= m["kg_prom"] <= KG_BOLSA_MAX]
        if filas:
            tot = sum(m["kg"] or 0 for m in filas)
            d["kg_prom"] = round(
                sum((m["kg"] or 0) * m["kg_prom"] for m in filas) / tot, 2) if tot else None
        if d["campo"] is None:
            huerfanos.append({
                "id": "lote_sin_campo",
                "detalle": f"el lote {lote} no declara de qué campo sale",
                "valor": lote, "movimiento": None,
                "fuente": {"archivo": ARCHIVO_MOV, "solapa": "(varias)", "fila_excel": None},
            })
        # Los lotes del plano de Santa Ana traen pivote y cuadrante.
        for piv, info in PLANO_SANTA_ANA.items():
            if f"l{lote}".upper().replace("L", "L") in info["lotes"] or \
               f"L{lote.upper()}" in info["lotes"]:
                d["campo"], d["pivote"] = "santa_ana", piv
                d["evidencia_campo"] = "figura en el plano Santa Ana 2023"
    return sorted(por_lote.values(), key=lambda d: d["id"]), huerfanos


def construir_ubicaciones(movs: list[dict]) -> list[dict]:
    vistos: dict[str, dict] = {
        "planta_mdp": {"id": "planta_mdp", "nombre": "Planta Mar del Plata",
                       "tipo": "planta", "bascula": True, "propia": True},
        "galpon_mdp": {"id": "galpon_mdp", "nombre": "Galpón Mar del Plata",
                       "tipo": "galpon", "bascula": False, "propia": True},
    }
    for fid, nombre in FRIGORIFICOS.items():
        vistos[fid] = {"id": fid, "nombre": nombre, "tipo": "frigorifico",
                       "bascula": False, "propia": False,
                       "nota": "subcontratado — se le paga por kilo movido"}
    usados = set()
    for m in movs:
        for lado in ("origen", "destino"):
            n = m.get(lado)
            if n and n["tipo"] in ("planta", "galpon", "frigorifico"):
                usados.add(n["id"])
    return [u for u in vistos.values() if u["id"] in usados or u["propia"]]


# ---------------------------------------------------------------------------
# Muestras de pre-cosecha → qué calibre da cada lote
# ---------------------------------------------------------------------------
def leer_muestras(carpeta: str) -> list[dict]:
    """El muestreo de campo antes de cosechar: cuánto de ese lote va a salir
    exportación, cuánto sin chicas y cuánto semillón.

    Es lo que permite decir si un lote SIRVE para un pedido en vez de suponerlo.
    Sugerirle a alguien un lote de granel para un pedido de exportación es
    perder la confianza de un productor en una pantalla.
    """
    ruta = os.path.join(carpeta, ARCHIVO_MUESTRAS)
    if not os.path.isfile(ruta):
        return []
    xl = pd.ExcelFile(ruta)
    muestras: list[dict] = []

    # Hoja 'Ag+At Root': tres bloques en columnas, uno por variedad. La fila
    # 'Total' de cada bloque tiene el lote, la superficie y el reparto real.
    if "Ag+At Root" in xl.sheet_names:
        df = xl.parse("Ag+At Root", header=None)
        for variedad, c0 in (("agata", 0), ("atlantic", 8), ("asterix", 16)):
            fila_total = None
            for i in range(len(df)):
                if _sn(df.iat[i, c0]) == "total":
                    fila_total = i
                    break
            if fila_total is None:
                continue
            try:
                lote = _lote(df.iat[fila_total, c0 + 1])
                sup = float(df.iat[fila_total, c0 + 2])
                total, exp, sch, sem = (float(df.iat[fila_total, c0 + 3 + k]) for k in range(4))
                pct = df.iat[fila_total + 2, c0 + 3]      # la fila '%' de abajo
            except Exception:
                continue
            if not total:
                continue
            muestras.append({
                "lote": lote, "variedad": variedad, "campana": "2020",
                "campo": "oriente", "superficie_ha": round(sup, 2),
                "produccion_bolsas": int(total),
                "reparto": {
                    "exportacion": round(exp / total, 4),
                    "sin_chicas": round(sch / total, 4),
                    "semillon": round(sem / total, 4),
                },
                "rinde_bolsas_ha": round(total / sup, 1) if sup else None,
                "fuente": {"archivo": ARCHIVO_MUESTRAS, "solapa": "Ag+At Root",
                           "fila_excel": fila_total + 1},
                "nota": "muestreo de pre-cosecha, campaña 2020 — es una referencia "
                        "de qué da el lote, no el stock de hoy",
            })
            _ = pct

    # Las hojas '<var> 22-12' traen la distribución de calibres en milímetros.
    for hoja, variedad in (("Ag 22-12", "agata"), ("At 22-12", "atlantic"),
                           ("Ax 22-12", "asterix")):
        if hoja not in xl.sheet_names:
            continue
        df = xl.parse(hoja, header=None)
        dist: dict[str, float] = {}
        for i in range(1, len(df)):
            rango = _texto(df.iat[i, 0])
            if not rango or _sn(rango) in ("total", "rootex", "s/rootex"):
                if _sn(rango) == "total":
                    break
                continue
            pct = df.iat[i, 2]
            if isinstance(pct, (int, float)) and not pd.isna(pct):
                dist[rango] = round(float(pct), 4)
        if dist:
            for m in muestras:
                if m["variedad"] == variedad:
                    m["distribucion_mm"] = dist
                    m["fuente_distribucion"] = {"archivo": ARCHIVO_MUESTRAS, "solapa": hoja}
    return muestras


# ---------------------------------------------------------------------------
def main() -> None:
    carpeta = _origen_archivos()
    print(f"Leyendo las planillas de Papasud desde:\n  {carpeta}\n")

    imp = Importacion(carpeta)
    imp.importar()

    lotes, huerfanos = construir_lotes(imp.movimientos)
    imp.anomalias.extend(huerfanos)
    ubicaciones = construir_ubicaciones(imp.movimientos)
    muestras = leer_muestras(carpeta)

    os.makedirs(SALIDA, exist_ok=True)
    salidas = {
        "movimientos.json": imp.movimientos,
        "lotes.json": lotes,
        "ubicaciones.json": ubicaciones,
        "anomalias.json": imp.anomalias,
        "muestras.json": muestras,
        "campos.json": [{"id": k, **v} for k, v in CAMPOS.items()],
    }
    for nombre, datos in salidas.items():
        with open(os.path.join(SALIDA, nombre), "w", encoding="utf-8") as fh:
            json.dump(datos, fh, ensure_ascii=False, indent=1)

    with open(os.path.join(SALIDA, "meta.json"), "w", encoding="utf-8") as fh:
        json.dump({
            "archivo": ARCHIVO_MOV,
            "solapas_importadas": SOLAPAS,
            "solapas_pendientes": SOLAPAS_PENDIENTES,
            "plano": {"santa_ana": PLANO_SANTA_ANA},
            "kg_bolsa_banda": [KG_BOLSA_MIN, KG_BOLSA_MAX],
        }, fh, ensure_ascii=False, indent=1)

    # -- el resumen que se lee en voz alta --------------------------------
    por_anomalia: dict[str, int] = defaultdict(int)
    for a in imp.anomalias:
        por_anomalia[a["id"]] += 1
    kg = sum(m["kg"] or 0 for m in imp.movimientos)
    print(f"\n{len(imp.movimientos)} movimientos · {len(lotes)} lotes · "
          f"{len(ubicaciones)} ubicaciones · {kg:,.0f} kg".replace(",", "."))
    print(f"{len(muestras)} muestras de pre-cosecha")
    print(f"\nLo que la planilla trae mal ({len(imp.anomalias)} hallazgos):")
    for aid, n in sorted(por_anomalia.items(), key=lambda kv: -kv[1]):
        print(f"  {n:>4}  {aid}")
    print(f"\n→ {SALIDA}")


if __name__ == "__main__":
    main()
