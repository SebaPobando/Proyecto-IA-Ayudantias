"""Vectores lexicos sin API. No representan calidad semantica del proveedor."""
import hashlib
import math
import re
import unicodedata
from langchain_core.embeddings import Embeddings


def palabras(texto):
    normal = "".join(c for c in unicodedata.normalize("NFD", texto.lower())
                     if unicodedata.category(c) != "Mn")
    return re.findall(r"[a-z0-9_]+", normal)


class EmbeddingsLocales(Embeddings):
    dimensiones = 256

    def embed_query(self, text):
        vector = [0.0] * self.dimensiones
        for palabra in palabras(text):
            indice = int(hashlib.sha256(palabra.encode()).hexdigest()[:8], 16) % self.dimensiones
            vector[indice] += 1
        norma = math.sqrt(sum(v * v for v in vector)) or 1
        return [v / norma for v in vector]

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]
