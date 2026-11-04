"""Bloque 18: extraer ideas, simplificarlas y organizarlas en viñetas."""

# import argparse 
# import json
# from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
    plantilla_extraer = PromptTemplate.from_template(
        "Extrae las tres ideas principales del siguiente texto. "
        "No agregues información:\n\n{texto}"
    )

    plantilla_simplificar = PromptTemplate.from_template(
        "Explica estas ideas con palabras sencillas para una "
        "persona sin conocimientos técnicos. "
        "Conserva su significado:\n\n{ideas}"
    )

    plantilla_formatear = PromptTemplate.from_template(
        "Organiza esta explicación en un máximo de tres viñetas. "
        "No agregues información ni introducción:\n\n{explicacion}"
    )

    extraer = plantilla_extraer | modelo | StrOutputParser()
    simplificar =plantilla_simplificar | modelo | StrOutputParser()
    formatear = plantilla_formatear | modelo | StrOutputParser()

    cadena = (
        extraer
        | (lambda resultado: {"ideas": resultado})
        | simplificar
        | (lambda resultado: {"explicacion": resultado})
        | formatear
    )

    return cadena

if __name__ == "__main__":
    load_dotenv()
    
    modelo = ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite")
    cadena = construir_cadena(modelo)

    texto = """
    La tokenización divide un texto en unidades llamadas tokens.
    Un token puede corresponder a una palabra, parte de una palabra
    o un signo de puntuación. Los modelos de lenguaje procesan
    secuencias de tokens y generan su respuesta progresivamente.
    """
    
    resultado = cadena.invoke({"texto": texto})
    print(resultado)