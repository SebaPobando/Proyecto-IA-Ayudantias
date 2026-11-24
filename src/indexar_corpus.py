"""Bloques 24 y 25: chunks con ID, metadatos y actualizacion persistente."""
import argparse
import hashlib
import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from .configuracion import DATOS, cargar_configuracion_real, guardar_json, ruta_indice
from .embeddings_locales import EmbeddingsLocales

COLECCION = "proyectoia_b32"


def cargar_corpus(ruta=None):
    corpus = json.loads(Path(ruta or DATOS / "corpus_tienda.json").read_text(encoding="utf-8"))
    ids = [d["id"] for d in corpus]
    if len(ids) != len(set(ids)) or not corpus:
        raise ValueError("El corpus debe tener IDs unicos y al menos un documento")
    if any(not d["id"].strip() or not d["texto"].strip() or not d["fuente"].strip() for d in corpus):
        raise ValueError("Cada documento necesita ID, texto y fuente no vacios")
    return corpus


def crear_chunks(corpus, chunk_size=200, chunk_overlap=30):
    if not 0 <= chunk_overlap < chunk_size:
        raise ValueError("El overlap debe ser menor que chunk_size y no negativo")
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    documentos, ids = [], []
    for origen in corpus:
        for n, texto in enumerate(splitter.split_text(origen["texto"])):
            if not texto.strip():
                raise ValueError("Se genero un chunk vacio")
            chunk_id = f"{origen['id']}:{n}"
            ids.append(chunk_id)
            documentos.append(Document(page_content=texto, metadata={
                "id": chunk_id, "source_id": origen["id"], "fuente": origen["fuente"],
                "version": hashlib.sha256(origen["texto"].encode()).hexdigest()[:12]}))
    return documentos, ids


def crear_embeddings(real=False):
    if not real:
        return EmbeddingsLocales()
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    cfg = cargar_configuracion_real()
    return GoogleGenerativeAIEmbeddings(model=cfg["embedding"], api_key=cfg["api_key"])


def abrir_indice(real=False, directorio=None, embeddings=None):
    from langchain_chroma import Chroma
    return Chroma(collection_name=COLECCION,
                  persist_directory=str(directorio or ruta_indice(real)),
                  embedding_function=embeddings or crear_embeddings(real))


def indexar(real=False, directorio=None, corpus=None, chunk_size=200, chunk_overlap=30):
    carpeta = Path(directorio or ruta_indice(real))
    carpeta.mkdir(parents=True, exist_ok=True)
    cfg_modelo = cargar_configuracion_real()["embedding"] if real else "lexico-local-256"
    identidad = {"modo": "real" if real else "simulado", "embedding": cfg_modelo,
                 "coleccion": COLECCION}
    manifiesto = carpeta / "manifiesto.json"
    if manifiesto.exists():
        anterior = json.loads(manifiesto.read_text(encoding="utf-8"))
        if any(anterior[k] != identidad[k] for k in identidad):
            raise ValueError("El indice usa otro modelo o modo. Elige otro RAG_INDEX_DIR y reindexa")
    documentos, ids = crear_chunks(corpus if corpus is not None else cargar_corpus(), chunk_size, chunk_overlap)
    store = abrir_indice(real, carpeta)
    anteriores = set(store.get()["ids"])
    store.add_documents(documentos, ids=ids)
    obsoletos = anteriores - set(ids)
    if obsoletos:
        store.delete(ids=sorted(obsoletos))
    guardados = set(store.get()["ids"])
    if guardados != set(ids):
        raise RuntimeError("El contenido persistido no coincide con el corpus")
    informe = {**identidad, "chunks": len(ids), "ids": ids, "eliminados": len(obsoletos),
               "chunk_size": chunk_size, "chunk_overlap": chunk_overlap}
    guardar_json(manifiesto, informe)
    return informe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--real", action="store_true", help="Calcula embeddings en el proveedor")
    parser.add_argument("--comparar", action="store_true")
    args = parser.parse_args()
    if args.comparar:
        texto = "\n\n".join(d["texto"] for d in cargar_corpus())
        for nombre, splitter in [("fijo", CharacterTextSplitter(separator="", chunk_size=110, chunk_overlap=0)),
                                  ("recursivo", RecursiveCharacterTextSplitter(chunk_size=110, chunk_overlap=20))]:
            print(nombre, json.dumps(splitter.split_text(texto), ensure_ascii=False, indent=2))
        return
    print(json.dumps(indexar(real=args.real), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
