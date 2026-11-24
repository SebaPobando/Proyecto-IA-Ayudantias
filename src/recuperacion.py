"""Bloque 26: recuperacion con distancia, metadatos y prompt dinamico."""
import json
from .configuracion import ruta_indice, cargar_configuracion_real
from .indexar_corpus import abrir_indice


def recuperar(pregunta, k=3, real=False, store=None):
    if not pregunta.strip() or type(k) is not int or k < 1:
        raise ValueError("La pregunta debe tener contenido y k debe ser un entero positivo")
    if store is None:
        if real:
            cfg = cargar_configuracion_real()
        manifiesto = ruta_indice(real) / "manifiesto.json"
        if not manifiesto.exists():
            raise ValueError("Falta el indice. Ejecuta python -m src.indexar_corpus" + (" --real" if real else ""))
        identidad = json.loads(manifiesto.read_text(encoding="utf-8"))
        esperado = cfg["embedding"] if real else "lexico-local-256"
        if identidad["embedding"] != esperado or identidad["modo"] != ("real" if real else "simulado"):
            raise ValueError("El modelo o modo no coincide con el indice. Reindexa en otra carpeta")
        store = abrir_indice(real)
    return store.similarity_search_with_score(pregunta, k=k)


def main():
    from .registro_rag import main as ejecutar
    ejecutar()


if __name__ == "__main__":
    main()
