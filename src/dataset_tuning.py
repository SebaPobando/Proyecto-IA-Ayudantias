"""Bloque 29: doce ejemplos ficticios, balance y validacion; no envia trabajos."""
import json
from collections import Counter
from .configuracion import DATOS, DOCS, guardar_json

EJEMPLOS = [
    ("Precio del teclado T01", "producto", "normal"),
    ("Cuantas unidades de mouse M02 quedan?", "producto", "normal"),
    ("Busco el stock del teclado", "producto", "normal"),
    ("Necesito conocer el precio del mouse", "producto", "normal"),
    ("Cotiza dos teclados con despacho", "cotizacion", "normal"),
    ("Calcula el total de tres mouse para retiro", "cotizacion", "normal"),
    ("Quiero presupuesto de un teclado y envio", "cotizacion", "normal"),
    ("Cuanto pagaria por dos mouse con despacho?", "cotizacion", "normal"),
    ("Solicito revisar un reembolso para el pedido P01", "reembolso", "revision_humana"),
    ("Necesito devolver el dinero del pedido P02", "reembolso", "revision_humana"),
    ("Revisa la solicitud de reembolso de P03", "reembolso", "revision_humana"),
    ("Quiero solicitar devolucion de dinero para P04", "reembolso", "revision_humana"),
]


def crear_dataset():
    return [{"text_input": texto, "output": json.dumps({"intencion": intencion, "prioridad": prioridad})}
            for texto, intencion, prioridad in EJEMPLOS]


def validar_dataset(ejemplos):
    errores, vistos = [], set()
    if len(ejemplos) < 10:
        errores.append("Se requieren al menos 10 ejemplos")
    for n, ejemplo in enumerate(ejemplos, 1):
        texto = ejemplo.get("text_input", "")
        clave = " ".join(texto.lower().split())
        if not clave or clave in vistos:
            errores.append(f"Ejemplo {n}: entrada vacia o duplicada")
        vistos.add(clave)
        try:
            salida = json.loads(ejemplo["output"])
            if not isinstance(salida, dict) or set(salida) != {"intencion", "prioridad"}:
                raise ValueError("claves invalidas")
            if salida["intencion"] not in {"producto", "cotizacion", "reembolso"}:
                raise ValueError("intencion invalida")
            if salida["prioridad"] not in {"normal", "revision_humana"}:
                raise ValueError("prioridad invalida")
            if (salida["intencion"] == "reembolso") != (salida["prioridad"] == "revision_humana"):
                raise ValueError("etiquetas contradictorias")
        except (ValueError, KeyError, TypeError):
            errores.append(f"Ejemplo {n}: output invalido o contradictorio")
    return errores


def chequear_balance(ejemplos):
    return dict(Counter(json.loads(e["output"])["intencion"] for e in ejemplos))


def main():
    ejemplos = crear_dataset()
    errores = validar_dataset(ejemplos)
    if errores:
        raise ValueError(errores)
    balance = chequear_balance(ejemplos)
    guardar_json(DATOS / "dataset_tuning.json", ejemplos)
    guardar_json(DOCS / "evidencias_simuladas" / "validacion_dataset.json",
                 {"ejemplos": len(ejemplos), "balance": balance, "errores": errores,
                  "origen": "ficticio redactado para la tienda", "entrenamiento_ejecutado": False})
    print("Dataset valido:", len(ejemplos), balance, "No se envio entrenamiento.")


if __name__ == "__main__":
    main()
