"""
Importador asistido — Ángela mapea las columnas de cualquier export.

El dueño suelta un Excel/CSV y el sistema infiere a qué campo canónico
corresponde cada columna (por nombre de header), reporta el mapeo para que lo
confirme, y deja lo que no pudo mapear a la vista. Hoy el mapeo es heurístico
(sinónimos); el hook de IA se enciende cuando haya ANTHROPIC_API_KEY.

# TODO IA: si hay API key, pedirle a Claude el mapeo de headers ambiguos.
# TODO: validación final del formato con un export REAL de Horizonte (spec §15).
"""
from __future__ import annotations

import csv
import io
import os
import unicodedata

import openpyxl

# Campos canónicos por destino (ver spec §9).
DESTINOS = {
    "venta_historica": ["fecha", "boca", "articulo", "cantidad", "kilos", "precio", "costo", "es_venta_a_sucursal_propia"],
    "cuenta_corriente": ["cliente", "saldo", "plazo", "vencimiento"],
    "producto": ["codigo", "descripcion", "stock", "costo", "pvp", "venta_x_peso"],
    "deposito": ["codigo", "producto", "ubicacion", "lote", "vencimiento", "cantidad"],
    "logistica": ["pedido", "cliente", "direccion", "estado", "fecha_prevista", "transporte"],
    # EL DESTINO DEL BRIEF: la planilla de stock de semilla que hoy editan
    # varias personas a la vez. Los campos son los del negocio de Papasud, no
    # los de un depósito genérico: sin variedad, categoría y campaña un lote de
    # semilla fiscalizada no se puede identificar ni certificar.
    "stock_semilla": ["lote", "variedad", "categoria", "campania", "ubicacion",
                      "camara", "bolsones", "kilos", "calibre", "campo_origen",
                      "analisis", "vencimiento"],
}

# Sinónimos de header por campo (normalizados: minúsculas, sin acentos).
SINONIMOS = {
    "codigo": ["codigo", "cod", "sku", "id"],
    "descripcion": ["descripcion", "producto", "nombre", "detalle", "articulo"],
    "pvp": ["pvp", "precio de venta", "precio venta", "precio publico", "venta", "precio"],
    "fecha": ["fecha", "dia", "date", "emision"],
    "boca": ["boca", "local", "sucursal", "punto de venta", "pdv", "deposito"],
    "articulo": ["articulo", "producto", "descripcion", "item", "codigo", "sku"],
    "cantidad": ["cantidad", "cant", "unidades", "qty", "bultos"],
    "kilos": ["kilos", "kg", "peso", "kgs"],
    "precio": ["precio", "pvp", "venta", "importe", "total", "monto"],
    "costo": ["costo", "cost", "costo unitario"],
    "es_venta_a_sucursal_propia": ["sucursal propia", "interna", "es sucursal", "propia"],
    "cliente": ["cliente", "razon social", "nombre", "cuit"],
    "saldo": ["saldo", "deuda", "debe", "balance"],
    "plazo": ["plazo", "dias", "condicion"],
    "vencimiento": ["vencimiento", "vence", "due"],
    "producto": ["producto", "descripcion", "articulo", "detalle", "nombre"],
    # ojo con el orden: "camara" es su propio campo en stock_semilla, así que
    # acá va al final — si estuviera primero se comería la columna Cámara y la
    # ubicación quedaría sin mapear
    "ubicacion": ["ubicacion", "frigorifico", "galpon", "deposito", "sitio",
                  "pasillo", "estanteria", "rack", "sector", "posicion"],
    "lote": ["lote", "partida", "batch"],
    "pedido": ["pedido", "nro pedido", "orden", "remito", "comprobante"],
    "direccion": ["direccion", "domicilio", "destino"],
    "estado": ["estado", "status", "situacion"],
    "fecha_prevista": ["fecha prevista", "fecha entrega", "prevista", "fecha"],
    "transporte": ["transporte", "camion", "chofer", "vehiculo", "flete"],
    # --- el vocabulario de la semilla de papa ---------------------------------
    # Estos sinónimos son los encabezados que aparecen de verdad en una planilla
    # de semillero: "cat.", "camp.", "bolsones", "cámara", "grado".
    "variedad": ["variedad", "var", "cultivar", "tipo"],
    "categoria": ["categoria", "cat", "categoria inase", "clase"],
    "campania": ["campania", "campana", "camp", "cosecha", "ciclo", "temporada"],
    "camara": ["camara", "cam", "sala", "frio"],
    "bolsones": ["bolsones", "bolson", "big bag", "bigbag", "bultos", "bolsas"],
    "calibre": ["calibre", "grado", "tamano", "medida", "mm"],
    "campo_origen": ["campo", "campo origen", "origen", "lote de campo", "establecimiento"],
    "analisis": ["analisis", "das-elisa", "elisa", "sanidad", "virus", "pvy"],
}


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()


