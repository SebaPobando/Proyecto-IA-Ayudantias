import os

from dotenv import load_dotenv
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma

load_dotenv()

clave = os.getenv("GEMINI_API_KEY")
nombre_modelo = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

if not clave:
    raise ValueError("Falta GEMINI_API_KEY en el archivo .env")

if __name__ == "__main__":
    corpus = [
        "consultar_producto recibe un codigo. T01 es un Teclado de 10000 CLP "
        "con stock 8. M02 es un Mouse de 6000 CLP con stock 12.",
        "cotizar_compra recibe precio_unitario, cantidad e incluir_despacho. "
        "El precio y la cantidad deben ser mayores que cero. No compra ni reserva stock.",
        "El subtotal es precio_unitario por cantidad. El despacho cuesta 2500 CLP "
        "si el subtotal es menor que 30000 CLP. Desde 30000 CLP es gratis. "
        "El retiro no tiene cargo de despacho.",
        "historiales guarda una conversacion por session_id. obtener_historial "
        "crea o recupera su historial. Los mensajes viven en memoria y se pierden "
        "al cerrar el programa.",
        "generar_reembolso solo simula. Requiere aprobacion en consola con s/n "
        "en 30 segundos. Sin aprobacion no se ejecuta. Un pedido ya reembolsado "
        "no se repite en la misma ejecucion.",
    ]

    texto = "\n\n".join(corpus)

    splitter_fijo = CharacterTextSplitter(
        separator="", chunk_size=110, chunk_overlap=0
    )
    chunks_fijo = splitter_fijo.split_text(texto)

    print("\nCHUNKING FIJO")
    for i, chunk in enumerate(chunks_fijo):
        print(f"--- chunk {i} ({len(chunk)} caracteres) ---")
        print(chunk)

    splitter_recursivo = RecursiveCharacterTextSplitter(
        chunk_size=110, chunk_overlap=20
    )
    chunks_recursivo = splitter_recursivo.split_text(texto)

    print("\nCHUNKING RECURSIVO")
    for i, chunk in enumerate(chunks_recursivo):
        print(f"--- chunk {i} ({len(chunk)} caracteres) ---")
        print(chunk)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200, chunk_overlap=30
    )
    chunks = splitter.create_documents(corpus)

    print(f"\nDocumentos originales: {len(corpus)}")
    print(f"Chunks para indexar: {len(chunks)}")
    for i, chunk in enumerate(chunks):
        print(f"--- Document {i} ({len(chunk.page_content)} caracteres) ---")
        print(chunk.page_content)

    persist_directory = "vectorstore/"
    modo = input("\nModo (indexar/verificar): ").strip().lower()
    if modo not in ("indexar", "verificar"):
        raise ValueError("Escribe indexar o verificar.")

    if modo == "indexar" and os.path.exists(persist_directory):
        raise ValueError(
            "Ya existe la carpeta del indice. Usa verificar. "
            "Para otro ensayo, cambia persist_directory."
        )

    if modo == "verificar" and not os.path.isdir(persist_directory):
        raise ValueError("No existe la carpeta del indice. Ejecuta primero indexar.")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        api_key=clave,
    )

    if modo == "indexar":
        try:
            vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=persist_directory,
            )
        except Exception as error:
            print("No se completo la indexacion:", type(error).__name__)
            raise SystemExit(1) from error

        print(f"Indexados {len(chunks)} chunks en {persist_directory}")

    vectorstore_recargado = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    cantidad_guardada = vectorstore_recargado._collection.count()
    print(f"Chunks guardados: {cantidad_guardada}")

    if cantidad_guardada != len(chunks):
        raise ValueError("El conteo guardado no coincide con el corpus actual.")

    print("Indice abierto y conteo correcto. La recarga no calcula embeddings.")