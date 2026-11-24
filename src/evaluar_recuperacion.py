"""Bloque 27: etiquetas previas y precision, recall, MRR para k=1,3,6."""
import argparse
import json
from statistics import mean
from .configuracion import DATOS, DOCS, LOCAL, guardar_json
from .recuperacion import recuperar


def metricas(recuperados, relevantes):
    unicos = list(dict.fromkeys(recuperados))
    relevantes = set(relevantes)
    aciertos = len(set(unicos) & relevantes)
    return {"precision": aciertos / len(unicos) if unicos else 0.0,
            "recall": aciertos / len(relevantes) if relevantes else 0.0,
            "mrr": next((1 / n for n, doc_id in enumerate(unicos, 1) if doc_id in relevantes), 0.0)}


def evaluar(real=False, store=None, casos=None):
    casos = casos if casos is not None else json.loads((DATOS / "evaluacion_recuperacion.json").read_text(encoding="utf-8"))
    if not casos or any(not caso["relevantes"] for caso in casos):
        raise ValueError("La evaluacion requiere casos con documentos relevantes etiquetados")
    filas = []
    for k in (1, 3, 6):
        for caso in casos:
            pares = recuperar(caso["pregunta"], k=k, real=real, store=store)
            ids = [doc.metadata["source_id"] for doc, _ in pares]
            filas.append({"k": k, "pregunta": caso["pregunta"], "recuperados": ids,
                          "relevantes": caso["relevantes"], **metricas(ids, caso["relevantes"])})
    resumen = [{"k": k, **{m: mean(f[m] for f in filas if f["k"] == k)
                           for m in ("precision", "recall", "mrr")}} for k in (1, 3, 6)]
    return {"modo": "real" if real else "simulado_lexico", "casos": len(casos),
            "unidad": "documentos fuente unicos; chunks de la misma fuente se deduplican",
            "resumen": resumen, "resultados": filas,
            "limite": "No mide veracidad de la generacion; el modo local no valida embeddings semanticos del proveedor"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true")
    args = parser.parse_args()
    resultado = evaluar(real=args.real)
    carpeta = LOCAL / "registros_reales" if args.real else DOCS / "evidencias_simuladas"
    guardar_json(carpeta / "evaluacion_recuperacion.json", resultado)
    print(json.dumps(resultado["resumen"], indent=2))


if __name__ == "__main__":
    main()