def inferir_mapeo(headers: list[str], destino: str = "venta_historica") -> dict:
    """Devuelve {campo_canonico: header_original|None} y los headers sin usar."""
    campos = DESTINOS.get(destino, [])
    headers_norm = [(h, _norm(h)) for h in headers]
    usados = set()
    mapeo = {}
    for campo in campos:
        encontrado = None
        for syn in SINONIMOS.get(campo, [campo]):
            for orig, hn in headers_norm:
                if orig in usados:
                    continue
                if syn == hn or syn in hn or hn in syn:
                    encontrado = orig
                    break
            if encontrado:
                break
        if encontrado:
            usados.add(encontrado)
        mapeo[campo] = encontrado
    sin_mapear = [h for h, _ in headers_norm if h not in usados]
    return {"destino": destino, "mapeo": mapeo, "sin_mapear": sin_mapear}


def _leer(path: str) -> tuple[list[str], list[list]]:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".xlsx", ".xlsm"):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = [[c for c in r] for r in ws.iter_rows(values_only=True)]
        wb.close()
    else:  # csv
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = [r for r in csv.reader(f)]
    headers = [str(c) if c is not None else "" for c in (rows[0] if rows else [])]
    return headers, rows[1:]


# Los campos SIN LOS CUALES una fila de stock de semilla no sirve. No es una
# preferencia: sin lote no se puede trazar, sin variedad y categoría no se puede
# rotular, y sin kilos no hay stock.
_OBLIGATORIOS = {
    "stock_semilla": ["lote", "variedad", "categoria", "kilos"],
    "deposito": ["lote", "cantidad"],
}

# El nombre del campo como lo dice una persona. "1 filas no tienen categoria"
# se lee como un mensaje de sistema; "1 fila sin categoría", como algo escrito.
_NOMBRE_CAMPO = {
    "lote": ("lote", "el lote"), "variedad": ("variedad", "la variedad"),
    "categoria": ("categoría", "la categoría"), "kilos": ("kilos", "los kilos"),
    "cantidad": ("cantidad", "la cantidad"), "bolsones": ("bolsones", "los bolsones"),
}


def revisar_filas(headers: list[str], filas: list[list], mapeo: dict,
                  destino: str) -> list[dict]:
    """QUÉ ESTÁ ROTO ADENTRO DE LA PLANILLA.

    Estructurar el Excel es la mitad del trabajo; la otra mitad es decir qué
    tiene mal. Papasud viene de años de planilla compartida y los errores están
    adentro: el mismo lote cargado dos veces por dos personas, kilos con texto
    en la celda, filas a las que les falta la categoría.

    Cada problema viaja con LA FILA (el número que se ve en el Excel) para que
    se pueda ir a corregir sin adivinar."""
    col = {campo: headers.index(h) for campo, h in (mapeo or {}).items()
           if h and h in headers}
    problemas: list[dict] = []

    def agregar(clase, titulo, afectadas, detalle):
        if afectadas:
            problemas.append({"clase": clase, "titulo": titulo,
                              "filas": afectadas[:20],
                              "cantidad": len(afectadas),
                              "detalle": detalle})

    # 1) obligatorios en blanco
    for campo in _OBLIGATORIOS.get(destino, []):
        if campo not in col:
            continue
        i = col[campo]
        vacias = [n + 2 for n, f in enumerate(filas)
                  if i >= len(f) or str(f[i] or "").strip() == ""]
        corto, largo = _NOMBRE_CAMPO.get(campo, (campo, "el " + campo))
        n_ = len(vacias)
        agregar("campo_vacio", f"Sin {corto}", vacias,
                f"{'Una fila no tiene' if n_ == 1 else f'{n_} filas no tienen'} "
                f"{largo}. Sin ese dato el lote no se puede identificar ni certificar.")

    # 2) el mismo lote dos veces — la firma de la planilla compartida
    if "lote" in col:
        i = col["lote"]
        vistos: dict[str, list[int]] = {}
        for n, f in enumerate(filas):
            k = str(f[i] if i < len(f) else "").strip().lower()
            if k:
                vistos.setdefault(k, []).append(n + 2)
        repes = sorted(n for ns in vistos.values() if len(ns) > 1 for n in ns)
        agregar("duplicado", "El mismo lote más de una vez", repes,
                "Dos personas cargaron el mismo lote en filas distintas: los "
                "kilos se cuentan dos veces.")

    # 3) cantidades que no son un número
    for campo in ("kilos", "bolsones", "cantidad"):
        if campo not in col:
            continue
        i = col[campo]
        malas = []
        for n, f in enumerate(filas):
            v = str(f[i] if i < len(f) else "").strip()
            if not v:
                continue
            try:
                float(v.replace(".", "").replace(",", ".") if "," in v else v)
            except ValueError:
                malas.append(n + 2)
        corto, _ = _NOMBRE_CAMPO.get(campo, (campo, campo))
        agregar("no_numerico",
                f"{corto.capitalize()}: hay texto donde va un número", malas,
                "Una celda tiene texto donde va una cantidad (un guion, un "
                "'aprox', una nota al margen). Esos kilos no se pueden sumar."
                if len(malas) == 1 else
                f"{len(malas)} celdas tienen texto donde va una cantidad. Esos "
                f"kilos no se pueden sumar.")

    return problemas


def previsualizar_filas(headers: list[str], filas: list[list], destino: str, n: int = 3) -> dict:
    info = inferir_mapeo(headers, destino)
    ejemplo = [dict(zip(headers, fila)) for fila in filas[:n]]
    info["filas_ejemplo"] = ejemplo
    info["total_filas"] = len(filas)
    info["mapeados"] = sum(1 for v in info["mapeo"].values() if v)
    info["problemas"] = revisar_filas(headers, filas, info["mapeo"], destino)
    return info


def previsualizar(path: str, destino: str = "venta_historica") -> dict:
    headers, filas = _leer(path)
    return previsualizar_filas(headers, filas, destino)


def leer_archivo(path: str, destino: str = "venta_historica") -> tuple[dict, str]:
    """Lee un archivo REAL (xlsx/xlsm/csv) y devuelve (preview, csv_equivalente).

    El CSV que vuelve no es un rodeo: el resto del pipeline —staging, la zona de
    revisión, el OK del dueño— ya trabaja sobre texto tabular. Convertir el
    Excel acá, en el borde, deja UN solo camino adentro del sistema en vez de
    dos que se pueden desincronizar."""
    headers, filas = _leer(path)
    info = previsualizar_filas(headers, filas, destino)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    for f in filas:
        w.writerow(["" if c is None else c for c in f])
    return info, buf.getvalue()


def previsualizar_csv(texto: str, destino: str = "venta_historica") -> dict:
    """Igual que previsualizar pero desde el contenido CSV (lo manda el frontend)."""
    rows = list(csv.reader(io.StringIO(texto)))
    headers = [str(c) for c in (rows[0] if rows else [])]
    return previsualizar_filas(headers, rows[1:], destino)
